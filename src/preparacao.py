"""Leitura e junção das tabelas do Olist em uma linha por pedido entregue.

Usado pelos dois notebooks, para que a base seja montada sempre do mesmo jeito.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import ARQUIVOS_CSV, PASTA_DADOS


def _ler_csv(nome_arquivo: str, pasta: Path) -> pd.DataFrame:
    """Lê o CSV aceitando também a versão compactada (.csv.gz)."""
    caminho = pasta / nome_arquivo
    if not caminho.exists() and (pasta / (nome_arquivo + ".gz")).exists():
        caminho = pasta / (nome_arquivo + ".gz")
    if not caminho.exists():
        raise FileNotFoundError(
            f"Arquivo {nome_arquivo} não encontrado em {pasta}. "
            "Veja data/LEIA-ME.md para baixar os dados do Kaggle."
        )
    # utf-8-sig remove o BOM que aparece no arquivo de tradução das categorias
    return pd.read_csv(caminho, encoding="utf-8-sig")


def carregar_tabelas(pasta: Path = PASTA_DADOS) -> dict:
    """Carrega as 8 tabelas usadas (a 9ª, geolocalização, não é necessária)."""
    tabelas = {chave: _ler_csv(arq, pasta) for chave, arq in ARQUIVOS_CSV.items()}
    datas = [
        "order_purchase_timestamp", "order_approved_at",
        "order_delivered_carrier_date", "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for col in datas:
        tabelas["orders"][col] = pd.to_datetime(tabelas["orders"][col])
    for col in ["review_creation_date", "review_answer_timestamp"]:
        tabelas["reviews"][col] = pd.to_datetime(tabelas["reviews"][col])
    return tabelas


def montar_base(tabelas: dict, verbose: bool = True) -> pd.DataFrame:
    """Une as tabelas e devolve uma linha por pedido entregue e avaliado.

    Decisões (justificadas no notebook 01):
    - só pedidos com status 'delivered' e data de entrega preenchida;
    - pedidos com mais de uma avaliação: fica a mais recente;
    - produto principal = item mais caro do pedido (define categoria e vendedor);
    - pagamento principal = forma com maior valor pago (define tipo e parcelas).
    """
    log = []
    orders = tabelas["orders"]
    log.append(("Pedidos no dataset", len(orders)))

    entregues = orders[
        (orders["order_status"] == "delivered")
        & orders["order_delivered_customer_date"].notna()
    ].copy()
    log.append(("Pedidos entregues com data de entrega", len(entregues)))

    # Avaliação: uma por pedido. As datas da avaliação servem SÓ para escolher
    # a mais recente; não entram como variável do modelo (vazamento de alvo).
    reviews = (
        tabelas["reviews"]
        .sort_values("review_answer_timestamp")
        .drop_duplicates("order_id", keep="last")
        [["order_id", "review_score", "review_creation_date"]]
    )
    base = entregues.merge(reviews, on="order_id", how="inner")
    log.append(("... e com avaliação", len(base)))

    # Itens: agrega valores e escolhe o item mais caro como produto principal
    items = tabelas["items"].merge(
        tabelas["products"][["product_id", "product_category_name"]],
        on="product_id", how="left",
    )
    agregado = items.groupby("order_id").agg(
        qtd_itens=("order_item_id", "count"),
        valor_produtos=("price", "sum"),
        valor_frete=("freight_value", "sum"),
    )
    principal = (
        items.sort_values(["order_id", "price"], ascending=[True, False])
        .drop_duplicates("order_id")
        [["order_id", "product_category_name", "seller_id"]]
    )
    base = base.merge(agregado, on="order_id", how="inner")
    base = base.merge(principal, on="order_id", how="left")
    log.append(("... e com itens", len(base)))

    # Tradução da categoria (usada só na EDA, para quem lê em inglês)
    base = base.merge(tabelas["traducao"], on="product_category_name", how="left")
    base["categoria"] = base["product_category_name"].fillna("sem_categoria")

    # Estado do cliente e do vendedor
    base = base.merge(
        tabelas["customers"][["customer_id", "customer_state"]],
        on="customer_id", how="left",
    )
    base = base.merge(
        tabelas["sellers"][["seller_id", "seller_state"]],
        on="seller_id", how="left",
    )

    # Pagamento principal
    pag = (
        tabelas["payments"]
        .sort_values(["order_id", "payment_value"], ascending=[True, False])
        .drop_duplicates("order_id")
        [["order_id", "payment_type", "payment_installments"]]
    )
    base = base.merge(pag, on="order_id", how="inner")
    log.append(("... e com pagamento", len(base)))

    base = base.rename(columns={
        "customer_state": "uf_cliente",
        "seller_state": "uf_vendedor",
        "payment_type": "pagamento",
        "payment_installments": "parcelas",
    })

    # Variáveis de tempo, em dias inteiros (o app usa um slider em dias)
    entrega = base["order_delivered_customer_date"].dt.normalize()
    estimada = base["order_estimated_delivery_date"].dt.normalize()
    compra = base["order_purchase_timestamp"].dt.normalize()
    base["dias_atraso"] = (entrega - estimada).dt.days
    base["tempo_entrega"] = (entrega - compra).dt.days
    base["prazo_estimado"] = (estimada - compra).dt.days

    # Remove inconsistências: entrega antes da compra
    base = base[base["tempo_entrega"] >= 0]
    log.append(("... sem entrega antes da compra", len(base)))

    # Só para análise (não é variável do modelo): avaliação criada antes da entrega
    base["avaliou_antes_entrega"] = (
        base["review_creation_date"] < base["order_delivered_customer_date"].dt.normalize()
    ).astype(int)

    base = adicionar_features_derivadas(base)
    base["negativa"] = (base["review_score"] <= 2).astype(int)

    if verbose:
        for texto, n in log:
            print(f"{texto:<45} {n:>8,}".replace(",", "."))
    return base.reset_index(drop=True)


def adicionar_features_derivadas(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula as variáveis derivadas. Usada no treino, no app e no script."""
    df = df.copy()
    valor = df["valor_produtos"].astype(float)
    df["frete_sobre_valor"] = np.where(valor > 0, df["valor_frete"] / valor.where(valor > 0, 1), 0.0)
    df["estados_diferentes"] = (df["uf_cliente"] != df["uf_vendedor"]).astype(int)
    df["parcelas"] = df["parcelas"].clip(lower=1)
    return df

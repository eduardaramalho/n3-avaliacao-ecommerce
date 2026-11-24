"""Transforma os campos do formulário (app ou linha de comando) nas variáveis do modelo.

O formulário pede só o que o atendimento conhece com facilidade. As duas
variáveis do modelo que não aparecem no formulário são estimadas assim:
- tempo_entrega = prazo estimado mediano para a UF do cliente + dias de atraso
  (mantém coerência: um pedido 10 dias atrasado também demorou mais para chegar);
- parcelas = mediana de parcelas da forma de pagamento escolhida (boleto = 1).
Os valores de referência vêm de models/referencia.json, gerado no notebook 02.
"""
import json

import pandas as pd

from src.config import ARQ_REFERENCIA, FEATURES
from src.preparacao import adicionar_features_derivadas

CAMPOS_FORMULARIO = [
    "categoria", "valor_produtos", "valor_frete", "qtd_itens",
    "pagamento", "uf_vendedor", "uf_cliente", "dias_atraso",
]


def carregar_referencia(caminho=ARQ_REFERENCIA) -> dict:
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def entrada_para_features(entrada: dict, ref: dict) -> pd.DataFrame:
    """Recebe um dicionário com CAMPOS_FORMULARIO e devolve 1 linha com FEATURES."""
    faltando = [c for c in CAMPOS_FORMULARIO if c not in entrada]
    if faltando:
        raise ValueError(f"Campos ausentes: {faltando}")

    prazo_uf = ref["prazo_mediano_por_uf"].get(entrada["uf_cliente"], ref["prazo_mediano_geral"])
    parcelas = ref["parcelas_mediana_por_pagamento"].get(entrada["pagamento"], 1)

    linha = {
        "categoria": entrada["categoria"],
        "valor_produtos": float(entrada["valor_produtos"]),
        "valor_frete": float(entrada["valor_frete"]),
        "qtd_itens": int(entrada["qtd_itens"]),
        "pagamento": entrada["pagamento"],
        "uf_vendedor": entrada["uf_vendedor"],
        "uf_cliente": entrada["uf_cliente"],
        "dias_atraso": int(entrada["dias_atraso"]),
        "tempo_entrega": max(1, int(round(prazo_uf + int(entrada["dias_atraso"])))),
        "parcelas": int(parcelas),
    }
    df = adicionar_features_derivadas(pd.DataFrame([linha]))
    return df[FEATURES]

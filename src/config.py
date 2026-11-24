"""Configurações compartilhadas entre notebooks, app e script de linha de comando.

Todos os caminhos são relativos à raiz do repositório, para funcionar igual
no computador de cada integrante e no Streamlit Community Cloud.
"""
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
# OLIST_DADOS permite apontar para outra pasta de dados sem mudar o código
PASTA_DADOS = Path(os.environ.get("OLIST_DADOS", RAIZ / "data"))
PASTA_MODELOS = RAIZ / "models"
PASTA_IMG = RAIZ / "img"

ARQ_MODELO = PASTA_MODELOS / "modelo.joblib"
ARQ_METRICAS = PASTA_MODELOS / "metricas.json"
ARQ_REFERENCIA = PASTA_MODELOS / "referencia.json"

URL_KAGGLE = "https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce"
URL_REPOSITORIO = "[LINK DO REPOSITÓRIO]"

ARQUIVOS_CSV = {
    "orders": "olist_orders_dataset.csv",
    "items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "traducao": "product_category_name_translation.csv",
}

SEMENTE = 42  # random_state fixo: qualquer pessoa que rodar obtém o mesmo resultado

# Variáveis de entrada do modelo (todas conhecidas antes de o cliente avaliar)
NUMERICAS = [
    "dias_atraso",        # data de entrega real menos data estimada (positivo = atrasou)
    "tempo_entrega",      # dias entre a compra e a entrega
    "valor_produtos",     # soma dos preços dos itens (R$)
    "valor_frete",        # soma do frete dos itens (R$)
    "frete_sobre_valor",  # frete / valor dos produtos
    "qtd_itens",          # quantidade de itens no pedido
    "parcelas",           # número de parcelas do pagamento principal
    "estados_diferentes", # 1 se a UF do vendedor for diferente da UF do cliente
]
CATEGORICAS = [
    "categoria",          # categoria do produto principal (item mais caro)
    "uf_cliente",
    "uf_vendedor",
    "pagamento",          # forma de pagamento principal (maior valor pago)
]
FEATURES = NUMERICAS + CATEGORICAS
ALVO = "negativa"  # 1 se review_score <= 2, senão 0

# Faixas de risco usadas no app (limite inferior de cada faixa, em probabilidade).
# Ponto de partida do protótipo. O notebook 02 confere se fazem sentido com a
# distribuição real das probabilidades.
FAIXAS_RISCO = [
    # (limite_inferior, nome, cor, ação sugerida)
    (0.00, "Risco baixo", "#16a34a",
     "Seguir o fluxo normal de atendimento."),
    (0.15, "Risco moderado", "#ca8a04",
     "Enviar mensagem proativa com o status da entrega."),
    (0.30, "Risco alto", "#ea580c",
     "Contato do atendimento antes da avaliação, explicando o atraso ou o problema."),
    (0.50, "Risco muito alto", "#dc2626",
     "Priorizar na fila do atendimento e oferecer compensação, como cupom ou frete grátis."),
]

FORMAS_PAGAMENTO = {
    "credit_card": "Cartão de crédito",
    "boleto": "Boleto",
    "voucher": "Voucher",
    "debit_card": "Cartão de débito",
}

UFS = ["AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS",
       "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC",
       "SE", "SP", "TO"]

# Nomes em português com acentuação para exibir no app.
# Categorias que não estão aqui são formatadas automaticamente.
NOMES_CATEGORIAS = {
    "cama_mesa_banho": "Cama, mesa e banho",
    "beleza_saude": "Beleza e saúde",
    "esporte_lazer": "Esporte e lazer",
    "moveis_decoracao": "Móveis e decoração",
    "informatica_acessorios": "Informática e acessórios",
    "utilidades_domesticas": "Utilidades domésticas",
    "relogios_presentes": "Relógios e presentes",
    "telefonia": "Telefonia",
    "ferramentas_jardim": "Ferramentas e jardim",
    "automotivo": "Automotivo",
    "brinquedos": "Brinquedos",
    "cool_stuff": "Cool stuff",
    "perfumaria": "Perfumaria",
    "bebes": "Bebês",
    "eletronicos": "Eletrônicos",
    "papelaria": "Papelaria",
    "fashion_bolsas_e_acessorios": "Moda: bolsas e acessórios",
    "pet_shop": "Pet shop",
    "moveis_escritorio": "Móveis de escritório",
    "consoles_games": "Consoles e games",
    "malas_acessorios": "Malas e acessórios",
    "construcao_ferramentas_construcao": "Construção: ferramentas",
    "eletrodomesticos": "Eletrodomésticos",
    "eletrodomesticos_2": "Eletrodomésticos 2",
    "instrumentos_musicais": "Instrumentos musicais",
    "eletroportateis": "Eletroportáteis",
    "casa_construcao": "Casa e construção",
    "livros_interesse_geral": "Livros de interesse geral",
    "livros_tecnicos": "Livros técnicos",
    "alimentos": "Alimentos",
    "alimentos_bebidas": "Alimentos e bebidas",
    "bebidas": "Bebidas",
    "moveis_sala": "Móveis de sala",
    "casa_conforto": "Casa e conforto",
    "audio": "Áudio",
    "climatizacao": "Climatização",
    "market_place": "Marketplace",
    "construcao_ferramentas_iluminacao": "Construção: iluminação",
    "construcao_ferramentas_jardim": "Construção: jardim",
    "construcao_ferramentas_seguranca": "Construção: segurança",
    "moveis_cozinha_area_de_servico_jantar_e_jardim": "Móveis de cozinha e área de serviço",
    "industria_comercio_e_negocios": "Indústria, comércio e negócios",
    "telefonia_fixa": "Telefonia fixa",
    "fashion_calcados": "Moda: calçados",
    "fashion_roupa_masculina": "Moda: roupa masculina",
    "agro_industria_e_comercio": "Agroindústria e comércio",
    "sinalizacao_e_seguranca": "Sinalização e segurança",
    "artigos_de_natal": "Artigos de Natal",
    "artes": "Artes",
    "pcs": "Computadores",
    "tablets_impressao_imagem": "Tablets, impressão e imagem",
    "outras": "Outras categorias",
    "sem_categoria": "Sem categoria",
}

# Categorias com menos pedidos que isso no treino viram "outras"
MIN_PEDIDOS_CATEGORIA = 300


def nome_categoria(codigo: str) -> str:
    """Converte o código da categoria (ex.: moveis_decoracao) em nome legível."""
    if codigo in NOMES_CATEGORIAS:
        return NOMES_CATEGORIAS[codigo]
    return str(codigo).replace("_", " ").capitalize()


def faixa_risco(prob: float):
    """Retorna (nome, cor, ação) da faixa correspondente à probabilidade."""
    escolhida = FAIXAS_RISCO[0]
    for faixa in FAIXAS_RISCO:
        if prob >= faixa[0]:
            escolhida = faixa
    _, nome, cor, acao = escolhida
    return nome, cor, acao

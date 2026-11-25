"""App Streamlit: risco de avaliação negativa de um pedido Olist.

Rodar localmente (na raiz do repositório):
    streamlit run app/app.py

Tema escuro, definido em .streamlit/config.toml e no dicionário CORES abaixo.
"""
import json
import sys
import unicodedata
from html import escape
from pathlib import Path

import joblib
import streamlit as st

# Permite importar src/ tanto localmente quanto no Streamlit Community Cloud
RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.config import (ARQ_METRICAS, ARQ_MODELO, FAIXAS_RISCO, FORMAS_PAGAMENTO,  # noqa: E402
                        URL_KAGGLE, URL_REPOSITORIO, UFS, faixa_risco, nome_categoria)
from src.explicacao import explicar, texto_frequencia  # noqa: E402
from src.features import carregar_referencia  # noqa: E402

st.set_page_config(page_title="Risco de avaliação negativa", layout="wide")

AZUL = "#2563eb"

# ---------------------------------------------------------------- cores
# Tema escuro, aprovado pela equipe para a apresentação no projetor.
# As mesmas cores estão em .streamlit/config.toml, para os campos do Streamlit combinarem.
CORES = {
    "fundo": "#0b1220", "cartao": "#111a2e", "borda": "#22304a", "borda_campo": "#33415c",
    "suave": "#1c2840", "texto": "#e5e9f0", "texto2": "#c3ccd9", "texto3": "#9aa7b8",
    "link": "#93b4ff", "ativo": "#1e2b4a",
    # (cor do texto, cor de fundo) de cada faixa de risco
    "faixas": {"Risco baixo": ("#4ade80", "#0f2a1c"), "Risco moderado": ("#facc15", "#2a2508"),
               "Risco alto": ("#fb923c", "#2e1a0c"), "Risco muito alto": ("#f87171", "#2f1215")},
    # (texto, fundo, borda) do selo de alerta
    "alerta_sim": ("#fdba74", "#2e1a0c", "#7c3a12"), "alerta_nao": ("#86efac", "#0f2a1c", "#1f5135"),
    # (barra, fundo do valor, texto do valor) dos fatores que somam e que tiram
    "fator_mais": ("#fb923c", "#2e1a0c", "#fdba74"), "fator_menos": (AZUL, "#1e2b4a", "#bfd2ff"),
    "matriz": {"vn": "#1e2b4a", "fp": "#1c2840", "fn": "#2e1a0c", "vp": "#25407a"},
}


def aplicar_css(c):
    st.markdown(f"""
<style>
  html, body, [class*="css"] {{ font-family: "Inter", "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
  .stApp {{ background: {c['fundo']}; }}
  header[data-testid="stHeader"] {{ background: transparent; }}
  .block-container {{ padding-top: 2.6rem; padding-bottom: 2rem; max-width: 1200px; }}
  h1, h2, h3, h4 {{ color: {c['texto']}; letter-spacing: -0.01em; }}
  div[data-testid="stVerticalBlockBorderWrapper"] {{ background: {c['cartao']}; border-color: {c['borda']} !important; border-radius: 14px; }}
  /* campos numéricos sem os botões de - e + */
  [data-testid="stNumberInputStepUp"], [data-testid="stNumberInputStepDown"] {{ display: none; }}
  /* slider: o valor aparece uma vez só, em texto acima dele */
  [data-testid="stSliderThumbValue"], [data-testid="stSliderTickBarMin"], [data-testid="stSliderTickBarMax"] {{ display: none; }}
  .stButton > button {{ border-radius: 999px; min-height: 44px; }}
  .stButton > button p {{ white-space: nowrap; font-size: 0.9rem; }}
  /* cabeçalho: logo, título e abas na mesma barra */
  .st-key-cabecalho {{ background: {c['cartao']}; border: 1px solid {c['borda']}; border-radius: 14px; padding: 8px 16px; margin-bottom: 0.6rem; }}
  .st-key-cabecalho [data-testid="stPageLink"] a {{ border-radius: 8px; padding: 6px 12px; }}
  .st-key-cabecalho [data-testid="stPageLink"] a[aria-current="page"] {{ background: {c['ativo']}; }}
  [data-testid="stPageLink"] p {{ white-space: nowrap; }}
  .rotulo-pequeno {{ font-size: 0.72rem; font-weight: 600; letter-spacing: 0.06em; color: {c['texto3']}; text-transform: uppercase; margin: 0 0 0.3rem; }}
  .cartao {{ background: {c['cartao']}; border: 1px solid {c['borda']}; border-radius: 14px; padding: 16px 18px; height: 100%; color: {c['texto2']}; }}
  .cartao a, .rodape a {{ color: {c['link']}; }}
  .metrica-titulo {{ font-size: 0.72rem; font-weight: 600; letter-spacing: 0.06em; color: {c['texto3']}; }}
  .metrica-valor {{ font-size: 1.9rem; font-weight: 800; color: {c['texto']}; line-height: 1.2; }}
  .metrica-desc {{ font-size: 0.8rem; color: {c['texto2']}; }}
  .chip {{ display: inline-block; background: {c['suave']}; border-radius: 999px; padding: 4px 12px; margin: 0 6px 6px 0; font-size: 0.82rem; color: {c['texto2']}; }}
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def carregar_modelo():
    return joblib.load(ARQ_MODELO)


@st.cache_data
def carregar_jsons():
    with open(ARQ_METRICAS, encoding="utf-8") as f:
        metricas = json.load(f)
    return metricas, carregar_referencia()


def cabecalho(c):
    with st.container(key="cabecalho"):
        logo, aba1, aba2, _ = st.columns([2.4, 1.3, 1.4, 3], vertical_alignment="center")
        logo.markdown(f"""
<div style="display:flex;align-items:center;gap:12px">
  <div style="width:38px;height:38px;border-radius:10px;background:{AZUL};display:flex;align-items:center;justify-content:center;flex-shrink:0">
    <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
      <polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/>
    </svg>
  </div>
  <div><div style="font-weight:700;font-size:1rem;color:{c['texto']};line-height:1.2">Risco de avaliação negativa</div>
  <div style="font-size:0.78rem;color:{c['texto3']}">E-commerce Olist · Equipe 4</div></div>
</div>""", unsafe_allow_html=True)
        aba1.page_link(PAGINA_PREVER, label="Prever pedido")
        aba2.page_link(PAGINA_SOBRE, label="Sobre o modelo")


def pct(v, casas=0):
    return f"{100 * v:.{casas}f}%".replace(".", ",")


def num(v, casas=2):
    return f"{v:.{casas}f}".replace(".", ",")


def sem_acento(texto):
    return "".join(ch for ch in unicodedata.normalize("NFD", texto) if unicodedata.category(ch) != "Mn").lower()


# ---------------------------------------------------------------- exemplos
EXEMPLOS = {
    "Pedido no prazo": dict(categoria="cama_mesa_banho", valor_produtos=90, valor_frete=15, qtd_itens=1,
                            pagamento="credit_card", uf_vendedor="SP", uf_cliente="SP", dias_atraso=-10),
    "Atraso longo": dict(categoria="moveis_decoracao", valor_produtos=180, valor_frete=45, qtd_itens=1,
                         pagamento="boleto", uf_vendedor="SP", uf_cliente="BA", dias_atraso=15),
    "Vários itens, outro estado": dict(categoria="informatica_acessorios", valor_produtos=250, valor_frete=60,
                                       qtd_itens=3, pagamento="credit_card", uf_vendedor="SP", uf_cliente="RJ",
                                       dias_atraso=0),
}


def aplicar_exemplo(nome):
    for campo, valor in EXEMPLOS[nome].items():
        st.session_state[campo] = valor


def exemplo_ativo():
    """Nome do exemplo cujos valores estão no formulário agora (ou None, se a pessoa mudou algo)."""
    for nome, valores in EXEMPLOS.items():
        if all(st.session_state.get(k) == v for k, v in valores.items()):
            return nome
    return None


def texto_atraso(d):
    if d > 0:
        return f"{d} dia{'s' if d != 1 else ''} atrasado"
    if d < 0:
        return f"{-d} dia{'s' if d != -1 else ''} adiantado"
    return "no prazo"


# ---------------------------------------------------------------- página 1
def pagina_prever():
    c = CORES
    aplicar_css(c)
    modelo = carregar_modelo()
    metricas, ref = carregar_jsons()

    if "categoria" not in st.session_state:
        aplicar_exemplo("Atraso longo")

    cabecalho(c)
    st.markdown("### Qual a chance deste pedido receber nota 1 ou 2?")
    st.markdown(f"<p style='color:{c['texto3']};margin-top:-0.7rem'>Informe os dados do pedido. "
                "O atendimento usa o resultado para agir antes de o cliente avaliar.</p>", unsafe_allow_html=True)

    esq, dir_ = st.columns(2, gap="medium")

    with esq, st.container(border=True):
        st.markdown("#### Dados do pedido")
        st.markdown("<div class='rotulo-pequeno'>Exemplos rápidos</div>", unsafe_allow_html=True)
        ativo = exemplo_ativo()
        b1, b2, b3 = st.columns([1.1, 0.95, 1.6])
        for col, nome in zip([b1, b2, b3], EXEMPLOS):
            col.button(nome, on_click=aplicar_exemplo, args=(nome,), use_container_width=True,
                       type="primary" if nome == ativo else "secondary",
                       icon=":material/check:" if nome == ativo else None)

        categorias = sorted(ref["categorias"], key=lambda k: sem_acento(nome_categoria(k)))
        if st.session_state.get("categoria") not in categorias:
            st.session_state["categoria"] = ref["pedido_tipico"]["categoria"]
        st.selectbox("Categoria do produto", categorias, key="categoria", format_func=nome_categoria)
        c1, c2 = st.columns(2)
        c1.number_input("Valor dos produtos (R$)", min_value=1, max_value=15000, step=1, key="valor_produtos")
        c2.number_input("Frete (R$)", min_value=0, max_value=2000, step=1, key="valor_frete")
        c1, c2 = st.columns(2)
        c1.number_input("Quantidade de itens", min_value=1, max_value=20, step=1, key="qtd_itens")
        c2.selectbox("Pagamento", sorted(FORMAS_PAGAMENTO, key=lambda k: FORMAS_PAGAMENTO[k]),
                     key="pagamento", format_func=FORMAS_PAGAMENTO.get)
        c1, c2 = st.columns(2)
        c1.selectbox("UF do vendedor", UFS, key="uf_vendedor")
        c2.selectbox("UF do cliente", UFS, key="uf_cliente")

        d = st.session_state["dias_atraso"]
        st.markdown(f"<div style='display:flex;justify-content:space-between;margin-top:0.3rem;color:{c['texto2']};font-size:0.9rem'>"
                    f"<span>Entrega em relação ao prazo estimado</span><b style='color:{c['texto']}'>{texto_atraso(d)}</b></div>",
                    unsafe_allow_html=True)
        st.slider("Entrega em relação ao prazo estimado", min_value=-15, max_value=30, step=1,
                  key="dias_atraso", label_visibility="collapsed")
        # "no prazo" fica na posição do 0 no slider (15 de 45 passos = 33%)
        st.markdown(f"<div style='position:relative;height:1.2rem;font-size:0.8rem;color:{c['texto3']};margin-top:-1rem'>"
                    "<span style='position:absolute;left:0'>15 dias adiantado</span>"
                    "<span style='position:absolute;left:33.3%;transform:translateX(-50%)'>no prazo</span>"
                    "<span style='position:absolute;right:0'>30 dias atrasado</span></div>",
                    unsafe_allow_html=True)

    entrada = {k: st.session_state[k] for k in EXEMPLOS["Pedido no prazo"]}
    prob, fatores = explicar(modelo, entrada, ref)
    nome_faixa, _, acao = faixa_risco(prob)
    cor, fundo = c["faixas"][nome_faixa]
    alerta = prob >= metricas["threshold"]

    with dir_:
        limites = [f[0] for f in FAIXAS_RISCO]
        nomes_escala = [n.replace("Risco ", "").capitalize() for _, n, _, _ in FAIXAS_RISCO]
        nomes_escala[0] += f" &lt;{pct(limites[1])}"
        nomes_escala[-1] += f" ≥{pct(limites[-1])}"
        marcas = "".join(f"<span>{n}</span>" for n in nomes_escala)

        a_txt, a_bg, a_borda = c["alerta_sim"] if alerta else c["alerta_nao"]
        icone_alerta = ('<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>'
                        if alerta else '<polyline points="20 6 9 17 4 12"/>')
        texto_alerta = "Entra na lista de alertas do atendimento" if alerta else "Não entra na lista de alertas"

        maior = max([abs(f["pp"]) for f in fatores] + [10])  # escala mínima: efeito pequeno = barra pequena

        def linha_fator(f):
            barra, pill_bg, pill_txt = c["fator_mais"] if f["pp"] > 0 else c["fator_menos"]
            sinal = "+" if f["pp"] > 0 else "−"
            return (f"<div style='display:flex;align-items:center;gap:12px;padding:7px 0;border-top:1px solid {c['suave']}'>"
                    f"<div style='flex:1;color:{c['texto']};font-size:0.92rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>{escape(f['rotulo'])}</div>"
                    f"<div style='width:120px;height:8px;background:{c['suave']};border-radius:4px;overflow:hidden'>"
                    f"<div style='width:{100 * abs(f['pp']) / maior:.0f}%;height:100%;border-radius:4px;background:{barra}'></div></div>"
                    f"<div style='min-width:76px;text-align:center;font-weight:700;font-size:0.85rem;border-radius:6px;padding:3px 6px;"
                    f"background:{pill_bg};color:{pill_txt}'>{sinal}{num(abs(f['pp']), 1)} p.p.</div></div>")

        linhas = "".join(linha_fator(f) for f in fatores) or (
            f"<div style='font-size:0.92rem;color:{c['texto2']};background:{c['suave']};border-radius:8px;padding:10px 12px'>"
            "Nenhum fator pesa muito: este pedido é parecido com um pedido típico.</div>")

        st.markdown(f"""
<div style="border:1px solid {c['borda']};border-radius:14px;overflow:hidden;background:{c['cartao']}">
  <div style="background:{fundo};padding:18px 20px 14px">
    <div style="color:{c['texto2']};font-size:0.9rem">Chance de avaliação negativa (nota 1 ou 2)</div>
    <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;margin-top:4px">
      <div style="font-size:4rem;font-weight:800;color:{cor};line-height:1;letter-spacing:-0.02em">{pct(prob)}</div>
      <div style="display:flex;flex-direction:column;gap:6px">
        <span style="align-self:flex-start;background:{c['cartao']};color:{cor};font-weight:700;border-radius:999px;padding:3px 12px;font-size:0.9rem;border:1px solid {cor}">{escape(nome_faixa)}</span>
        <span style="color:{c['texto2']};font-size:0.85rem">{texto_frequencia(prob)}</span>
      </div>
    </div>
    <div style="height:10px;background:{c['borda']};border-radius:5px;margin-top:16px;overflow:hidden">
      <div style="width:{100 * prob:.1f}%;height:100%;background:{cor};border-radius:5px"></div>
    </div>
    <div style="display:flex;justify-content:space-between;font-size:0.75rem;color:{c['texto3']};margin-top:6px">{marcas}</div>
  </div>
  <div style="padding:16px 20px 18px;display:flex;flex-direction:column;gap:14px">
    <div style="display:flex;align-items:center;gap:8px;font-size:0.9rem;font-weight:600;color:{a_txt};background:{a_bg};border:1px solid {a_borda};border-radius:10px;padding:10px 12px">
      <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">{icone_alerta}</svg>
      <span>{texto_alerta}</span>
    </div>
    <div style="border:1px solid {c['borda']};background:{c['fundo']};border-radius:10px;padding:12px 14px;display:flex;gap:12px">
      <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{AZUL}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;margin-top:2px"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
      <div><div class="rotulo-pequeno" style="margin:0">Ação sugerida para o atendimento</div>
      <div style="color:{c['texto']};font-size:0.98rem">{escape(acao)}</div></div>
    </div>
    <div>
      <div style="font-weight:700;font-size:1.02rem;color:{c['texto']}">Por que esse valor?</div>
      <div style="font-size:0.8rem;color:{c['texto3']};margin-bottom:6px">O que mais soma (+) ou tira (−) da chance, comparado a um pedido típico.</div>
      {linhas}
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

        with st.expander("Como esse cálculo é feito"):
            t = ref["pedido_tipico"]
            st.markdown(
                "Para cada campo, trocamos **só aquele campo** pelo valor de um pedido típico do treino "
                "e recalculamos a probabilidade com o mesmo modelo. A diferença é o efeito do campo neste pedido. "
                "Mostramos só efeitos de 1 p.p. ou mais. Como a Random Forest não é linear, os efeitos não somam "
                "exatamente a probabilidade final.\n\n"
                f"Pedido típico: {nome_categoria(t['categoria'])}, R$ {t['valor_produtos']:.0f} em produtos, "
                f"R$ {t['valor_frete']:.0f} de frete, {t['qtd_itens']} item, {FORMAS_PAGAMENTO[t['pagamento']]}, "
                f"vendedor e cliente em {t['uf_cliente']}, entrega {texto_atraso(t['dias_atraso'])}.\n\n"
                "Campos que não estão no formulário são estimados: tempo de entrega = prazo mediano da UF do cliente "
                "+ dias de atraso; parcelas = mediana da forma de pagamento.\n\n"
                f"A lista de alertas inclui pedidos com chance a partir de {pct(metricas['threshold'], 1)} "
                "(threshold escolhido no notebook 02)."
            )
        r1, r2 = st.columns([1.5, 1.2], vertical_alignment="center")
        r1.markdown(f"<div style='font-size:0.85rem;color:{c['texto3']}'>Chance média de um pedido qualquer: "
                    f"<b style='color:{c['texto']}'>{pct(ref['taxa_base'], 1)}</b></div>", unsafe_allow_html=True)
        r2.page_link(PAGINA_SOBRE, label="Como o modelo foi treinado")


# ---------------------------------------------------------------- página 2
def cartao(c, titulo, corpo_html):
    return (f"<div class='cartao'><div style='font-weight:700;font-size:1.02rem;margin-bottom:6px;color:{c['texto']}'>"
            f"{titulo}</div>{corpo_html}</div>")


def pagina_sobre():
    c = CORES
    aplicar_css(c)
    m, ref = carregar_jsons()
    rf, lr = m["teste"]["random_forest"], m["teste"]["baseline"]
    mc = m["matriz_confusao"]
    milhar = lambda v: f"{v:,}".replace(",", ".")  # noqa: E731

    cabecalho(c)
    st.markdown("### Sobre o modelo")
    st.markdown(f"<p style='color:{c['texto3']};margin-top:-0.7rem'>Um classificador estima, para cada pedido entregue, "
                "a chance de o cliente dar nota 1 ou 2. O objetivo é que o atendimento aja antes da avaliação.</p>",
                unsafe_allow_html=True)

    lista = "margin:0;padding-left:18px;line-height:1.6;font-size:0.92rem"
    c1, c2 = st.columns(2)
    c1.markdown(cartao(c, "Problema e público", f"""<ul style='{lista}'>
        <li>Alvo: avaliação negativa (nota 1 ou 2) = 1; notas 3 a 5 = 0.</li>
        <li>Quem usa: atendimento e CX do marketplace, para priorizar contatos.</li>
        <li>Também útil para logística e para a gestão de vendedores.</li></ul>"""), unsafe_allow_html=True)
    c2.markdown(cartao(c, "Dados", f"""<ul style='{lista}'>
        <li>Brazilian E-Commerce Public Dataset by Olist (Kaggle).</li>
        <li>{milhar(m['n_pedidos'])} pedidos entregues e avaliados, de {m['periodo']['inicio']} a {m['periodo']['fim']}.</li>
        <li>8 tabelas unidas por pedido: pedidos, itens, pagamentos, avaliações, clientes, vendedores, produtos e tradução de categorias.</li>
        <li><a href='{URL_KAGGLE}' target='_blank'>Página do dataset</a></li></ul>"""), unsafe_allow_html=True)

    st.write("")
    chips = "".join(f"<span class='chip'>{v}</span>" for v in [
        "Dias de atraso vs. prazo", "Tempo de entrega", "Quantidade de itens", "Valor e frete", "Frete / valor",
        "Categoria", "UF do cliente e do vendedor", "Vendedor em outro estado", "Pagamento e parcelas"])
    st.markdown(cartao(c, "Variáveis usadas", chips + f"<div style='font-size:0.85rem;color:{c['texto3']};margin-top:4px'>"
                       "Texto e datas da avaliação ficaram de fora: só existem depois que o cliente avalia "
                       "e vazariam o alvo.</div>"), unsafe_allow_html=True)

    # "De cada 100 pedidos": tradução da matriz de confusão para o atendimento
    st.write("")
    n = m["n_teste"]
    blocos = [(num(100 * rf["perc_alertas"], 0), "entram na lista de alertas"),
              (num(100 * mc["vp"] / n, 1), "desses alertas são clientes realmente insatisfeitos"),
              (num(100 * mc["fn"] / n, 1), f"insatisfeitos não são alertados ({num(100 * m['taxa_base'], 1)} no total)")]
    cards = "".join(f"<div style='flex:1 1 200px;border:1px solid {c['borda']};border-radius:12px;padding:12px 16px'>"
                    f"<div style='font-size:2rem;font-weight:800;color:{c['texto']}'>{v}</div>"
                    f"<div style='font-size:0.9rem'>{t}</div></div>" for v, t in blocos)
    st.markdown(cartao(c, "Na prática, de cada 100 pedidos de teste",
                       f"<div style='font-size:0.85rem;color:{c['texto3']};margin:-4px 0 10px'>Random Forest com threshold de "
                       f"{pct(m['threshold'])}.</div><div style='display:flex;flex-wrap:wrap;gap:12px'>{cards}</div>"),
                unsafe_allow_html=True)

    st.write("")
    with st.container(border=True):
        a, b = st.columns([1.2, 1.8])
        a.markdown("#### Desempenho no conjunto de teste")
        b.markdown(f"<div style='text-align:right;color:{c['texto3']};padding-top:0.6rem'>{milhar(n)} pedidos nunca vistos "
                   f"no treino · {m['modelo_final']} vs. {m['baseline']}</div>", unsafe_allow_html=True)
        cards = [("RECALL", "recall", "insatisfeitos que o modelo encontra"),
                 ("PRECISÃO", "precisao", "alertas que eram mesmo insatisfeitos"),
                 ("F1", "f1", "equilíbrio entre os dois"),
                 ("ROC-AUC", "roc_auc", "separação geral das classes")]
        for col, (tit, k, desc) in zip(st.columns(4), cards):
            col.markdown(f"<div class='cartao'><div class='metrica-titulo'>{tit}</div>"
                         f"<div class='metrica-valor'>{num(rf[k])}</div><div class='metrica-desc'>{desc}</div>"
                         f"<div class='metrica-desc' style='margin-top:4px;color:{c['texto3']}'>baseline: {num(lr[k])}</div>"
                         "</div>", unsafe_allow_html=True)

        st.write("")
        e, d = st.columns([1, 1.5])

        def celula(v, rotulo, cor_fundo):
            return (f"<div style='background:{cor_fundo};border-radius:8px;padding:12px;text-align:center'>"
                    f"<b style='font-size:1.1rem;color:{c['texto']}'>{milhar(v)}</b>"
                    f"<div style='font-size:0.72rem;color:{c['texto3']}'>{rotulo}</div></div>")
        cm = c["matriz"]
        e.markdown(f"""<div style='font-weight:700;color:{c['texto']};margin-bottom:8px'>Matriz de confusão</div>
<div style='display:grid;grid-template-columns:100px repeat(2,minmax(0,1fr));gap:6px;font-size:0.85rem;color:{c['texto2']};align-items:center;margin-bottom:10px'>
<span></span><span style='text-align:center'>Previsto: não</span><span style='text-align:center'>Previsto: negativa</span>
<span>Real: não</span>{celula(mc['vn'], 'acerto sem alerta', cm['vn'])}{celula(mc['fp'], 'alerta à toa', cm['fp'])}
<span>Real: negativa</span>{celula(mc['fn'], 'escapou', cm['fn'])}{celula(mc['vp'], 'alerta certo', cm['vp'])}
</div>""", unsafe_allow_html=True)
        d.markdown(f"""<div style='font-weight:700;color:{c['texto']};margin-bottom:8px'>Como foi avaliado</div>
<ul style='padding-left:18px;color:{c['texto2']};font-size:0.92rem;line-height:1.6;margin:0'>
<li>Divisão treino/teste {m['divisao']} ({milhar(m['n_treino'])} e {milhar(n)} pedidos) e validação cruzada estratificada com {m['k_folds']} partes no treino.</li>
<li>Só {pct(m['taxa_base'], 1)} de negativas: foco em recall, precisão, F1 e PR-AUC, não em acurácia.</li>
<li>Threshold de {pct(m['threshold'], 1)}, escolhido pelo {m['criterio_threshold']} (sem usar o teste).</li>
<li>PR-AUC: {num(rf['pr_auc'])} (baseline {num(lr['pr_auc'])}; um chute daria {num(m['taxa_base'])}).</li>
</ul>""", unsafe_allow_html=True)

    st.write("")
    st.markdown(cartao(c, "Limitações", f"""<ul style='{lista}'>
        <li>Defeito, item errado ou faltando não aparecem nos dados: quase todos os insatisfeitos que escapam receberam o pedido no prazo.</li>
        <li>Boa parte do acerto vem de pedidos atrasados em que o cliente avaliou antes de receber (29% das notas negativas). O alerta é mais útil assim que o prazo estimado vence.</li>
        <li>Dados de 2016 a 2018. Em pedidos mais recentes, com menos atrasos, o desempenho cai: o modelo precisaria ser retreinado com frequência.</li>
        <li>Falsos positivos são pedidos com perfil de risco em que o cliente foi tolerante. O custo é um contato a mais.</li>
        </ul>"""), unsafe_allow_html=True)
    st.markdown(f"<div class='rodape' style='font-size:0.85rem;color:{c['texto3']};margin-top:14px'>Projeto final de "
                f"Aprendizagem de Máquina · Equipe 4: Eduarda, Eduardo e Anna · "
                f"<a href='{URL_REPOSITORIO}' target='_blank'>Repositório no GitHub</a></div>", unsafe_allow_html=True)


PAGINA_PREVER = st.Page(pagina_prever, title="Prever pedido", default=True)
PAGINA_SOBRE = st.Page(pagina_sobre, title="Sobre o modelo", url_path="sobre")
st.navigation([PAGINA_PREVER, PAGINA_SOBRE], position="hidden").run()

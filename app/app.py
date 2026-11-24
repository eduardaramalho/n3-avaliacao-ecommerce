"""App Streamlit: risco de avaliação negativa de um pedido Olist.

Rodar localmente (na raiz do repositório):
    streamlit run app/app.py
"""
import json
import sys
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
CORES_FUNDO = {"#16a34a": "#f0fdf4", "#ca8a04": "#fefce8", "#ea580c": "#fff7ed", "#dc2626": "#fef2f2"}

st.markdown(f"""
<style>
  html, body, [class*="css"] {{ font-family: "Inter", "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
  .stApp {{ background: #f8fafc; }}
  .block-container {{ padding-top: 3.2rem; max-width: 1200px; }}
  .stButton > button p {{ white-space: nowrap; font-size: 0.88rem; }}
  table.matriz td, table.matriz tr, table.matriz {{ border: none !important; }}
  h1, h2, h3 {{ color: #0f172a; letter-spacing: -0.01em; }}
  div[data-testid="stVerticalBlockBorderWrapper"] {{ background: #ffffff; border-radius: 14px; }}
  .stButton > button {{ border-radius: 999px; border: 1px solid #cbd5e1; background: #fff; font-size: 0.9rem; }}
  .stButton > button:hover {{ border-color: {AZUL}; color: {AZUL}; }}
  .rotulo-pequeno {{ font-size: 0.75rem; font-weight: 600; letter-spacing: 0.06em; color: #64748b; text-transform: uppercase; margin: 0.2rem 0 0.4rem; }}
  .cabecalho {{ display: flex; align-items: center; gap: 12px; margin-bottom: 0.6rem; }}
  .logo {{ width: 40px; height: 40px; border-radius: 10px; background: {AZUL}; display: flex; align-items: center; justify-content: center; }}
  .cab-titulo {{ font-weight: 700; font-size: 1.05rem; color: #0f172a; line-height: 1.1; }}
  .cab-sub {{ font-size: 0.8rem; color: #64748b; }}
  .cartao {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 16px 18px; height: 100%; }}
  .metrica-titulo {{ font-size: 0.72rem; font-weight: 600; letter-spacing: 0.06em; color: #64748b; }}
  .metrica-valor {{ font-size: 1.9rem; font-weight: 800; color: #0f172a; line-height: 1.2; }}
  .metrica-desc {{ font-size: 0.78rem; color: #64748b; }}
  .chip {{ display: inline-block; background: #f1f5f9; border-radius: 999px; padding: 4px 12px; margin: 0 6px 6px 0; font-size: 0.82rem; color: #334155; }}
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


def cabecalho():
    st.markdown("""
    <div class="cabecalho">
      <div class="logo">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
          <polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/>
        </svg>
      </div>
      <div><div class="cab-titulo">Risco de avaliação negativa</div><div class="cab-sub">E-commerce Olist · Equipe 4</div></div>
    </div>
    """, unsafe_allow_html=True)


def pct(v, casas=0):
    return f"{100 * v:.{casas}f}%".replace(".", ",")


# ---------------------------------------------------------------- exemplos
EXEMPLOS = {
    "Pedido no prazo": dict(categoria="cama_mesa_banho", valor_produtos=90.0, valor_frete=15.0, qtd_itens=1,
                            pagamento="credit_card", uf_vendedor="SP", uf_cliente="SP", dias_atraso=-10),
    "Atraso longo": dict(categoria="moveis_decoracao", valor_produtos=180.0, valor_frete=45.0, qtd_itens=1,
                         pagamento="boleto", uf_vendedor="SP", uf_cliente="BA", dias_atraso=15),
    "Vários itens, outro estado": dict(categoria="informatica_acessorios", valor_produtos=250.0, valor_frete=60.0,
                                       qtd_itens=3, pagamento="credit_card", uf_vendedor="SP", uf_cliente="RJ",
                                       dias_atraso=0),
}


def aplicar_exemplo(nome):
    for campo, valor in EXEMPLOS[nome].items():
        st.session_state[campo] = valor


def texto_atraso(d):
    if d > 0:
        return f"{d} dia{'s' if d != 1 else ''} atrasado"
    if d < 0:
        return f"{-d} dia{'s' if d != -1 else ''} adiantado"
    return "no prazo"


# ---------------------------------------------------------------- página 1
def pagina_prever():
    modelo = carregar_modelo()
    metricas, ref = carregar_jsons()

    if "categoria" not in st.session_state:
        aplicar_exemplo("Atraso longo")

    cabecalho()
    st.markdown("## Qual a chance deste pedido receber nota 1 ou 2?")
    st.markdown("<p style='color:#475569;margin-top:-0.6rem'>Informe os dados do pedido. "
                "O atendimento usa o resultado para agir antes de o cliente avaliar.</p>", unsafe_allow_html=True)

    esq, dir_ = st.columns(2, gap="medium")

    with esq, st.container(border=True):
        st.markdown("#### Dados do pedido")
        st.markdown("<div class='rotulo-pequeno'>Exemplos rápidos</div>", unsafe_allow_html=True)
        b1, b2, b3 = st.columns([1.05, 0.85, 1.55])
        for col, nome in zip([b1, b2, b3], EXEMPLOS):
            col.button(nome, on_click=aplicar_exemplo, args=(nome,), use_container_width=True)

        categorias = ref["categorias"]
        if st.session_state.get("categoria") not in categorias:
            st.session_state["categoria"] = ref["pedido_tipico"]["categoria"]
        st.selectbox("Categoria do produto", categorias, key="categoria", format_func=nome_categoria)
        c1, c2 = st.columns(2)
        c1.number_input("Valor dos produtos (R$)", min_value=1.0, max_value=15000.0, step=10.0, key="valor_produtos")
        c2.number_input("Frete (R$)", min_value=0.0, max_value=2000.0, step=5.0, key="valor_frete")
        c1, c2 = st.columns(2)
        c1.number_input("Quantidade de itens", min_value=1, max_value=20, step=1, key="qtd_itens")
        c2.selectbox("Pagamento", list(FORMAS_PAGAMENTO), key="pagamento", format_func=FORMAS_PAGAMENTO.get)
        c1, c2 = st.columns(2)
        c1.selectbox("UF do vendedor", UFS, key="uf_vendedor")
        c2.selectbox("UF do cliente", UFS, key="uf_cliente")

        d = st.session_state["dias_atraso"]
        st.markdown(f"<div style='display:flex;justify-content:space-between;margin-top:0.4rem'>"
                    f"<span>Entrega em relação ao prazo estimado</span><b>{texto_atraso(d)}</b></div>",
                    unsafe_allow_html=True)
        st.slider("Entrega em relação ao prazo estimado", min_value=-15, max_value=30, step=1,
                  key="dias_atraso", label_visibility="collapsed")
        # "no prazo" fica na posição do 0 no slider (15 de 45 passos = 33%)
        st.markdown("<div style='position:relative;height:1.2rem;font-size:0.8rem;color:#64748b;margin-top:-0.8rem'>"
                    "<span style='position:absolute;left:0'>15 dias adiantado</span>"
                    "<span style='position:absolute;left:33.3%;transform:translateX(-50%)'>no prazo</span>"
                    "<span style='position:absolute;right:0'>30 dias atrasado</span></div>",
                    unsafe_allow_html=True)

    entrada = {c: st.session_state[c] for c in EXEMPLOS["Pedido no prazo"]}
    prob, fatores = explicar(modelo, entrada, ref)
    nome_faixa, cor, acao = faixa_risco(prob)
    fundo = CORES_FUNDO.get(cor, "#f8fafc")

    with dir_:
        limites = [f[0] for f in FAIXAS_RISCO]
        nomes_escala = [n.replace("Risco ", "").capitalize() for _, n, _, _ in FAIXAS_RISCO]
        nomes_escala[0] += f" &lt;{pct(limites[1])}"
        nomes_escala[-1] += f" ≥{pct(limites[-1])}"
        marcas = "".join(f"<span>{n}</span>" for n in nomes_escala)
        # escala mínima de 10 p.p.: efeitos pequenos aparecem como barras pequenas
        maior = max([abs(f["pp"]) for f in fatores] + [10])
        linhas_fatores = "".join(
            f"<div style='display:flex;align-items:center;gap:10px;margin:7px 0'>"
            f"<div style='flex:1;color:#334155;font-size:0.92rem'>{escape(f['rotulo'])}</div>"
            f"<div style='width:120px;height:8px;background:#f1f5f9;border-radius:4px;overflow:hidden'>"
            f"<div style='width:{100 * abs(f['pp']) / maior:.0f}%;height:100%;border-radius:4px;"
            f"background:{'#ea580c' if f['pp'] > 0 else '#16a34a'}'></div></div>"
            f"<div style='width:84px;text-align:center;font-weight:700;font-size:0.85rem;border-radius:6px;padding:2px 4px;"
            f"background:{'#fff7ed' if f['pp'] > 0 else '#f0fdf4'};color:{'#9a3412' if f['pp'] > 0 else '#166534'}'>"
            f"{f['pp']:+.1f}".replace(".", ",") + " p.p.</div></div>"
            for f in fatores) or "<div style='color:#64748b'>Este pedido é parecido com um pedido típico.</div>"

        st.markdown(f"""
<div style="border:1px solid #e2e8f0;border-radius:14px;overflow:hidden;background:#fff">
  <div style="background:{fundo};padding:18px 20px 14px">
    <div style="color:#334155;font-size:0.92rem">Chance de avaliação negativa (nota 1 ou 2)</div>
    <div style="display:flex;align-items:center;gap:16px;margin-top:2px">
      <div style="font-size:4rem;font-weight:800;color:{cor};line-height:1">{pct(prob)}</div>
      <div>
        <span style="background:#fff;color:{cor};font-weight:700;border-radius:999px;padding:3px 12px;font-size:0.9rem">{escape(nome_faixa)}</span>
        <div style="color:#475569;font-size:0.85rem;margin-top:6px">{texto_frequencia(prob)}</div>
      </div>
    </div>
    <div style="height:10px;background:#e2e8f0;border-radius:5px;margin-top:16px;overflow:hidden">
      <div style="width:{100 * prob:.1f}%;height:100%;background:{cor};border-radius:5px"></div>
    </div>
    <div style="display:flex;justify-content:space-between;font-size:0.75rem;color:#64748b;margin-top:4px">{marcas}</div>
  </div>
  <div style="padding:16px 20px">
    <div style="border:1px solid #e2e8f0;background:#f8fafc;border-radius:10px;padding:12px 14px;display:flex;gap:12px">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{AZUL}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;margin-top:2px"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
      <div><div class="rotulo-pequeno" style="margin:0">Ação sugerida para o atendimento</div>
      <div style="color:#0f172a;font-size:1rem">{escape(acao)}</div></div>
    </div>
    <div style="font-weight:700;font-size:1.05rem;margin-top:16px;color:#0f172a">Por que esse valor?</div>
    <div style="font-size:0.8rem;color:#64748b">Quanto cada campo soma (+) ou tira (−) da chance, em pontos percentuais,
      comparado a um pedido típico do treino.</div>
    {linhas_fatores}
  </div>
</div>
""", unsafe_allow_html=True)

        with st.expander("Como o \"Por que esse valor?\" é calculado"):
            t = ref["pedido_tipico"]
            st.markdown(
                "Para cada campo, trocamos **só aquele campo** pelo valor de um pedido típico do treino "
                "e recalculamos a probabilidade com o mesmo modelo. A diferença é o efeito do campo neste pedido. "
                "Como a Random Forest não é linear, os efeitos não somam exatamente a probabilidade final.\n\n"
                f"Pedido típico: {nome_categoria(t['categoria'])}, R$ {t['valor_produtos']:.0f} em produtos, "
                f"R$ {t['valor_frete']:.0f} de frete, {t['qtd_itens']} item, {FORMAS_PAGAMENTO[t['pagamento']]}, "
                f"vendedor e cliente em {t['uf_cliente']}, entrega {texto_atraso(t['dias_atraso'])}.\n\n"
                "Campos que não estão no formulário são estimados: tempo de entrega = prazo mediano da UF do cliente "
                "+ dias de atraso; parcelas = mediana da forma de pagamento."
            )
        st.markdown(f"<div style='font-size:0.85rem;color:#475569;margin-top:6px'>Referência: chance média de um "
                    f"pedido qualquer no treino = <b>{pct(ref['taxa_base'], 1)}</b>. Alerta para o atendimento a partir de "
                    f"{pct(metricas['threshold'], 1)}.</div>", unsafe_allow_html=True)
        st.page_link(PAGINA_SOBRE, label="Como o modelo foi treinado")


# ---------------------------------------------------------------- página 2
def cartao(titulo_html, corpo_html):
    return f"<div class='cartao'><div style='font-weight:700;font-size:1.05rem;margin-bottom:6px'>{titulo_html}</div>{corpo_html}</div>"


def pagina_sobre():
    m, ref = carregar_jsons()
    rf, lr = m["teste"]["random_forest"], m["teste"]["baseline"]
    cabecalho()
    st.markdown("## Sobre o modelo")
    st.markdown("<p style='color:#475569;margin-top:-0.6rem'>Um classificador estima, para cada pedido entregue, a chance de "
                "o cliente dar nota 1 ou 2. O objetivo é que o atendimento aja antes da avaliação.</p>",
                unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    c1.markdown(cartao("Problema e público", """<ul style='margin:0;padding-left:18px;color:#334155'>
        <li>Alvo: avaliação negativa (nota 1 ou 2) = 1; notas 3 a 5 = 0.</li>
        <li>Quem usa: atendimento e CX do marketplace, para priorizar contatos.</li>
        <li>Também útil para logística e para a gestão de vendedores.</li></ul>"""), unsafe_allow_html=True)
    c2.markdown(cartao("Dados", f"""<ul style='margin:0;padding-left:18px;color:#334155'>
        <li>Brazilian E-Commerce Public Dataset by Olist (Kaggle).</li>
        <li>{m['n_pedidos']:,} pedidos entregues e avaliados, de {m['periodo']['inicio']} a {m['periodo']['fim']}.</li>
        <li>Tabelas unidas por pedido: pedidos, itens, pagamentos, avaliações, clientes, vendedores, produtos e tradução de categorias.</li>
        <li><a href='{URL_KAGGLE}' target='_blank'>Página do dataset</a></li></ul>""".replace(",", ".", 1)),
                unsafe_allow_html=True)

    st.write("")
    chips = "".join(f"<span class='chip'>{v}</span>" for v in [
        "Dias de atraso vs. prazo estimado", "Tempo de entrega", "Valor dos produtos", "Frete e frete / valor",
        "Quantidade de itens", "Categoria do produto", "UF do cliente e do vendedor", "Vendedor em outro estado",
        "Forma de pagamento e parcelas"])
    st.markdown(cartao("Variáveis usadas", chips + "<div style='font-size:0.85rem;color:#475569;margin-top:6px'>"
                       "Texto, título e datas da avaliação ficaram de fora: só existem depois que o cliente avalia "
                       "e vazariam o alvo.</div>"), unsafe_allow_html=True)

    st.write("")
    with st.container(border=True):
        a, b = st.columns([1.2, 1.8])
        a.markdown("#### Desempenho no conjunto de teste")
        b.markdown(f"<div style='text-align:right;color:#475569;padding-top:0.6rem'>Modelo: {m['modelo_final']} · "
                   f"baseline: {m['baseline']}</div>", unsafe_allow_html=True)
        cards = [("RECALL", "recall", "negativas que o modelo encontra"),
                 ("PRECISÃO", "precisao", "alertas que eram mesmo negativas"),
                 ("F1", "f1", "equilíbrio entre os dois"),
                 ("ROC-AUC", "roc_auc", "separação geral das classes")]
        for col, (tit, k, desc) in zip(st.columns(4), cards):
            col.markdown(f"<div class='cartao'><div class='metrica-titulo'>{tit}</div>"
                         f"<div class='metrica-valor'>{rf[k]:.2f}".replace(".", ",") +
                         f"</div><div class='metrica-desc'>{desc}</div>"
                         f"<div class='metrica-desc' style='margin-top:4px'>baseline: {lr[k]:.2f}".replace(".", ",") +
                         "</div></div>", unsafe_allow_html=True)

        st.write("")
        e, d = st.columns([1, 1.6])
        mc = m["matriz_confusao"]

        def celula(v, rotulo, fundo):
            return (f"<td style='background:{fundo};border-radius:8px;text-align:center;padding:14px 18px'>"
                    f"<b style='font-size:1.1rem'>{v:,}".replace(",", ".") +
                    f"</b><div style='font-size:0.72rem;color:#475569'>{rotulo}</div></td>")
        e.markdown(f"""<div style='font-weight:700'>Matriz de confusão</div>
<table class='matriz' style='border-collapse:separate;border-spacing:6px;font-size:0.85rem;color:#334155'>
<tr><td></td><td style='text-align:center'>Previsto: não</td><td style='text-align:center'>Previsto: negativa</td></tr>
<tr><td>Real: não</td>{celula(mc['vn'], 'VN', '#eff6ff')}{celula(mc['fp'], 'FP', '#f1f5f9')}</tr>
<tr><td>Real: negativa</td>{celula(mc['fn'], 'FN', '#fff7ed')}{celula(mc['vp'], 'VP', '#dbeafe')}</tr>
</table>""", unsafe_allow_html=True)
        d.markdown(f"""<div style='font-weight:700'>Como foi avaliado</div>
<ul style='padding-left:18px;color:#334155;font-size:0.92rem'>
<li>Divisão treino/teste {m['divisao']} ({m['n_treino']:,} e {m['n_teste']:,} pedidos) e validação cruzada estratificada com {m['k_folds']} partes no treino.</li>
<li>Classes desbalanceadas ({pct(m['taxa_base'], 1)} de negativas): foco em recall, precisão, F1 e PR-AUC, não em acurácia.</li>
<li>Threshold de {pct(m['threshold'], 1)}, escolhido pelo {m['criterio_threshold']}. O modelo alerta {pct(rf['perc_alertas'], 1)} dos pedidos.</li>
<li>PR-AUC no teste: {str(round(rf['pr_auc'], 3)).replace('.', ',')} (baseline {str(round(lr['pr_auc'], 3)).replace('.', ',')}; um chute daria {str(round(m['taxa_base'], 3)).replace('.', ',')}).</li>
</ul>""".replace(f"{m['n_treino']:,}", f"{m['n_treino']:,}".replace(",", "."))
                   .replace(f"{m['n_teste']:,}", f"{m['n_teste']:,}".replace(",", ".")), unsafe_allow_html=True)

    st.write("")
    st.markdown(cartao("Limitações", """<ul style='margin:0;padding-left:18px;color:#334155'>
        <li>A nota depende de fatores que não estão nos dados, como defeito, item errado ou faltando e a expectativa do cliente. Quase todos os falsos negativos são pedidos entregues no prazo com esse tipo de problema.</li>
        <li>Boa parte do acerto vem de pedidos atrasados em que o cliente avaliou antes de receber (29% das notas negativas). Sem esse grupo, o desempenho cai bastante. Por isso o alerta é mais útil assim que o prazo estimado vence.</li>
        <li>Dados de 2016 a 2018. Em pedidos mais recentes, com menos atrasos, o desempenho cai: o modelo precisaria ser retreinado com frequência.</li>
        <li>Falsos positivos são pedidos com perfil de risco em que o cliente foi tolerante. O custo é um contato a mais.</li>
        </ul>"""), unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:0.85rem;color:#475569;margin-top:14px'>Projeto final de Aprendizagem de Máquina · "
                f"Equipe 4: Eduarda, Eduardo e Anna · <a href='{URL_REPOSITORIO}' target='_blank'>Repositório no GitHub</a>"
                f"</div>", unsafe_allow_html=True)


PAGINA_PREVER = st.Page(pagina_prever, title="Prever pedido", default=True)
PAGINA_SOBRE = st.Page(pagina_sobre, title="Sobre o modelo", url_path="sobre")
st.navigation([PAGINA_PREVER, PAGINA_SOBRE], position="top").run()

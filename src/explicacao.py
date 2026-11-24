"""Explicação local: "Por que esse valor?".

Método (simples e honesto, funciona com qualquer modelo):
1. calcula a probabilidade do pedido informado;
2. para cada campo do formulário, troca só aquele campo pelo valor de um
   "pedido típico" do treino (mediana para números, valor mais comum para categorias)
   e calcula a probabilidade de novo;
3. a diferença, em pontos percentuais (p.p.), é o quanto aquele campo soma (+)
   ou tira (-) da chance deste pedido em relação ao pedido típico.

Limitação: como o modelo não é linear, as contribuições não somam exatamente
a probabilidade final. Elas mostram o efeito de cada campo isoladamente.
"""
from src.config import FORMAS_PAGAMENTO, nome_categoria
from src.features import CAMPOS_FORMULARIO, entrada_para_features


def prever_probabilidade(modelo, entrada: dict, ref: dict) -> float:
    x = entrada_para_features(entrada, ref)
    return float(modelo.predict_proba(x)[0, 1])


def texto_frequencia(p: float) -> str:
    """Frase simples para o atendimento: "cerca de 6 em cada 10 pedidos como este"."""
    if p >= 0.2:
        return f"cerca de {round(p * 10)} em cada 10 pedidos como este"
    if p <= 0:
        return ""
    return f"cerca de 1 em cada {round(1 / p)} pedidos como este"


def _descrever_atraso(d: int) -> str:
    if d > 0:
        return f"{d} dia{'s' if d != 1 else ''} atrasado"
    if d < 0:
        return f"{-d} dia{'s' if d != -1 else ''} adiantado"
    return "no prazo"


def _rotulo(campo: str, entrada: dict, tipico: dict) -> str:
    v = entrada[campo]
    if campo == "dias_atraso":
        return f"Entrega {_descrever_atraso(int(v))} (típico: {_descrever_atraso(int(tipico[campo]))})"
    if campo == "qtd_itens":
        return f"{int(v)} ite{'ns' if int(v) != 1 else 'm'} no pedido"
    if campo == "categoria":
        return f"Categoria: {nome_categoria(v)}"
    if campo == "valor_produtos":
        return f"Valor dos produtos R$ {float(v):,.0f}".replace(",", ".")
    if campo == "valor_frete":
        perc = 100 * float(v) / float(entrada["valor_produtos"]) if float(entrada["valor_produtos"]) > 0 else 0
        return f"Frete R$ {float(v):,.0f} ({perc:.0f}% do valor)".replace(",", ".")
    if campo == "pagamento":
        return f"Pagamento: {FORMAS_PAGAMENTO.get(v, v)}"
    if campo == "uf_cliente":
        return f"Cliente em {v}"
    if campo == "uf_vendedor":
        outro = " (outro estado)" if v != entrada["uf_cliente"] else " (mesmo estado)"
        return f"Vendedor em {v}{outro}"
    return campo


def explicar(modelo, entrada: dict, ref: dict, top: int = 6, minimo_pp: float = 0.1):
    """Retorna (probabilidade, lista de fatores).

    Cada fator é um dicionário com 'rotulo' e 'pp' (pontos percentuais).
    """
    tipico = ref["pedido_tipico"]
    p = prever_probabilidade(modelo, entrada, ref)
    fatores = []
    for campo in CAMPOS_FORMULARIO:
        if entrada[campo] == tipico[campo]:
            continue
        alterada = dict(entrada)
        alterada[campo] = tipico[campo]
        p_ref = prever_probabilidade(modelo, alterada, ref)
        pp = 100 * (p - p_ref)
        if abs(pp) >= minimo_pp:
            fatores.append({"campo": campo, "rotulo": _rotulo(campo, entrada, tipico), "pp": pp})
    fatores.sort(key=lambda f: abs(f["pp"]), reverse=True)
    return p, fatores[:top]

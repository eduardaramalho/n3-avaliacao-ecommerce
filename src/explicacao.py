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


# Preposição usada com cada UF ("Cliente na BA", "Cliente no RJ", "Cliente em SP")
_PREP_UF = {
    "AC": "no", "AL": "em", "AM": "no", "AP": "no", "BA": "na", "CE": "no", "DF": "no",
    "ES": "no", "GO": "em", "MA": "no", "MG": "em", "MS": "em", "MT": "em", "PA": "no",
    "PB": "na", "PE": "em", "PI": "no", "PR": "no", "RJ": "no", "RN": "no", "RO": "em",
    "RR": "em", "RS": "no", "SC": "em", "SE": "em", "SP": "em", "TO": "em",
}
_PAGAMENTO_FRASE = {
    "credit_card": "Pagamento no cartão de crédito",
    "boleto": "Pagamento no boleto",
    "voucher": "Pagamento com voucher",
    "debit_card": "Pagamento no cartão de débito",
}


def _reais(v) -> str:
    return f"R$ {float(v):,.0f}".replace(",", ".")


def _rotulo(campo: str, entrada: dict) -> str:
    """Rótulo curto, que cabe em uma linha no app."""
    v = entrada[campo]
    if campo == "dias_atraso":
        d = int(v)
        if d > 0:
            return f"Atraso de {d} dia{'s' if d != 1 else ''}"
        if d < 0:
            return f"Entrega {-d} dia{'s' if d != -1 else ''} adiantada"
        return "Entrega no prazo, sem folga"
    if campo == "qtd_itens":
        return f"{int(v)} ite{'ns' if int(v) != 1 else 'm'} no pedido"
    if campo == "categoria":
        return nome_categoria(v)
    if campo == "valor_produtos":
        return f"Valor de {_reais(v)}"
    if campo == "valor_frete":
        return f"Frete de {_reais(v)}"
    if campo == "pagamento":
        return _PAGAMENTO_FRASE.get(v, f"Pagamento: {FORMAS_PAGAMENTO.get(v, v)}")
    if campo == "uf_cliente":
        return f"Cliente {_PREP_UF.get(v, 'em')} {v}"
    if campo == "uf_vendedor":
        if v != entrada["uf_cliente"]:
            return f"Vendedor de outro estado ({v})"
        return f"Vendedor no mesmo estado ({v})"
    return campo


def explicar(modelo, entrada: dict, ref: dict, top: int = 6, minimo_pp: float = 1.0):
    """Retorna (probabilidade, lista de fatores).

    Só entram fatores com efeito de pelo menos `minimo_pp` pontos percentuais:
    efeitos menores são ruído e confundem quem lê.

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
            fatores.append({"campo": campo, "rotulo": _rotulo(campo, entrada), "pp": pp})
    fatores.sort(key=lambda f: abs(f["pp"]), reverse=True)
    return p, fatores[:top]

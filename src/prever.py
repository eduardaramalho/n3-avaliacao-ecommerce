"""Previsão pela linha de comando (alternativa ao app, caso a interface falhe).

Exemplo:
    python -m src.prever --atraso 10 --frete 40 --valor 180 --itens 2 \
        --categoria moveis_decoracao --pagamento boleto --uf-vendedor SP --uf-cliente BA

Use --listar-categorias para ver os códigos aceitos.
"""
import argparse

import joblib

from src.config import ARQ_MODELO, FORMAS_PAGAMENTO, UFS, faixa_risco, nome_categoria
from src.explicacao import explicar, texto_frequencia
from src.features import carregar_referencia


def main(argv=None):
    ref = carregar_referencia()
    p = argparse.ArgumentParser(description="Risco de avaliação negativa (nota 1 ou 2) de um pedido Olist")
    p.add_argument("--atraso", type=int, default=0, help="dias em relação ao prazo (negativo = adiantado)")
    p.add_argument("--valor", type=float, default=100.0, help="valor dos produtos em R$")
    p.add_argument("--frete", type=float, default=20.0, help="frete em R$")
    p.add_argument("--itens", type=int, default=1, help="quantidade de itens")
    p.add_argument("--categoria", default=ref["pedido_tipico"]["categoria"])
    p.add_argument("--pagamento", default="credit_card", choices=list(FORMAS_PAGAMENTO))
    p.add_argument("--uf-vendedor", default="SP", choices=UFS)
    p.add_argument("--uf-cliente", default="SP", choices=UFS)
    p.add_argument("--listar-categorias", action="store_true")
    a = p.parse_args(argv)

    if a.listar_categorias:
        for c in ref["categorias"]:
            print(f"{c:<50} {nome_categoria(c)}")
        return

    entrada = {
        "categoria": a.categoria, "valor_produtos": a.valor, "valor_frete": a.frete,
        "qtd_itens": a.itens, "pagamento": a.pagamento, "uf_vendedor": a.uf_vendedor,
        "uf_cliente": a.uf_cliente, "dias_atraso": a.atraso,
    }
    modelo = joblib.load(ARQ_MODELO)
    prob, fatores = explicar(modelo, entrada, ref)
    nome, _, acao = faixa_risco(prob)

    print(f"\nChance de avaliação negativa: {100 * prob:.0f}%  ({nome})")
    print(texto_frequencia(prob).capitalize())
    print(f"Ação sugerida: {acao}\n")
    print("Principais fatores (comparados a um pedido típico):")
    for f in fatores:
        print(f"  {f['pp']:+6.1f} p.p.  {f['rotulo']}")
    print(f"\nChance média de um pedido qualquer: {100 * ref['taxa_base']:.1f}%")


if __name__ == "__main__":
    main()

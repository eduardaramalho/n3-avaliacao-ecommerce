<!-- Responsável: Eduardo -->
# Risco de avaliação negativa em pedidos de e-commerce (Olist)

Projeto final de Aprendizagem de Máquina (Engenharia de Software, Católica SC), Equipe 4. Treinamos um modelo de classificação que estima a chance de um pedido entregue receber nota 1 ou 2 do cliente. Assim, o time de atendimento sabe quais pedidos priorizar e pode entrar em contato antes de o cliente avaliar. O modelo usa dados públicos de cerca de 100 mil pedidos do marketplace Olist.

<!-- Responsável: Eduarda -->
## Página de teste

https://risco-avaliacao-olist.streamlit.app/

Informe os dados de um pedido (ou use um dos exemplos prontos) e veja a probabilidade de avaliação negativa, a faixa de risco, a ação sugerida para o atendimento e os fatores que mais pesaram.

<!-- Responsável: Eduardo -->
## Problema e público-alvo

<!-- Responsável: Eduardo -->
## Dataset

*Brazilian E-Commerce Public Dataset by Olist*, disponível no [Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). São cerca de 100 mil pedidos reais e anonimizados, feitos de 2016 a 2018, em 9 tabelas. Usamos 8 delas (pedidos, itens, pagamentos, avaliações, clientes, vendedores, produtos e tradução de categorias) e chegamos a 95.823 pedidos entregues e avaliados.

<!-- Responsável: Eduarda -->
## Como executar localmente

Requisitos: Python 3.11 ou superior.

```bash
git clone [LINK DO REPOSITÓRIO]
cd olist-avaliacao-negativa
pip install -r requirements.txt
```

Rodar o app (não precisa dos dados, usa o modelo salvo em `models/`):

```bash
streamlit run app/app.py
```

Previsão pela linha de comando (alternativa ao app):

```bash
python -m src.prever --atraso 15 --valor 180 --frete 45 --itens 1 --categoria moveis_decoracao --pagamento boleto --uf-vendedor SP --uf-cliente BA
```

Para refazer a análise e o treino: baixe os CSVs conforme [`data/LEIA-ME.md`](data/LEIA-ME.md), instale o Jupyter (`pip install jupyter`) e rode, em ordem, `notebooks/01_preparacao_eda.ipynb` e `notebooks/02_modelagem_avaliacao.ipynb`. O notebook 02 gera `models/modelo.joblib` e `models/metricas.json`.

| Pasta | Conteúdo |
|---|---|
| `notebooks/` | Preparação e EDA (01), modelagem e avaliação (02) |
| `src/` | Junção dos dados e cálculo das variáveis, usados igualmente nos notebooks, no app e no script |
| `app/` | App Streamlit |
| `models/` | Modelo treinado e métricas |
| `img/` | Gráficos usados neste README |
| `docs/`, `apresentacao/` | Guia da equipe e roteiro da apresentação |

<!-- Responsável: Eduarda -->
## Limitações

- Problemas de produto (defeito, item errado ou faltando) não aparecem nos dados. Por isso, quase todos os clientes insatisfeitos que o modelo deixa passar receberam o pedido no prazo.
- Boa parte do acerto vem de pedidos atrasados em que o cliente avaliou antes de receber (29% das notas negativas). Quando esse grupo fica de fora, a PR-AUC cai de 0,46 para 0,19. O alerta é mais útil assim que o prazo estimado vence.
- Os dados são de 2016 a 2018. Numa divisão temporal (treino com os pedidos mais antigos, teste com os mais recentes), a ROC-AUC cai de 0,76 para 0,68, porque o período recente tem menos atrasos. Em uso real, o modelo precisaria ser retreinado.
- O app estima duas variáveis que não estão no formulário: o tempo de entrega (prazo mediano da UF + atraso) e as parcelas (mediana da forma de pagamento).

<!-- Responsável: Eduardo -->
## Considerações finais

<!-- Responsável: Eduardo -->
## Referências

OLIST. **Brazilian E-Commerce Public Dataset by Olist**. Kaggle, 2018. Disponível em: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce. Acesso em: 24 nov. 2026.

SCIKIT-LEARN DEVELOPERS. **scikit-learn: machine learning in Python**: user guide. Disponível em: https://scikit-learn.org/stable/user_guide.html. Acesso em: 24 nov. 2026.



# Dados

Os CSVs não ficam no repositório (são grandes e têm licença própria). Para rodar os notebooks:

1. Acesse https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce (precisa de login no Kaggle).
2. Clique em **Download** e descompacte o `archive.zip` nesta pasta (`data/`).
3. Arquivos usados (o de geolocalização pode ficar de fora):
   - `olist_orders_dataset.csv`
   - `olist_order_items_dataset.csv`
   - `olist_order_payments_dataset.csv`
   - `olist_order_reviews_dataset.csv`
   - `olist_customers_dataset.csv`
   - `olist_sellers_dataset.csv`
   - `olist_products_dataset.csv`
   - `product_category_name_translation.csv`

O app **não** precisa dos CSVs: ele usa o modelo já treinado em `models/`.

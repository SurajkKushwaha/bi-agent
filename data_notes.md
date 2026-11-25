# Data notes

All data is in one DuckDB database. It covers an online store in Brazil, January to early September 2018.

## Tables

| Table | Source | What it holds | Columns |
|---|---|---|---|
| customers | SQL database | One row per customer | customer_id, customer_city, customer_state |
| products | SQL database | One row per product | product_id, product_category_name, product_weight_g |
| sellers | SQL database | One row per seller | seller_id, seller_city, seller_state |
| orders | SQL database | One row per order | order_id, customer_id, order_status, order_purchase_timestamp, order_approved_at, order_delivered_customer_date, order_estimated_delivery_date |
| order_items | SQL database | One row per product in an order | order_id, order_item_id, product_id, seller_id, price, freight_value |
| payments | SQL database | One row per payment of an order | order_id, payment_sequential, payment_type, payment_installments, payment_value |
| targets | Excel (finance) | Monthly revenue target per region and category | month, region, category, target_revenue |
| region_map | Excel (finance) | Which region each state belongs to | state, region, region_manager |
| promos | Google Sheet (marketing) | Marketing campaigns | campaign_id, campaign_name, start_date, end_date, channel, category, region, discount_pct, spend |
| reviews | CSV (support) | Customer reviews of orders | review_id, order_id, review_score, review_comment_message, review_creation_date |

## Column values

- `orders.order_status`: 'delivered', 'shipped' or 'canceled'.
- `products.product_category_name`: electronics, computers_accessories, housewares, health_beauty, sports_leisure, furniture_decor, toys, fashion_bags. Some are NULL.
- `customers.customer_state`, `sellers.seller_state`: Brazilian state codes (SP, RJ, BA, ...).
- `region_map.region`, `targets.region`: North, Northeast, Central-West, Southeast, South.
- `targets.month`: text in 'YYYY-MM' format, e.g. '2018-06'.
- `promos.region`: 'All' or one region name. `promos.category` matches product_category_name.
- `payments.payment_type`: credit_card, boleto, voucher, debit_card.
- `reviews.review_score`: 1 (worst) to 5 (best).

## How tables join

- orders.order_id = order_items.order_id = payments.order_id = reviews.order_id
- orders.customer_id = customers.customer_id
- order_items.product_id = products.product_id
- order_items.seller_id = sellers.seller_id
- customers.customer_state = region_map.state (gives the region)
- Sales vs target: month (strftime(order_purchase_timestamp, '%Y-%m')) + region + category (product_category_name) = targets.month + targets.region + targets.category
- Sales vs promos: product_category_name = promos.category, order date between start_date and end_date, and promos.region = region or 'All'

## Business definitions

- **Revenue** = SUM(order_items.price) for orders with order_status = 'delivered'. Freight is not included.
- **Order month** = the month of orders.order_purchase_timestamp.
- **Number of orders** = COUNT(DISTINCT order_id).
- **Average order value** = revenue / number of delivered orders.
- **Late delivery** = order_delivered_customer_date is more than 1 day after order_estimated_delivery_date (delivered orders only).
- **"Last month"** = the latest complete month in the data (August 2018), not today's date.

## Known data problems

- September 2018 has only 14 orders and none are delivered. The data stops there, so it is not a real drop.
- Many orders from the end of August are still 'shipped', so August revenue looks lower than it really is.
- Canceled and shipped orders have no delivery date.
- 4 products have no category (NULL). Show them as 'unknown'.
- 50 orders have two reviews. Count each order once when averaging scores per order.
- The target for June 2018, North, toys is missing.
- Campaign CMP06 appears twice in promos. Count it once.

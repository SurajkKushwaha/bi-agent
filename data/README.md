# BI Agent – Dummy Dataset

Practice data for the AI Business Intelligence Agent project. It imitates a Brazilian online store (January–September 2018) spread across **four sources**, like a real company. Column names follow the real Olist dataset, so you can switch to Olist later with very few changes.

All data is randomly generated: no real customers, sellers or campaigns.

## Folder contents

```
bi_agent_dummy_data/
├── sql_database/
│   ├── sales.db              ← SQLite database (the "company database")
│   └── csv/                  ← the same 6 tables as CSV, to load into SQL Server if you prefer
├── excel/
│   └── targets_2018.xlsx     ← finance team file: Monthly_Targets + Region_Map sheets
├── google_sheets/
│   └── promo_calendar.csv    ← marketing team file: import this into Google Sheets
├── csv/
│   └── order_reviews.csv     ← review export from the support tool
├── generate_data.py          ← recreates everything (fixed seed = same data every run)
├── README.md
└── ANSWER_KEY.md             ← what the agent should find (for trainers)
```

## Source 1 – SQL database (`sales.db`)

| Table | Rows | Columns |
|---|---|---|
| `customers` | 2,000 | customer_id, customer_city, customer_state |
| `products` | 120 | product_id, product_category_name, product_weight_g |
| `sellers` | 40 | seller_id, seller_city, seller_state |
| `orders` | 5,804 | order_id, customer_id, order_status, order_purchase_timestamp, order_approved_at, order_delivered_customer_date, order_estimated_delivery_date |
| `order_items` | 9,738 | order_id, order_item_id, product_id, seller_id, price, freight_value |
| `payments` | 5,939 | order_id, payment_sequential, payment_type, payment_installments, payment_value |

- `order_status` is `delivered`, `shipped` or `canceled`.
- Categories (English): electronics, computers_accessories, housewares, health_beauty, sports_leisure, furniture_decor, toys, fashion_bags.
- States are Brazilian state codes (SP, RJ, BA…). Use `Region_Map` in the Excel file to group them into regions.
- An order can have several items (`order_item_id` 1, 2, 3) and several payments (voucher + card).

**Want SQL Server instead?** Load the CSVs in `sql_database/csv/` with the Import Flat File wizard, or with pandas:
```python
df.to_sql("orders", engine, index=False, if_exists="replace")
```

## Source 2 – Excel (`targets_2018.xlsx`)

| Sheet | Rows | Columns |
|---|---|---|
| `Monthly_Targets` | 479 | month (YYYY-MM), region, category, target_revenue |
| `Region_Map` | 13 | state, region, region_manager |

Regions: North, Northeast, Central-West, Southeast, South.

## Source 3 – Google Sheets (`promo_calendar.csv`)

Import it: Google Sheets → File → Import → Upload → `promo_calendar.csv`. Name the sheet `promo_calendar`.
To read it from Python the simple way: File → Share → Publish to web → CSV, then `pd.read_csv(link)`.

| Columns |
|---|
| campaign_id, campaign_name, start_date, end_date, channel, category, region ("All" or a region name), discount_pct, spend |

## Source 4 – CSV (`order_reviews.csv`)

| Rows | Columns |
|---|---|
| 4,995 | review_id, order_id, review_score (1–5), review_comment_message, review_creation_date |

## How the sources join

| Key | Joins |
|---|---|
| `order_id` | orders ↔ order_items ↔ payments ↔ order_reviews |
| `customer_id` | orders ↔ customers |
| `product_id` | order_items ↔ products |
| `seller_id` | order_items ↔ sellers |
| `customer_state` = `Region_Map.state` | customers → region |
| month + region + category | sales ↔ Monthly_Targets |
| category + region + date range | sales ↔ promo_calendar |

## Business definitions (put these in your glossary)

- **Revenue** = sum of `order_items.price` for orders with `order_status = 'delivered'` (freight not included).
- **Order month** = month of `order_purchase_timestamp`.
- **Late delivery** = `order_delivered_customer_date` more than 1 day after `order_estimated_delivery_date`.
- **"Last month"** = the latest *complete* month in the data, not today's date.

## Known data issues (left in on purpose)

| Issue | Where | What the agent should do |
|---|---|---|
| September 2018 has only 14 orders, none delivered | orders | Say the month is incomplete; don't report a "collapse" |
| Late-August orders are still `shipped`, so August revenue looks low | orders | Mention that recent orders are not delivered yet |
| Canceled / shipped orders have no delivery date | orders | Use delivered orders for revenue and delivery metrics |
| 4 products have no category (25 order lines) | products | Report them as "unknown", not drop them silently |
| 50 orders have two reviews | order_reviews.csv | Deduplicate before averaging per order |
| One missing target row (June, North, toys) | Monthly_Targets | Say the target is missing |
| One start date written as `15/03/2018` | promo_calendar | Parse it carefully or flag it |
| Campaign CMP06 is listed twice | promo_calendar | Remove the duplicate before summing spend |

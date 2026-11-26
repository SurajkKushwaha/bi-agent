# loader.py - copy all 4 sources into one DuckDB file
# Run: python loader.py

import os
from dotenv import load_dotenv
load_dotenv()

import sqlite3
import duckdb
import pandas as pd


# ---- 1. Read the 4 sources ----

# Source 1: SQL database
sql_con = sqlite3.connect("data/sql_database/sales.db")
customers   = pd.read_sql("SELECT * FROM customers", sql_con)
products    = pd.read_sql("SELECT * FROM products", sql_con)
sellers     = pd.read_sql("SELECT * FROM sellers", sql_con)
orders      = pd.read_sql("SELECT * FROM orders", sql_con)
order_items = pd.read_sql("SELECT * FROM order_items", sql_con)
payments    = pd.read_sql("SELECT * FROM payments", sql_con)
sql_con.close()

# Source 2: Excel (two sheets)
targets    = pd.read_excel("data/excel/targets_2018.xlsx", sheet_name="Monthly_Targets")
region_map = pd.read_excel("data/excel/targets_2018.xlsx", sheet_name="Region_Map")

# Source 3: Google Sheet (local CSV copy for now)
# promos = pd.read_csv("data/google_sheets/promo_calendar.csv")
promos = pd.read_csv(os.getenv("PROMO_SHEET_URL"))

# Source 4: CSV
reviews = pd.read_csv("data/csv/order_reviews.csv")

# ---- 2. Fix text dates -> real dates ----
for col in ["order_purchase_timestamp", "order_approved_at",
            "order_delivered_customer_date", "order_estimated_delivery_date"]:
    orders[col] = pd.to_datetime(orders[col])

reviews["review_creation_date"] = pd.to_datetime(reviews["review_creation_date"])
promos["start_date"] = pd.to_datetime(promos["start_date"], format="mixed")  # one date is 15/03/2018
promos["end_date"]   = pd.to_datetime(promos["end_date"], format="mixed")

# ---- 3. Save everything into DuckDB ----
tables = {
    "customers": customers, "products": products, "sellers": sellers,
    "orders": orders, "order_items": order_items, "payments": payments,
    "targets": targets, "region_map": region_map,
    "promos": promos, "reviews": reviews,
}

con = duckdb.connect("data/warehouse.duckdb")
for name, df in tables.items():
    con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM df")
    print(f"{name:<12} {len(df):>6} rows")
con.close()

print("Done: data/warehouse.duckdb is ready")
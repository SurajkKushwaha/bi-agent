import os, sqlite3
import pandas as pd
import duckdb
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()
print("API key found:", bool(os.getenv("GROQ_API_KEY")))

con = sqlite3.connect("data/sql_database/sales.db")
print("Orders in DB:", pd.read_sql("SELECT COUNT(*) AS n FROM orders", con).n[0])

print("Target rows:", len(pd.read_excel("data/excel/targets_2018.xlsx", sheet_name="Monthly_Targets")))
print("Promos:", len(pd.read_csv("data/google_sheets/promo_calendar.csv")))
print("Reviews:", len(pd.read_csv("data/csv/order_reviews.csv")))

# need to understand this
print("DuckDB works:", duckdb.sql("SELECT 1 + 1").fetchall()[0][0] == 2)

llm = ChatGroq(model="openai/gpt-oss-120b")
print("LLM says:", llm.invoke("Reply with just: ready").content)
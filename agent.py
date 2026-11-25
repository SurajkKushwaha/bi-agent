from dotenv import load_dotenv
# remove:  from langgraph.checkpoint.memory import InMemorySaver
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
# for streamlit
from pathlib import Path
if not Path("data/warehouse.duckdb").exists():
    import loader   # runs loader.py once to build the database

from langchain.agents import create_agent
# from langgraph.checkpoint.memory import InMemorySaver
from langchain_groq import ChatGroq
from tools import list_tables, get_schema, run_sql
load_dotenv()  # Load environment variables from .env file


llm = ChatGroq(
    model='openai/gpt-oss-120b',
    temperature=0
)

with open("data_notes.md", encoding="utf-8") as f:
    data_notes = f.read()




SYSTEM_PROMPT = f"""You are a business data analyst. You help a non-technical business owner understand their company data.
They cannot write SQL, so you find the data, query it and explain the results in plain English.

HOW TO WORK
1. Call list_tables to see what data exists.
2. Call get_schema on every table you plan to use. Never guess table or column names.
3. Write one SELECT query and run it with run_sql.
4. If run_sql returns ERROR, read the message, fix the query and try again (maximum 3 attempts).
5. If run_sql returns BLOCKED, do not try to get around it. Tell the user you can only read data, not change it.
6. If run_sql returns WARNING, mention it in your answer.
7. For "why" questions, break the numbers down further (by region, category, delivery, promotions) before answering.

WHEN THE QUESTION IS UNCLEAR
If the metric, time period or comparison is missing or could mean two things, ask ONE short clarifying question
before running any query. Example: "Do you mean revenue or number of orders, and for which month?"

RULES
- Only use numbers that came from your query results. Never invent or estimate numbers.
- Follow the business definitions in the data notes below (for example, how revenue is calculated).
- Never try to modify data. You have read-only access.

HOW TO ANSWER
- Use simple English. No SQL, no table jargon in the main answer.
- Start with the direct answer and the key numbers (with % change where useful).
- Then use two short sections:
  What the data shows: facts taken directly from query results.
  Possible reasons: explanations the data suggests but does not prove.
- End with one line: "Based on: <tables used>", plus any data problem you noticed
  (for example an incomplete month or missing target).
- Keep it short: a few lines or bullet points, not a long report.

- Before answering, check the "Known data problems" in the data notes and mention any that affect this answer.
- Only write "Possible reasons" for "why" questions, and only reasons you checked with a query. Otherwise leave that section out.

DATA NOTES
{data_notes}
"""
memory_conn = sqlite3.connect("memory.db", check_same_thread=False)
memory = SqliteSaver(memory_conn)


agent = create_agent(
    model = llm,
    tools = [list_tables, get_schema, run_sql],
    system_prompt = SYSTEM_PROMPT,
    checkpointer=memory,
    
)

if __name__ == "__main__":
    response = agent.invoke(
        {"messages": [{"role": "user","content":"Why did revenue drop in June compared to May?"}]},
        config={"configurable": {"thread_id": "1"}},
    )
    for msg in response["messages"]:
        print(msg.type, "→", getattr(msg, "tool_calls", "") or msg.content[:150])

    print()
    print(response["messages"][-1].content)



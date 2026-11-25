from langchain.tools import tool
import duckdb


DB_PATH = "data/warehouse.duckdb"

@tool
def list_tables() ->str :
    """"
    List all the tables availiable in the company database
    
    Call this first to see what data exists before writing any SQL.

    """
    con = duckdb.connect(DB_PATH, read_only=True)
    tables = con.execute("SHOW TABLES").fetchall()
    con.close()

    names = [row[0] for row in tables]  
    return ', '.join(names)


# def get_schema(table_name:str)->str:
#     """
#     Show the columns and 3 sample rows of a table in the company database
#     """
#     connection = duckdb.connect(DB_PATH,read_only=True)
#     schema = f"Schema for table {table_name}:\n"
#     describe = connection.execute(f"DESCRIBE {table_name}").fetchall()   
#     rows = connection.execute(f"SELECT * FROM {table_name} LIMIT 3").fetchall()
#     connection.close()

#     print('schema:', schema)
#     print('describe:', describe)
#     print('rows:', rows)

@tool
def get_schema(table_name: str) -> str:
    """Show the columns and 3 sample rows of one table.
    Call this before writing SQL on a table, to see exact column names and value formats."""
    connection = duckdb.connect(DB_PATH, read_only=True)
    try:
        columns = connection.execute(f"DESCRIBE {table_name}").df()
        rows = connection.execute(f"SELECT * FROM {table_name} LIMIT 3").df()
    except Exception:
        return f"Table '{table_name}' not found. Use list_tables to see available tables."
    finally:
        connection.close()

    columns_text = columns[["column_name", "column_type"]].to_string(index=False)
    rows_text = rows.to_string(index=False)
    # print(f"Table: {table_name}\n\nColumns:\n{columns_text}\n\nSample rows:\n{rows_text}")
    return f"Table: {table_name}\n\nColumns:\n{columns_text}\n\nSample rows:\n{rows_text}"

@tool
def run_sql(query: str) -> str:
    """Run a read-only SQL SELECT query on the company database (DuckDB) and return the result.
    Only SELECT or WITH queries are allowed. Use exact table and column names from get_schema."""
    cleaned_query = query.strip().rstrip(";").strip()
    upper_query = cleaned_query.upper()

    # Safety check 1: must be a SELECT (or WITH ... SELECT)
    if not (upper_query.startswith("SELECT") or upper_query.startswith("WITH")):
        return "BLOCKED: only SELECT queries are allowed."

    # Safety check 2: one statement only, no dangerous keywords
    if ";" in cleaned_query:
        return "BLOCKED: only one query at a time is allowed."
    not_allowed = ["INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER", "ATTACH", "COPY"]
    for word in not_allowed:
        if word in upper_query.split():
            return f"BLOCKED: {word} is not allowed. Only SELECT queries are permitted."

    # Add a LIMIT so huge results never reach the LLM
    if "LIMIT" not in upper_query:
        cleaned_query += " LIMIT 200"

    connection = duckdb.connect(DB_PATH, read_only=True)
    try:
        result = connection.execute(cleaned_query).df()
    except Exception as e:
        return f"ERROR: {e}"
    finally:
        connection.close()

    if result.empty:
        return "WARNING: the query returned no rows."
    return result.to_string(index=False)

# def run_sql(query:str)->str:
    """
    Run a SQL query on the company database and return the results as a string.
    """

    try:
        connection = duckdb.connect(DB_PATH, read_only=True)
        cleaned_query= query.strip()
        
        if ';' in cleaned_query:
            cleaned_query = cleaned_query.strip(';')
        
        if "LIMIT" not in cleaned_query:
            cleaned_query += " LIMIT 200"
        
        not_allowed = ["INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER"]
        
        for word in not_allowed:
            if word in cleaned_query.upper():
                return f"Error: {word} statements are not allowed. Only SELECT queries are permitted."

        execute_cleaned_query = connection.execute(cleaned_query).df()

        if execute_cleaned_query.empty:
            return "Query executed successfully, but returned no results."

        return execute_cleaned_query.to_string(index=False)        
    except Exception as e:
        return f"Error connecting to the database: {str(e)}"
    finally:
        connection.close()        
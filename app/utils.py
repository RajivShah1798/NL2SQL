from sentence_transformers import SentenceTransformer, util
import sqlite3
import os

DB_PATH = os.path.join(os.getcwd(), "metadata_store.db")


def run_sql_query(db_path, sql):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        conn.close()
        return result
    except Exception as e:
        raise RuntimeError(f"Error executing SQL on {db_path}:\n{sql}\n{e}")

def init_metadata_db():
    if os.path.exists("metadata_store.db"):
        return
    conn = sqlite3.connect("metadata_store.db")
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS metadata")
    cursor.execute("""
        CREATE TABLE metadata (
            db_id TEXT,
            table_name TEXT,
            column_name TEXT,
            data_type TEXT,
            table_intent TEXT,
            column_intent TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_metadata(metadata_list, db_path="metadata_store.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    for entry in metadata_list:
        cursor.execute("""
            INSERT INTO metadata (db_id, table_name, column_name, data_type, table_intent, column_intent)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            entry["db_id"],
            entry["table_name"],
            entry["column_name"],
            entry["data_type"],
            entry.get("table_intent"),
            entry.get("column_intent")
        ))
    conn.commit()
    conn.close()
    
def get_db_list(metadata_db="metadata_store.db"):
    conn = sqlite3.connect(metadata_db)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT db_id FROM metadata")
    dbs = [row[0] for row in cursor.fetchall()]
    conn.close()
    return dbs

model = SentenceTransformer("all-MiniLM-L6-v2")

def get_top_tables_by_semantic_similarity(question, top_k=4, metadata_db="metadata_store.db"):
    query_embedding = model.encode(question, convert_to_tensor=True)

    conn = sqlite3.connect(metadata_db)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("📋 Available tables in DB:", tables)
    
    
    cursor.execute("SELECT DISTINCT db_id, table_name, table_intent FROM metadata")
    table_data = cursor.fetchall()
    conn.close()

    scored_tables = []
    for db_id, table_name, table_intent in table_data:
        if not table_intent:
            continue
        table_embedding = model.encode(table_intent, convert_to_tensor=True)
        score = util.pytorch_cos_sim(query_embedding, table_embedding).item()
        scored_tables.append((score, db_id, table_name))

    scored_tables.sort(reverse=True)
    return [(db_id, table_name) for score, db_id, table_name in scored_tables[:top_k]]

def get_column_info_by_tables(db_id, table_names, metadata_db="metadata_store.db"):
    conn = sqlite3.connect(metadata_db)
    cursor = conn.cursor()

    table_map = {}
    for table in table_names:
        cursor.execute("""
            SELECT column_name, data_type, column_intent
            FROM metadata
            WHERE db_id = ? AND table_name = ?
        """, (db_id, table))
        table_map[table] = cursor.fetchall()

    conn.close()
    return table_map

def build_semantic_info_dict(question, top_k=4, metadata_db="metadata_store.db"):
    top_tables = get_top_tables_by_semantic_similarity(question, top_k, metadata_db)
    if not top_tables:
        return "", []

    db_id = top_tables[0][0]
    table_names = [table for _, table in top_tables]

    column_data = get_column_info_by_tables(db_id, table_names, metadata_db)

    conn = sqlite3.connect(metadata_db)
    cursor = conn.cursor()

    db_schema = []
    for table in table_names:
        columns_raw = column_data[table]  
        columns = []
        column_intents = {}

        for col_name, col_type, col_intent in columns_raw:
            columns.append(f"{col_name} ({col_type})")
            column_intents[col_name.lower()] = col_intent

        cursor.execute("""
            SELECT DISTINCT table_intent
            FROM metadata
            WHERE db_id = ? AND table_name = ?
        """, (db_id, table))
        table_intent_row = cursor.fetchone()
        table_intent = table_intent_row[0] if table_intent_row else ""

        db_schema.append({
            "table_name": table,
            "table_intent": table_intent,
            "columns": columns,
            "column_intents": column_intents
        })

    conn.close()
    return db_id, db_schema

def build_prompt(question, db, db_schema, include_sql=True):
    lines = []
    lines.append(f"### Database: {db}")
    lines.append("")


    for table in db_schema:
        lines.append(f"### Table Schema: {table['table_name']} - {table['table_intent']}")
        for col in table["columns"]:
            col_name, col_type = col.split(" (", 1)
            col_type = col_type.rstrip(")")
            col_intent = table["column_intents"].get(col_name.lower(), "")
            lines.append(f"- {col_name} ({col_type}): {col_intent}")
        lines.append("")

    lines.append(f"### Question: {question}")
    if include_sql:
        lines.append("### SQL:")

    return "\n".join(lines)


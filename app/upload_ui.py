import streamlit as st
import os
from collections import defaultdict

from ddl_parser import extract_schema_metadata
from utils import init_metadata_db, insert_metadata
from intent_infer import call_generate_intents_api

def upload_schema_page(model_serving_url: str):
    st.title("📄 Upload DDL + SQLite DB")
    init_metadata_db()

    if "uploads" not in st.session_state:
        st.session_state.uploads = []

    uploaded_ddls = st.file_uploader("Upload DDL Files (.sql)", type=["sql"], accept_multiple_files=True)
    uploaded_dbs = st.file_uploader("Upload SQLite DBs (.db)", type=["db"], accept_multiple_files=True)

    if uploaded_ddls and uploaded_dbs:
        os.makedirs("uploaded_dbs", exist_ok=True)
        for ddl_file, db_file in zip(uploaded_ddls, uploaded_dbs):
            ddl_contents = ddl_file.read().decode("utf-8")
            db_path = os.path.join("uploaded_dbs", db_file.name)

            with open(db_path, "wb") as f:
                f.write(db_file.read())
            st.session_state.uploads = []
            st.session_state.uploads.append({
                "ddl_name": ddl_file.name,
                "db_name": db_file.name,
                "ddl_contents": ddl_contents,
                "db_path": db_path
            })

        st.success("✅ Files uploaded. You can now infer intents.")

    if st.button("🧠 Run Intent Inference"):
        all_metadata = []

        for entry in st.session_state.uploads:
            st.write(f"📂 Processing: {entry['ddl_name']} + {entry['db_name']}")
            parsed_metadata = extract_schema_metadata(entry["ddl_contents"])
            if not parsed_metadata:
                st.warning(f"⚠️ No tables found in {entry['ddl_name']}")
                continue

            parsed_metadata_with_intent = []
            with st.spinner("Inferring intents..."):
                for table_name, columns, data_types in parsed_metadata:
                    response = call_generate_intents_api(model_serving_url, table_name, columns, data_types)
                    table_intent = response.get('table_intent')
                    column_intents = response.get('column_intents')

                    for col, dtype in zip(columns, data_types):
                        parsed_metadata_with_intent.append({
                            "db_id": entry["db_name"],
                            "table_name": table_name,
                            "column_name": col,
                            "data_type": dtype,
                            "table_intent": table_intent,
                            "column_intent": column_intents.get(col, "")
                        })

            insert_metadata(parsed_metadata_with_intent)
            all_metadata.extend(parsed_metadata_with_intent)

        st.subheader("📊 Extracted Metadata + Intents")
        grouped = defaultdict(list)
        for entry in all_metadata:
            grouped[entry["table_name"]].append(entry)

        for table_name, entries in grouped.items():
            with st.expander(f"🗂️ Table: {table_name} — {entries[0]['table_intent']}"):
                st.dataframe([
                    {
                        "Column": row["column_name"],
                        "Type": row["data_type"],
                        "Intent": row["column_intent"]
                    }
                    for row in entries
                ], use_container_width=True)

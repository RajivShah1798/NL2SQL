import streamlit as st
from utils import get_db_list, run_sql_query, build_semantic_info_dict, build_prompt
import requests


def call_generate_query_api(api_url, prompt):
    endpoint = f"{api_url}/generate_query"
    headers = {"Content-Type": "application/json"}
    payload = {
        "prompt": prompt
    }

    response = requests.post(endpoint, json=payload, headers=headers)
    print("Response:\n", response)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API Error {response.status_code}: {response.text}")

def query_interface_page(model_serving_url: str):
    st.title("💬 Natural Language to SQL Chat")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    dbs = get_db_list()
    db_id = st.selectbox("Choose a database", dbs)

    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area("Ask a question about your database:", key="chat_input")
        submitted = st.form_submit_button("Generate SQL")

    if submitted and user_input:
        db_id, db_schema = build_semantic_info_dict(user_input)
        prompt = build_prompt(user_input, db_id, db_schema)
        print("Generated Prompt: ", prompt)
        sql_result = call_generate_query_api(model_serving_url, prompt)['sql_query']

        db_path = f"./uploaded_dbs/{db_id}"
        try:
            result = run_sql_query(db_path, sql_result)
        except Exception as e:
            result = f"❌ Error executing SQL: {e}"

        st.session_state.chat_history.append({
            "question": user_input,
            "sql": sql_result,
            "result": result
        })

    st.subheader("🧠 Conversation History")
    for i, entry in enumerate(reversed(st.session_state.chat_history)):
        with st.expander(f"Q{i+1}: {entry['question']}"):
            st.markdown(f"**Generated SQL:**")
            st.code(entry["sql"])
            st.markdown(f"**Result:**")
            st.write(entry["result"])

    if st.button("🧹 Clear Conversation"):
        st.session_state.chat_history = []

import streamlit as st
from upload_ui import upload_schema_page
from query_ui import query_interface_page
from dotenv import load_dotenv
import os

st.set_page_config(page_title="NL2SQL Assistant", layout="wide")

load_dotenv()
model_server_url = os.getenv("MODEL_SERVER_URL")


if "active_page" not in st.session_state:
    st.session_state.active_page = "home"


st.sidebar.title("🔄 Navigation")
if st.sidebar.button("🏠 Home"):
    st.session_state.active_page = "home"
if st.sidebar.button("📤 Upload Schema"):
    st.session_state.active_page = "upload"
if st.sidebar.button("🔎 Query Interface"):
    st.session_state.active_page = "query"
if st.sidebar.button("🧹 Start New Session"):
    st.session_state.clear()
    st.session_state.active_page = "home"


if st.session_state.active_page == "home":
    st.title("🧠 Welcome to NL2SQL Assistant")
    st.markdown("""
    This assistant allows you to:
    - Upload DDL and SQLite files to extract metadata and infer intents
    - Ask natural language questions and receive SQL queries + results
    - Keep your data and interactions consistent within a session

    Use the sidebar to get started!
    """)

elif st.session_state.active_page == "upload":
    upload_schema_page(model_server_url)

elif st.session_state.active_page == "query":
    query_interface_page(model_server_url)

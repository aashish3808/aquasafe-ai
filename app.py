import streamlit as st
import pandas as pd
import os
import traceback
from sqlalchemy import create_engine, text
from google import genai
from google.cloud import storage
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
API_KEY = os.getenv("GEMINI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")

# Initialize Clients
genai_client = None
storage_client = None
engine = None

try:
    if API_KEY:
        genai_client = genai.Client(api_key=API_KEY)
    
    storage_client = storage.Client()
    
    if not DATABASE_URL:
        st.error("DATABASE_URL is not set in environment variables.")
    else:
        # pool_pre_ping=True handles stale connections
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
except Exception as e:
    st.error(f"Initialization Error: {traceback.format_exc()}")

def get_sql_from_natural_language(user_query: str) -> str:
    schema_context = "Table: water_tests (ph_level, hardness, solids_tds, chloramines, sulfate, organic_carbon, turbidity, is_potable). Rules: Return ONLY raw SQL, no markdown formatting."
    prompt = f"{schema_context}\n\nUser Question: {user_query}\nSQL Query:"
    
    response = genai_client.models.generate_content(
        model="gemini-2.0-flash", 
        contents=prompt
    )
    return response.text.replace("```sql", "").replace("```", "").strip()

def execute_query(sql_query: str):
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(sql_query), conn)
            return df, None
    except Exception as e:
        return None, str(e)

st.set_page_config(page_title="AquaSafe AI", page_icon="💧", layout="wide")
st.title("💧 AquaSafe AI")
st.subheader("Query public water safety records using plain English.")

user_question = st.text_input("Ask about water quality (e.g., 'What is the average ph level?'):")

if st.button("Analyze Data"):
    if user_question and genai_client and engine:
        with st.spinner("Analyzing..."):
            sql = get_sql_from_natural_language(user_question)
            st.info(f"Generated SQL: `{sql}`")
            results, error = execute_query(sql)
            
            if error:
                st.error(f"Execution Error: {error}")
            else:
                st.success("Query successful!")
                st.dataframe(results, use_container_width=True)
    else:
        st.warning("Ensure all configurations (API Key, DB Connection) are active.")

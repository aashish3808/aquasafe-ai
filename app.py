import streamlit as st
import psycopg2
import pandas as pd
import os
import vertexai
from vertexai.generative_models import GenerativeModel
from dotenv import load_dotenv

# Load environment variables from the .env file (for local runs)
load_dotenv()

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "your-gcp-project-id")
LOCATION = "us-central1"

vertexai.init(project=PROJECT_ID, location=LOCATION)

# Using gemini-3-flash-preview for next-generation speed and budget-friendly reasoning
model = GenerativeModel("gemini-3-flash-preview")

DB_HOST = os.environ.get("ALLOYDB_IP", "127.0.0.1")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASS = os.environ.get("DB_PASS", "your_password")
DB_NAME = os.environ.get("DB_NAME", "postgres")

def get_sql_from_natural_language(user_query: str) -> str:
    schema_context = """
    You are an expert PostgreSQL database engineer. 
    Translate the user's natural language question into a valid PostgreSQL query.
    
    Schema:
    CREATE TABLE water_tests (
        sample_id SERIAL PRIMARY KEY, ph_level FLOAT, hardness FLOAT,
        solids_tds FLOAT, chloramines FLOAT, sulfate FLOAT,
        organic_carbon FLOAT, turbidity FLOAT, is_potable BOOLEAN 
    );
    
    Rules:
    1. Return ONLY the raw SQL code.
    2. Do not include markdown formatting like ```sql.
    3. Only query the `water_tests` table.
    """
    prompt = f"{schema_context}\n\nUser Question: {user_query}\nSQL Query:"
    response = model.generate_content(prompt)
    return response.text.replace("```sql", "").replace("```", "").strip()

def execute_query(sql_query: str):
    try:
        conn = psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, dbname=DB_NAME)
        df = pd.read_sql_query(sql_query, conn)
        conn.close()
        return df, None
    except psycopg2.Error as e:
        return None, str(e)

st.set_page_config(page_title="AquaSafe AI", page_icon="💧", layout="wide")
st.title("💧 AquaSafe AI")
st.subheader("Query public water safety records using plain English.")

user_question = st.text_input("Ask a question about the water tests data:", placeholder="e.g., Show me 10 samples with the lowest hardness.")

if st.button("Analyze Data"):
    if user_question:
        with st.spinner("Translating English to SQL..."):
            generated_sql = get_sql_from_natural_language(user_question)
            
        st.info(f"**Generated SQL Query:**\n```sql\n{generated_sql}\n```")
        
        with st.spinner("Executing against AlloyDB..."):
            results_df, error = execute_query(generated_sql)
            
        if error:
            st.error(f"Database Execution Error: The AI generated invalid SQL.\n\nDetails: {error}")
        elif results_df is not None and not results_df.empty:
            st.success("Query executed successfully!")
            st.dataframe(results_df, use_container_width=True)
        else:
            st.warning("Query executed successfully, but returned 0 results.")

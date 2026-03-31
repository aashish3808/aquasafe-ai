import pandas as pd
from sqlalchemy import create_engine
import os
import traceback
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
CSV_FILE_PATH = "water_potability.csv"

def setup_database():
    print(f"Connecting to AlloyDB via SQLAlchemy...")
    try:
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL is not set in environment variables.")
        
        # Initialize Engine with pool_pre_ping to check connection health
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        
        print(f"Reading {CSV_FILE_PATH}...")
        df = pd.read_csv(CSV_FILE_PATH)
        
        # Load into AlloyDB using SQLAlchemy's to_sql
        print("Uploading data to water_tests table...")
        df.to_sql('water_tests', engine, if_exists='replace', index=False)
        
        print("Data loaded successfully!")
    except Exception as e:
        print(f"Initialization Error: {traceback.format_exc()}")
    finally:
        if 'engine' in locals():
            engine.dispose()

if __name__ == "__main__":
    setup_database()

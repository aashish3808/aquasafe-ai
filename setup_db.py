import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables from the .env file (for local runs)
load_dotenv()

DB_HOST = os.environ.get("ALLOYDB_IP", "127.0.0.1")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASS = os.environ.get("DB_PASS", "your_password")
DB_NAME = os.environ.get("DB_NAME", "postgres")
CSV_FILE_PATH = "water_potability.csv" 

def setup_database():
    print(f"Connecting to private AlloyDB instance at {DB_HOST}...")
    try:
        conn = psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, dbname=DB_NAME)
        cur = conn.cursor()
        
        print("Creating table if it doesn't exist...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS water_tests (
                sample_id SERIAL PRIMARY KEY,
                ph_level FLOAT, hardness FLOAT, solids_tds FLOAT,
                chloramines FLOAT, sulfate FLOAT, organic_carbon FLOAT,
                turbidity FLOAT, is_potable BOOLEAN 
            );
        """)
        
        print(f"Loading data from {CSV_FILE_PATH}...")
        with open(CSV_FILE_PATH, 'r') as f:
            next(f) # Skip header
            copy_sql = """
                COPY water_tests (ph_level, hardness, solids_tds, chloramines, 
                                  sulfate, organic_carbon, turbidity, is_potable) 
                FROM STDIN WITH CSV
            """
            cur.copy_expert(copy_sql, f)

        conn.commit()
        print("Data loaded successfully!")

    except Exception as e:
        print(f"Database Error: {e}")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    setup_database()

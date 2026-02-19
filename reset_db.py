import psycopg2
from etl.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

def reset_db():
    print("Connecting to database...")
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
        cur = conn.cursor()
        
        print("Truncating tables: job_embeddings, jobs...")
        # Truncate tables cleanly
        cur.execute("TRUNCATE TABLE job_embeddings, jobs RESTART IDENTITY CASCADE;")
        
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Database reset successfully.")
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")

if __name__ == "__main__":
    reset_db()

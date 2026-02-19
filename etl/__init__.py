"""
ETL Config — โหลด .env และจัดการ connection กับ DB + Ollama
"""
import os
from dotenv import load_dotenv

# โหลด .env จาก root ของโปรเจกต์
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# Database
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'jobmatcher')
DB_USER = os.getenv('DB_USER', 'jobmatcher')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'jobmatcher_secret')

DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Ollama
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'nomic-embed-text')

# Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_FULL_DATA = os.path.join(PROJECT_ROOT, 'jobsdb_full_data.csv')

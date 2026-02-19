import pytest
import pandas as pd
from unittest.mock import patch, MagicMock, call
# ปรับ import ตามโครงสร้างโปรเจกต์ของคุณ
from etl.load_to_db import upsert_job, upsert_embedding, run_pipeline

# ==========================================
# Fixtures: เตรียมตัวแสดงแทน (Mocks)
# ==========================================

@pytest.fixture
def mock_cursor():
    """จำลอง Database Cursor"""
    cursor = MagicMock()
    # สมมติว่าเวลา insert เสร็จแล้ว database คืนค่า id = 1 กลับมา
    cursor.fetchone.return_value = [1] 
    return cursor

@pytest.fixture
def mock_db_connection(mock_cursor):
    """จำลอง Database Connection"""
    conn = MagicMock()
    conn.cursor.return_value = mock_cursor
    return conn

@pytest.fixture
def sample_job_data():
    """ข้อมูลจำลองสำหรับทดสอบ Upsert"""
    return {
        'title': 'Data Engineer',
        'company': 'Tech Corp',
        'location': 'Bangkok',
        'salary': '50k',
        'link': 'http://test.com/job1',
        'description': 'Python SQL needed',
        'skills': ['Python', 'SQL'],
        'experience_years': '3 years',
        'job_type': 'Full-time'
    }

# ==========================================
# Unit Tests: ทดสอบฟังก์ชันย่อย (DB Operations)
# ==========================================

def test_upsert_job(mock_cursor, sample_job_data):
    """ทดสอบว่าสร้าง SQL Query สำหรับ upsert_job ถูกต้องไหม"""
    
    # Action
    job_id = upsert_job(mock_cursor, sample_job_data)

    # Assert
    assert job_id == 1
    # เช็คว่ามีการเรียก execute (ยิง SQL)
    mock_cursor.execute.assert_called_once()
    
    # เช็คว่า SQL args มีข้อมูลครบถ้วน
    args = mock_cursor.execute.call_args[0]
    sql_query = args[0]
    sql_params = args[1]
    
    assert "INSERT INTO jobs" in sql_query
    assert sample_job_data['title'] in sql_params
    assert sample_job_data['link'] in sql_params
    # เช็คว่า skills ถูกแปลงเป็น json string แล้ว
    assert '["Python", "SQL"]' in sql_params or "['Python', 'SQL']" in str(sql_params)

def test_upsert_embedding(mock_cursor):
    """ทดสอบการบันทึก Embedding"""
    # Action
    upsert_embedding(mock_cursor, job_id=1, embedding=[0.1, 0.2], model='nomic-test')

    # Assert
    mock_cursor.execute.assert_called_once()
    sql_params = mock_cursor.execute.call_args[0][1]
    assert sql_params[0] == 1 # job_id
    assert str([0.1, 0.2]) == sql_params[1] # embedding string

# ==========================================
# Integration Tests: ทดสอบ Pipeline หลัก (Mocked)
# ==========================================

@patch('etl.load_to_db.psycopg2.connect') # 1. Mock DB Connect
@patch('etl.load_to_db.pd.read_csv')      # 2. Mock การอ่าน CSV
@patch('etl.load_to_db.extract_skills')   # 3. Mock Ollama Extraction
@patch('etl.load_to_db.embed_text')       # 4. Mock Embedding
def test_run_pipeline_full_flow(mock_embed, mock_extract, mock_read_csv, mock_connect, mock_db_connection):
    """ทดสอบ Flow หลัก: อ่าน CSV -> Extract -> Embed -> Save"""
    
    # --- Setup ---
    # 1. เชื่อมต่อ DB ปลอม
    mock_connect.return_value = mock_db_connection
    
    # 2. จำลองข้อมูลใน CSV (สร้าง DataFrame ปลอมๆ)
    mock_df = pd.DataFrame([
        {
            'Title': 'Job A', 
            'Company': 'Comp A', 
            'Link': 'http://test.com/a', 
            'JobDescription': 'JD Content A',
            'Location': 'BKK',
            'Salary': 'N/A'
        }
    ])
    mock_read_csv.return_value = mock_df

    # 3. จำลองผลลัพธ์จาก AI
    mock_extract.return_value = {'required_skills': ['Python'], 'experience_years': '1y'}
    mock_embed.return_value = [0.1, 0.2, 0.3]

    # 4. จำลองว่า DB ว่างเปล่า (ไม่มีงานซ้ำ)
    # fetchall ถูกเรียก 2 ครั้ง (เช็ค skills, เช็ค embeddings) -> ให้คืนค่าว่างทั้งคู่
    mock_db_connection.cursor.return_value.fetchall.side_effect = [[], []]

    # --- Action ---
    run_pipeline(csv_path="dummy.csv")

    # --- Assert ---
    # 1. ต้องมีการอ่าน CSV
    mock_read_csv.assert_called_once()
    
    # 2. ต้องมีการเรียก AI ทั้ง 2 ตัว
    mock_extract.assert_called_with('JD Content A')
    mock_embed.assert_called_with('JD Content A')
    
    # 3. ต้องมีการเรียก execute SQL อย่างน้อย 2 ครั้ง (Insert Job, Insert Embed)
    # (เราเช็คแบบคร่าวๆ ว่ามีการ commit ข้อมูล)
    mock_db_connection.commit.assert_called()

@patch('etl.load_to_db.psycopg2.connect')
@patch('etl.load_to_db.pd.read_csv')
@patch('etl.load_to_db.extract_skills')
@patch('etl.load_to_db.embed_text')
def test_run_pipeline_skip_existing(mock_embed, mock_extract, mock_read_csv, mock_connect, mock_db_connection):
    """ทดสอบ Logic การข้าม (Skip): ถ้างายมีใน DB แล้ว ต้องไม่เรียก AI ซ้ำ"""
    
    # --- Setup ---
    mock_connect.return_value = mock_db_connection
    
    # สร้าง DF ปลอม 1 งาน
    target_link = 'http://test.com/existing'
    mock_df = pd.DataFrame([{
        'Title': 'Job B', 'Link': target_link, 'JobDescription': 'JD B'
    }])
    mock_read_csv.return_value = mock_df

    # จำลองว่า DB มีงานนี้อยู่แล้ว! (คืนค่า Link กลับมา)
    # fetchall ครั้งแรก (check skills) -> เจอ
    # fetchall ครั้งสอง (check embed) -> เจอ
    mock_db_connection.cursor.return_value.fetchall.side_effect = [[(target_link,)], [(target_link,)]]

    # --- Action ---
    run_pipeline("dummy.csv")

    # --- Assert ---
    # AI ต้อง **ไม่ถูกเรียก** (เพราะมีข้อมูลแล้ว)
    mock_extract.assert_not_called()
    mock_embed.assert_not_called()
    
    # แต่ยังต้องมีการ Commit (เพื่อ update timestamp หรือ logic อื่นๆ ถ้ามี)
    mock_db_connection.commit.assert_called()
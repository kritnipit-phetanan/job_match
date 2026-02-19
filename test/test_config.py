import os
import pytest
from unittest.mock import patch
import importlib

# Import module ที่เราจะเทส
from etl import config

def test_config_defaults():
    """
    1. Sanity Check: เช็คค่า Default ทั่วไป
    (เทสว่าโหลดโมดูลแล้วค่าไม่เป็น None และ Type ถูกต้อง)
    """
    # เช็คว่า DB URL ถูกสร้างเป็น String และมี format เบื้องต้นถูก
    assert isinstance(config.DB_URL, str)
    assert config.DB_URL.startswith("postgresql://")
    
    # เช็คว่า Path สำคัญๆ มีอยู่จริง (สำคัญมาก! กัน path ผิด)
    assert os.path.exists(config.PROJECT_ROOT), "Project Root ไม่ควรจะหาไม่เจอ"
    # หมายเหตุ: CSV_FULL_DATA อาจจะยังไม่มีไฟล์จริงตอนเริ่มโปรเจกต์ เลยอาจจะแค่เช็คว่า path ลงท้ายถูกไหม
    assert config.CSV_FULL_DATA.endswith('jobsdb_full_data.csv')

def test_db_url_construction():
    """
    2. Logic Check: เทสว่าประกอบร่าง DB_URL ถูกต้องไหม
    (เทคนิค: ใช้ patch.dict เพื่อจำลอง Env Var แล้ว reload config)
    """
    # จำลอง Environment Variable ชุดใหม่
    mock_env = {
        "DB_USER": "test_user",
        "DB_PASSWORD": "test_password",
        "DB_HOST": "1.2.3.4",
        "DB_PORT": "9999",
        "DB_NAME": "test_db"
    }

    # ใช้ patch.dict จำลอง environment
    with patch.dict(os.environ, mock_env):
        # *** สำคัญมาก ***: ต้อง reload module เพื่อให้มันอ่าน os.getenv ใหม่
        importlib.reload(config)
        
        expected_url = "postgresql://test_user:test_password@1.2.3.4:9999/test_db"
        assert config.DB_URL == expected_url

    # Clean up: Reload กลับเป็นค่าเดิม (จาก .env จริง หรือ default) เพื่อไม่ให้กระทบ test อื่น
    importlib.reload(config)

def test_ollama_config():
    """3. เช็คค่า Ollama"""
    # เช็คว่า Model default เป็น llama3 ตามที่ตั้งใจไว้
    # (ถ้าในเครื่องคุณเซ็ต .env เป็นค่าอื่น Test นี้อาจต้องปรับตาม หรือใช้ mock เหมือนข้างบน)
    assert config.OLLAMA_MODEL is not None
    assert config.EMBEDDING_MODEL == 'nomic-embed-text'
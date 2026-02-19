import pytest
from unittest.mock import patch, MagicMock
# สมมติว่าไฟล์โค้ดของคุณอยู่ที่ etl/extract_skills.py
from etl.extract_skills import extract_skills, _parse_json_response

# ==========================================
# Part 1: Test Logic การแกะ JSON (_parse_json_response)
# ส่วนนี้สำคัญมาก เพราะ AI ชอบตอบกลับมาหลายรูปแบบ
# ==========================================

def test_parse_json_clean():
    """1. กรณี AI ตอบ JSON มาเป๊ะๆ"""
    input_text = '{"required_skills": ["Python"], "job_type": "Full-time"}'
    result = _parse_json_response(input_text)
    assert result["required_skills"] == ["Python"]

def test_parse_json_with_markdown():
    """2. กรณี AI ตอบมาพร้อม Markdown Code Block (เจอบ่อยสุด)"""
    input_text = """
    Here is the result:
    ```json
    {
        "required_skills": ["SQL", "AWS"],
        "experience_years": "3 years"
    }
    ```
    Hope this helps!
    """
    result = _parse_json_response(input_text)
    assert result["required_skills"] == ["SQL", "AWS"]

def test_parse_json_dirty_text():
    """3. กรณี AI ตอบ JSON มาในข้อความดื้อๆ ไม่มี Code Block"""
    input_text = """
    Sure, based on the JD, the skills are:
    {
        "required_skills": ["Java"],
        "job_type": "Contract"
    }
    """
    result = _parse_json_response(input_text)
    assert result["required_skills"] == ["Java"]

def test_parse_json_failure():
    """4. กรณี AI มั่ว ตอบอะไรมาไม่รู้ที่แกะไม่ได้เลย"""
    input_text = "Sorry, I cannot extract skills from this text."
    result = _parse_json_response(input_text)
    # ต้องได้ค่า Default กลับมา
    assert result["required_skills"] == []
    assert result["experience_years"] == "Not specified"


# ==========================================
# Part 2: Test ฟังก์ชันหลัก (extract_skills)
# ใช้ Mock เพื่อไม่ต้องเรียก Ollama จริงๆ
# ==========================================

@patch('etl.extract_skills.ollama_client')
def test_extract_skills_success(mock_ollama):
    """ทดสอบกรณีทำงานสำเร็จ (Happy Path)"""
    # Setup: จำลองการตอบกลับของ Ollama
    mock_response = {
        'message': {
            'content': '{"required_skills": ["Python", "Docker"], "job_type": "Full-time"}'
        }
    }
    mock_ollama.chat.return_value = mock_response

    # Action
    jd_text = "We are looking for a Python Developer with Docker skills."
    result = extract_skills(jd_text)

    # Assert
    assert result["required_skills"] == ["Python", "Docker"]
    assert result["job_type"] == "Full-time"
    
    # เช็คว่าเราส่ง System Prompt ไปถูกต้องไหม
    args, kwargs = mock_ollama.chat.call_args
    assert kwargs['model'] is not None # ต้องมีการส่ง model
    assert kwargs['options']['temperature'] == 0.1 # ต้องมีการคุม temperature

def test_extract_skills_invalid_input():
    """ทดสอบกรณี Input ใช้ไม่ได้ (ไม่ต้อง Mock เพราะฟังก์ชันตัดจบก่อน)"""
    assert extract_skills("")["required_skills"] == []
    assert extract_skills("Not Found")["required_skills"] == []
    assert extract_skills(None)["required_skills"] == []

@patch('etl.extract_skills.ollama_client')
def test_extract_skills_api_error(mock_ollama):
    """ทดสอบกรณี Ollama Error (เช่น Server ล่ม)"""
    # Setup: สั่งให้ระเบิด
    mock_ollama.chat.side_effect = Exception("Ollama is down!")

    # Action
    result = extract_skills("Some valid JD")

    # Assert: ต้องไม่ Crash และคืนค่า Default
    assert result["required_skills"] == []
    assert result["experience_years"] == "Not specified"
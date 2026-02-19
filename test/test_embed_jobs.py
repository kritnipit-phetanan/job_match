import pytest
from unittest.mock import patch, MagicMock
# สมมติว่าไฟล์ script ของคุณชื่อ embed_jobs.py และอยู่ในโฟลเดอร์ etl
from etl.embed_jobs import embed_text, embed_batch 

# --- Test Case 1: ทดสอบว่า embed_text ทำงานถูกต้องเมื่อ Ollama ตอบกลับมาปกติ ---
@patch('etl.embed_jobs.ollama_client') # Mock ตัว library ollama ในไฟล์ embed_jobs
def test_embed_text_success(mock_ollama):
    # Setup: จำลองสิ่งที่ Ollama จะตอบกลับมา
    mock_response = {'embeddings': [[0.1, 0.2, 0.3]]}
    mock_ollama.embed.return_value = mock_response

    # Action: เรียกใช้ฟังก์ชันจริง
    text = "Python Developer required"
    result = embed_text(text)

    # Assert: ตรวจสอบผลลัพธ์
    assert result == [0.1, 0.2, 0.3] # ค่าต้องตรงกับที่ Mock
    assert len(result) == 3
    
    # ตรวจสอบว่าฟังก์ชันมีการเรียก ollama.embed จริงหรือไม่
    mock_ollama.embed.assert_called_once() 

# --- Test Case 2: ทดสอบ Input ที่ไม่ควร Embed (Empty/Error strings) ---
def test_embed_text_invalid_input():
    assert embed_text("") is None
    assert embed_text("Not Found") is None
    assert embed_text(None) is None

# --- Test Case 3: ทดสอบกรณี Ollama Error (เช่น Server ล่ม) ---
@patch('etl.embed_jobs.ollama_client')
def test_embed_text_api_error(mock_ollama):
    # Setup: จำลองว่า Ollama โยน Exception ออกมา
    mock_ollama.embed.side_effect = Exception("Ollama connection failed")

    # Action
    result = embed_text("Some text")

    # Assert: ฟังก์ชันควร Handle error แล้ว return None (ตาม logic code คุณ)
    assert result is None

# --- Test Case 4: ทดสอบ embed_batch (หลายข้อความ) ---
@patch('etl.embed_jobs.ollama_client')
def test_embed_batch(mock_ollama):
    # Setup: จำลองตอบกลับ 2 ครั้ง
    mock_ollama.embed.side_effect = [
        {'embeddings': [[1.0, 0.0]]}, # ตอบครั้งที่ 1
        {'embeddings': [[0.0, 1.0]]}  # ตอบครั้งที่ 2
    ]

    texts = ["Job A", "Job B"]
    results = embed_batch(texts)

    assert len(results) == 2
    assert results[0] == [1.0, 0.0]
    assert results[1] == [0.0, 1.0]
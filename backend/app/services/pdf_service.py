import pymupdf4llm
import tempfile
import os
import re

def clean_pii(text: str) -> str:
    """
    ลบข้อมูลส่วนตัว (PII) เบื้องต้นออกจาก Text เพื่อความปลอดภัย
    ก่อนส่งไปให้ AI หรือเก็บลง Database
    """
    # 1. ลบ Email (แทนที่ด้วย [EMAIL])
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    text = re.sub(email_pattern, "[EMAIL]", text)

    # 2. ลบเบอร์โทรศัพท์ (แบบง่าย) (แทนที่ด้วย [PHONE])
    # หาตัวเลขที่เกาะกลุ่มกัน 9-10 ตัว หรือมีขีดคั่น
    phone_pattern = r'\(?(\+66|0)\)?[- ]?\d{1,2}[- ]?\d{3}[- ]?\d{3,4}'
    text = re.sub(phone_pattern, "[PHONE]", text)

    return text

def parse_pdf_to_markdown(file_bytes: bytes, filename: str) -> str:
    """
    รับไฟล์ PDF (binary) -> Save ลง Temp -> ใช้ pymupdf4llm อ่าน -> คืนค่า Markdown
    """
    # 1. สร้างไฟล์ชั่วคราว (Temp File) เพราะ pymupdf4llm ต้องการ path ของไฟล์
    # delete=False เพื่อให้เราปิดไฟล์แล้วเปิดอ่านใหม่ได้ (Windows/Linux compatible)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(file_bytes)
        tmp_path = tmp_file.name

    try:
        # 2. แปลง PDF เป็น Markdown (พระเอกของเรา) 🦸‍♂️
        md_text = pymupdf4llm.to_markdown(tmp_path)
        
        # 3. ลบข้อมูลส่วนตัว (Optional)
        cleaned_text = clean_pii(md_text)
        
        return cleaned_text

    finally:
        # 4. ลบไฟล์ชั่วคราวทิ้งเสมอ (Clean up) เพื่อไม่ให้รกเครื่อง
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
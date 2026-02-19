from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.pdf_service import parse_pdf_to_markdown

router = APIRouter(
    prefix="/resume",
    tags=["Resume Parser"]
)

@router.post("/parse")
async def parse_resume(file: UploadFile = File(...)):
    """
    รับไฟล์ PDF Resume และแปลงเป็น Markdown Text
    """
    # 1. เช็คว่าเป็นไฟล์ PDF ไหม
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # 2. อ่านไฟล์เป็น Bytes
    file_bytes = await file.read()

    # 3. เรียกใช้ Service (สมอง) ที่เราเขียนไว้
    try:
        markdown_text = parse_pdf_to_markdown(file_bytes, file.filename)
        
        return {
            "filename": file.filename,
            "parsed_content": markdown_text,
            "message": "Resume parsed successfully! ✅"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing PDF: {str(e)}")
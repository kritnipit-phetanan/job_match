import re
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends
from app.services.pdf_service import parse_pdf_to_markdown
from app.services.rag_service import embed_text, search_matching_jobs
from app.core.database import get_db_connection
from app.services.llm_service import generate_tailored_cover_letter, analyze_batch_resume
from app.schemas.job import CoverLetterRequest, SkillGapRequest

router = APIRouter(
    prefix="/resume",
    tags=["Resume Engine"]
)

@router.post("/analyze")
async def analyze_resume(
    file: UploadFile = File(...),
    limit: int = Query(5, description="จำนวนงานที่ต้องการให้แสดง"),
    location: str = Query(None, description="กรองตามสถานที่ (เช่น Bangkok)"),
    job_type: str = Query(None, description="กรองตามประเภทงาน (เช่น Full-time)"),
    db_conn = Depends(get_db_connection)  # <-- ยืม Connection DB มาใช้
):
    """
    รับไฟล์ PDF Resume -> แปลงเป็น Text -> แปลงเป็น Vector -> ค้นหางานที่ Match สุดใน Database
    """
    # 1. เช็คว่าเป็นไฟล์ PDF ไหม
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="รองรับเฉพาะไฟล์ PDF เท่านั้นครับ")

    try:
        # ---------------------------------------------------------
        # STEP 1: อ่านและทำความสะอาด Resume (PDF -> Markdown)
        # ---------------------------------------------------------
        file_bytes = await file.read()
        markdown_text = parse_pdf_to_markdown(file_bytes, file.filename)
        
        # ถ้าไฟล์ว่างเปล่า (อ่าน text ไม่ออก)
        if not markdown_text or len(markdown_text.strip()) < 50:
            raise ValueError("อ่านเนื้อหาจาก PDF ไม่ได้ หรือเนื้อหาสั้นเกินไป")

        # ---------------------------------------------------------
        # STEP 2: สมอง AI แปลงข้อความเป็น Vector (Markdown -> Vector)
        # ---------------------------------------------------------
        resume_vector = embed_text(markdown_text)

        # ---------------------------------------------------------
        # STEP 3: ค้นหาใน Database (Vector -> Matched Jobs)
        # ---------------------------------------------------------
        pool_jobs = search_matching_jobs(
            conn=db_conn,
            resume_vector=resume_vector,
            pool_size=20,
            location_filter=location,
            job_type_filter=job_type
        )

        # ---------------------------------------------------------
        # STEP 4: ส่งให้ Gemini วิเคราะห์รวดเดียว (Experience + Skill Gap ของทั้ง 20 งาน)
        # ---------------------------------------------------------
        ai_analysis = analyze_batch_resume(markdown_text, pool_jobs)
        candidate_exp = ai_analysis.get("years_of_experience", 0)
        skill_gaps = ai_analysis.get("skill_gaps", {})

        print(f"🧠 AI วิเคราะห์ประสบการณ์ได้: {candidate_exp} ปี")

        # ---------------------------------------------------------
        # STEP 5: หักคะแนน (Penalty) และแนบ Skill Gap เข้าไปในการ์ดงานแต่ละอัน
        # ---------------------------------------------------------
        final_results = []
        for job in pool_jobs:
            # หักคะแนนประสบการณ์
            exp_str = str(job['experience_years'])
            match = re.search(r'(\d+)', exp_str)
            job_min_exp = int(match.group(1)) if match else 0
            
            penalty = 0
            if candidate_exp < job_min_exp:
                penalty = (job_min_exp - candidate_exp) * 10
            
            job['match_score'] = max(0.0, float(job['match_score']) - penalty)
            
            # ยัด Skill gap ที่ได้จาก AI ใส่เข้าไปใน Object งานเลย
            str_job_id = str(job['id'])
            job['matched_skills'] = skill_gaps.get(str_job_id, {}).get('matched', [])
            job['missing_skills'] = skill_gaps.get(str_job_id, {}).get('missing', [])
            
            final_results.append(job)

        # ---------------------------------------------------------
        # STEP 6: จัดเรียงคะแนนใหม่จากมากไปน้อย และตัดเอาแค่ limit (5 งาน)
        # ---------------------------------------------------------
        final_results = sorted(final_results, key=lambda x: x['match_score'], reverse=True)
        top_jobs = final_results[:limit]

        return {
            "status": "success",
            "filename": file.filename,
            "candidate_experience": candidate_exp,
            "jobs": top_jobs,
            "resume_markdown": markdown_text
        }

    except Exception as e:
        print(f"🔥 Error ใน /analyze: {e}")
        raise HTTPException(status_code=500, detail="ระบบเกิดข้อผิดพลาด")

@router.post("/generate-cover-letter")
async def generate_cover_letter(request: CoverLetterRequest):
    """
    รับ Resume Text และ Job Description เพื่อสร้าง Cover Letter ที่ตรงกับตำแหน่งงานด้วย AI
    """
    try:
        # 1. โยนข้อมูลให้ Gemini ทำงาน
        letter_content = generate_tailored_cover_letter(
            resume_text=request.resume_markdown,
            job_desc=request.job_description
        )
        
        return {
            "status": "success",
            "cover_letter": letter_content
        }

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"🔥 Error ใน /generate-cover-letter: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการสร้าง Cover Letter")

# @router.post("/skill-gap")
# async def get_skill_gap(request: SkillGapRequest):
#     """
#     วิเคราะห์ Skill ที่ตรงกัน และ Skill ที่ยังขาด
#     """
#     try:
#         result = analyze_skill_gap(
#             resume_text=request.resume_markdown, 
#             job_skills=request.job_skills
#         )
#         return {"status": "success", "data": result}
#     except ValueError as ve:
#         raise HTTPException(status_code=400, detail=str(ve))
#     except Exception as e:
#         print(f"🔥 Error ใน /skill-gap: {e}")
#         raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการวิเคราะห์ Skill Gap")
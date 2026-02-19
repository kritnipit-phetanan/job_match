# 📅 Project Roadmap & Implementation Plan

This project is divided into four main phases, following the standard Data Engineering lifecycle: Ingestion → Processing → Storage → Serving.

## Phase 1: Data Acquisition (Ingestion) ✅
**Goal:** Build a robust scraper for recruitment platforms (JobsDB).
- [x] Initialize Python environment and Playwright setup.
- [x] Develop scraping logic for JobsDB search results (e.g., keywords: "Data Engineer", "Python").
- [x] Handle pagination to scrape multiple pages of results.
- [x] Implement robust error handling and retry mechanisms.
- [x] **Stealth Mode:** Bypass anti-scraping measures (User-Agent rotation, random delays) using `playwright-stealth`.
- [x] Output raw job data to CSV (`jobsdb_result_all.csv` — 160 งาน, `jobsdb_full_data.csv` — พร้อม JD).

**Bonus (ทำเพิ่มเกินแผน):**
- [x] 🍪 Login session cookies (Google login via real Chrome) — `scrape_jobsdb.py --login`
- [x] 🔄 UA rotation pool (Chrome 143/144/145 พร้อม Build จริง) + SEC-CH-UA Client Hints headers
- [x] 📄 Deep scraping Job Descriptions (`scrape_jobsdb_details.py`) — ดึง JD ครบ 160/160
- [x] 🔁 Incremental scraping — ข้ามงานซ้ำ, append เฉพาะงานใหม่
- [x] 🛡️ Anti-detection: mouse/scroll simulation, long breaks ทุก 25 งาน, variable delays 5-15 วิ

## Phase 2: Data Engineering & Storage (ETL Pipeline) ✅
**Goal:** Clean data, extract skills using AI, and store embeddings.
- [x] Setup **PostgreSQL** locally via Docker with **pgvector** (`docker-compose.yml` + Adminer UI).
- [x] **Security:** Setup `.env` file for managing API keys and DB credentials.
- [x] Design relational schema (`jobs`, `job_embeddings`) with vector index (`db/init.sql`).
- [x] Integrate **Ollama (Llama3.2)** for Data Cleaning & Extraction:
    - *Prompt Engineering:* Created `etl/extract_skills.py` — extracts skills, experience years, and job type from JDs.
    - *Robust JSON parsing:* Handles markdown wrappers, dirty text, and JS-style `// comments`.
- [x] Implement **Text Embedding** for Job Descriptions — `nomic-embed-text` (768 dims) via `etl/embed_jobs.py`.
- [x] Write the load script to upsert processed jobs into PostgreSQL — `etl/load_to_db.py` (idempotent, skip-on-existing).
- [x] ✅ **Pipeline ทำงานสำเร็จ 160/160 งาน, 0 errors**

## Phase 2.5: Quality Assurance & Testing ✅
**Goal:** Ensure the pipeline is resilient to website structure changes.
- [x] **Unit Testing:**
    - [x] Write tests for the JD parser (`test/test_extract_skills.py`)
    - [x] Mock external API calls to test pipeline logic (`test/test_load_to_db.py`, `test/test_embed_jobs.py`, `test/test_config.py`)
- [x] **Scraping Health Checks:**
    - [x] Implement a check to verify if JobsDB HTML selectors have changed (`test/health_check.py`)

## Phase 3: Backend & RAG Logic (The Brain)

**Goal:** Develop the Resume Analysis API with Hybrid Search capabilities.

### Step 1: Project Setup
- [ ] Initialize **FastAPI** project structure (folders: `routers`, `schemas`, `services`).
- [ ] Configure `settings.py` using `pydantic-settings` to load variables from `.env`.

### Step 2: Resume Parser Service
- [ ] Install `pymupdf4llm` (recommended for high-accuracy local parsing).
- [ ] Implement function to convert **PDF Resume** -> **Markdown Text**.
- [ ] *(Bonus)* Implement text cleaning to remove **PII** (Personally Identifiable Information) like phone numbers/emails before embedding.

### Step 3: Core Logic `POST /analyze-resume`
- [ ] **Embed:** Convert "Resume Markdown" to Vector (using `nomic-embed-text`).
- [ ] **Hybrid Search:** Query `pgvector` with SQL logic:
    - *Query Logic:* `SELECT * FROM jobs ORDER BY embedding <=> resume_vec LIMIT 10`
    - *Filter:* Allow user to filter by `job_type` or `location` via API parameters.
- [ ] **Ranking:** Calculate simple "Match Score" formula: `(1 - cosine_distance) * 100`.

### Step 4: Generative AI `POST /generate-cover-letter`
- [ ] Integrate **Gemini API** (using `google-generativeai` SDK).
- [ ] Design System Prompt that accepts `{resume_markdown}` and `{job_description}`.
- [ ] Implement **Streaming Response** (optional but highly recommended for UX) to show the letter being typed out in real-time.

## Phase 4: Frontend & Deployment (The Interface)
**Goal:** Create a user-friendly web application.
- [ ] Initialize **Next.js** project with Tailwind CSS and **Shadcn UI**.
- [ ] Build **Job Dashboard**: List jobs with "Match %" badges.
- [ ] Build **Resume Upload**: Drag-and-drop interface for PDF.
- [ ] Build **Analysis View**: Show "Skills You Have" vs. "Skills You Lack".
- [ ] **Deployment:**
    - Frontend: Vercel.
    - Backend/DB: Supabase (DB) + Render/Railway (API).
- [ ] **Automation:** Configure GitHub Actions to run the Job Scraper daily.

## 🔮 Future Improvements
- [ ] **Salary Trends:** Visualize average salaries for specific tech stacks.
- [ ] **Course Recommendation:** Suggest courses (Udemy/Coursera) for missing skills.
- [ ] **Email Alerts:** Notify users when a >90% match job is found.
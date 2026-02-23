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

## Phase 3: Backend & RAG Logic (The Brain) ✅

**Goal:** Develop the Resume Analysis API with Hybrid Search capabilities.

### Step 1: Project Setup
- [x] Initialize **FastAPI** project structure (folders: `routers`, `schemas`, `services`).
- [x] Configure `settings.py` using `pydantic-settings` to load variables from `.env`.

### Step 2: Resume Parser Service
- [x] Install `pymupdf4llm` (recommended for high-accuracy local parsing).
- [x] Implement function to convert **PDF Resume** -> **Markdown Text**.
- [x] *(Bonus)* Implement text cleaning to remove **PII** (Personally Identifiable Information) like phone numbers/emails before embedding.

### Step 3: Core Logic `POST /analyze/resume`
- [x] **Embed:** Convert "Resume Markdown" to Vector (using `nomic-embed-text`).
- [x] **Hybrid Search:** Query `pgvector` with SQL logic:
    - *Query Logic:* `SELECT * FROM jobs ORDER BY embedding <=> resume_vec LIMIT 10`
    - *Filter:* Allow user to filter by `job_type` or `location` via API parameters.
- [x] **Ranking:** Calculate simple "Match Score" formula: `(1 - cosine_distance) * 100`.

### Step 4: Generative AI `POST /generate-cover-letter`
- [x] Integrate **Gemini API** (using `google.genai` SDK).
- [x] Design System Prompt that accepts `{resume_markdown}` and `{job_description}`.
- [x] Implement **Streaming Response** (optional but highly recommended for UX) to show the letter being typed out in real-time.

## Phase 4: Frontend & Deployment (The Interface)
**Goal:** Create a user-friendly web application.
### Step 1: Frontend Initialization
- [x] Initialize **Next.js 15** (App Router) + React 19 project.
- [x] Configure **Tailwind CSS v4** (Zero-runtime, lightning-fast styling).
- [x] Integrate **Shadcn UI** for enterprise-grade, accessible components.

### Step 2: Core UI Components
- [x] Build **Resume Upload Zone**: Interactive drag-and-drop interface accepting PDF files.
- [x] Build **Job Dashboard**: Data table/cards listing scraped jobs with "**Match Score %**" progress rings.

### Step 3: AI Analysis Views
- [x] Build **Skill Gap Analysis**: Visual comparison of "Skills You Have" vs. "Skills You Lack" based on RAG output.
- [x] **Build Cover Letter Generator**: Real-time UI with a Streaming text effect to show Gemini AI typing the letter dynamically.

### Step 4: Cloud Deployment (Production)
- [x] **Database**: Migrate local PostgreSQL to Supabase (Free tier with native pgvector support).
- [x] **Backend API**: Deploy FastAPI Docker container to Render or Railway (Easy auto-deploy from GitHub).
- [x] **Frontend**: Deploy Next.js app to Vercel for optimal Server-Side Rendering (SSR) and edge caching.

### Step 5: CI/CD & Automation
- [ ] Configure **GitHub Actions** cron job to run the Python scraper pipeline (etl/) automatically every night and upsert fresh data to Supabase.

## 🔮 Future Improvements
- [x] **Salary Trends:** Visualize average salaries for specific tech stacks.
- [ ] **Course Recommendation:** Suggest courses (Udemy/Coursera) for missing skills.
- [ ] **Social Media Alerts:** Notify users when a >90% match job is found.
- [ ] **AI Mock Interviewer 🎙️:** Generate personalized interview questions based on the candidate's *Missing Skills* and the specific Job Description, allowing users to practice and receive AI feedback.
- [ ] **Resume Roasting / Optimization 🔥:** An AI-powered critique mode that provides brutally honest (or highly professional) feedback to improve resume bullet points and action verbs.
- [ ] **Career Path Evolution Roadmap 🗺️:** A visual progression tree showing the stepping stones from the user's current role to their dream role, predicting the next skills to acquire.
- [x] **Market Demand Heatmap 📊:** Real-time analytics highlighting trending "Hot Skills" across all scraped jobs to help users prioritize their learning focus.
- [ ] **Tailored Portfolio Generator 💼:** Automatically generate a structured portfolio or GitHub README template that highlights the exact projects/skills a specific role demands.
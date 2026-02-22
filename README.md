# JobMatcher 🎯
**AI-Powered Resume to Job Matching & Analytics Platform**

JobMatcher is a full-stack automated pipeline that scrapes real job listings, analyzes them using AI (Groq + Gemini), and provides a smart frontend interface for users to upload their resumes. The system calculates a match score, identifies skill gaps, analyzes market demand/salary trends, and even generates personalized cover letters.

![JobMatcher Overview](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green)
![Next.js](https://img.shields.io/badge/Next.js-15-black)
![Supabase](https://img.shields.io/badge/Supabase-pgvector-emerald)

## 🌟 Key Features

### 1. 🤖 AI Matchmaker (RAG)
- **Semantic Search:** Uses `pgvector` and Gemini Embeddings to find jobs that semantically match your resume, rather than just exact keyword matching.
- **Skill Gap Analysis:** Highlights exactly which required skills from the job description are missing from your resume.
- **Cover Letter Generator:** Automatically drafts a tailored cover letter based on your resume and the specific job requirements using LLMs.

### 2. 📊 Market Analytics Dashboard
- **Market Demand Heatmap:** Visualizes which tech skills are currently most requested in the market.
- **Salary Trends:** Analyzes and plots average salary ranges mapped against specific tools and technologies.
- **Data Freshness:** Powered by an automated nightly scraping pipeline (via GitHub Actions) ensuring data is always up-to-date.

### 3. 🕸️ Automated Cloud Scraping Pipeline
- Scrapes job data using Playwright with advanced Anti-Detection techniques (stealth mode, human-like scrolling, UA rotation).
- Cloud-ready scripts designed to run on GitHub Actions.
- Robust ETL pipeline that extracts structured data (skills, experience) using Groq API and generates embeddings via Google Gemini.

---

## 🏗️ Architecture

The project follows a modern Data Engineering + Full-Stack architecture:

```mermaid
graph TD
    subgraph Data Pipeline
        S[Playwright Scraper] -->|Raw Data| DB[(Supabase PostgreSQL)]
        DB -->|ETL: Groq+Gemini| DB
    end
    subgraph Backend API
        FA[FastAPI Server] ---|pgvector queries| DB
        FA --- LLM[Gemini API]
    end
    subgraph Frontend Client
        UI[Next.js App Router] --- FA
    end
```

### Tech Stack
- **Database:** Supabase (PostgreSQL + pgvector)
- **Backend:** Python, FastAPI, Uvicorn, SQLAlchemy, Tenacity
- **Frontend:** Next.js 15 (React), TailwindCSS, Recharts, Lucide Icons
- **AI/LLMs:** Google Gemini (Embeddings & Generation), Groq (Fast JSON Extraction)
- **Automation:** GitHub Actions, Playwright

---

## 🚀 Getting Started (Local Development)

### Prerequisites
- Python 3.11+
- Node.js 18+ (with `pnpm`)
- PostgreSQL (or Supabase account)

### 1. Database Setup
You can use a local Docker Postgres or a Supabase project.

1. Execute the schema from `db/init.sql` to create tables, indexes, and pgvector extension.
2. Copy `.env.example` to `.env` and fill in your credentials:
   ```env
   DATABASE_URL=postgresql://user:pass@host:5432/dbname
   GEMINI_API_KEY=your_key
   GROQ_API_KEY=your_key
   ```

### 2. Backend (FastAPI)
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start the server (runs on http://localhost:8000)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend (Next.js)
```bash
cd frontend
pnpm install

# Create .env.local
echo 'NEXT_PUBLIC_API_URL=http://localhost:8000' > .env.local

# Start dev server (runs on http://localhost:3000)
pnpm dev
```

### 4. Running the Scraper / ETL Pipeline
```bash
# Phase 1: Scrape Job Listings
python cloud_scrape_jobs.py

# Phase 2: Scrape Job Descriptions
python cloud_scrape_details.py

# Phase 3: Run ETL (Extract Skills -> Embed -> Upsert Db)
python -m etl.load_to_db
```

---

## ☁️ Cloud Deployment

- **Database:** Supabase Cloud (Free Tier)
- **Backend:** `render.yaml` provided for easy deployment to Render.
- **Frontend:** Optimized for Vercel deployment.
- **Automation:** `.github/workflows/scrape.yml` configured for nightly unattended runs.

---
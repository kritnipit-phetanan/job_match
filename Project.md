# JobMatcher: AI-Powered Career Intelligence Platform

## 📖 Executive Summary
JobMatcher is an end-to-end Data Engineering and AI project designed to bridge the gap between job seekers and their ideal roles. The platform automates the extraction of job listings from recruitment sites (e.g., JobsDB), utilizes Local LLMs to structure unstructured Job Descriptions (JDs), and provides a RAG-based system to analyze a user's resume against market demands, offering personalized skill gap analysis and cover letter generation.

## 🚀 Problem Statement
Job hunting is often inefficient. Candidates struggle to find roles that genuinely match their skill sets amidst thousands of listings. Furthermore, manually tailoring resumes and cover letters for every application is time-consuming, and identifying specific "missing skills" (Gap Analysis) for a desired role is difficult without objective data.

## 💡 Solution
An automated system that:
1.  **Scrapes** daily job postings from platforms like JobsDB/Blognone.
2.  **Parses & Structures** raw JDs into structured data (Skills, Experience, Salary) using Local LLMs.
3.  **Analyzes** the user's uploaded Resume (PDF) against the job database.
4.  **Serves** insights via an AI Chatbot that calculates a "Match Score," identifies missing skills, and generates tailored cover letters.

## 🏗 System Architecture (Hybrid Model)
To optimize costs while maintaining performance, the system uses a hybrid architecture:

* **Offline / Batch Processing (The Market Data Pipeline):**
    * Executes daily via **GitHub Actions**.
    * **Playwright** scrapes job listings (Title, Company, JD, Location) from target sites.
    * **Ollama (Local LLM)** acts as an Information Extractor, converting raw HTML JDs into JSON (extracting Tech Stack, Hard Skills, Soft Skills).
    * **PostgreSQL + pgvector** stores the structured jobs and their vector embeddings.

* **Online / Real-time Serving (The Candidate App):**
    * **Next.js** provides the frontend for users to upload resumes and view job matches.
    * **FastAPI** handles PDF parsing and vector similarity search (Resume Vector vs. Job Vectors).
    * **Gemini API (Free Tier) / Groq Cloud API** generates the final analysis (e.g., "You are a 85% match, but you need to learn Airflow") and writes cover letters.

## ✨ Key Features
* **Automated Job Aggregator:** Daily scraping of niche tech roles (Data Engineer, AI Engineer).
* **Resume Parser:** Extracts skills and experience from user-uploaded PDFs.
* **Skill Gap Analysis:** AI compares the Resume against JDs to highlight missing requirements.
* **Smart Match Score:** Ranks jobs based on semantic similarity to the user's profile, not just keyword matching.
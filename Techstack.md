# 🛠 Technology Stack

This project utilizes a modern, AI-Native stack focused on Data Engineering, RAG (Retrieval-Augmented Generation), and High-Performance Computing.

## Core Language
* **Python (3.10+)**: Chosen for its rich ecosystem in Scraping, PDF processing, and AI integration.

## Data Acquisition (Scraping)
* **Playwright**:
    * *Reason:* Handles dynamic content (React/Vue hydration) on job boards effortlessly. Configured with stealth plugins to bypass sophisticated bot detection (Cloudflare/Akamai).

## Data Processing & AI (The "Brain")
* **Ollama (Local LLM - Llama3/Mistral)**:
    * *Reason:* Used for **offline JD Parsing**. It extracts structured data (Skills, Experience Years) from unstructured job descriptions without incurring API costs.
* **Gemini API (Google) / Groq Cloud API**:
    * *Reason:* Used for **real-time user interaction**. It powers the "Cover Letter Generator" and "Resume Feedback" features due to its high speed and reasoning capabilities.
* **PyMuPDF4LLM**:
    * *Reason:* A specialized library that converts PDF Resumes into Markdown. Unlike traditional parsers, it preserves layout semantics (headers, tables, lists), which is critical for the LLM to understand the structure of a resume accurately.

## Database & Storage
* **PostgreSQL**:
    * *Reason:* The most robust open-source RDBMS, handling relational data (Jobs, Users) with ACID compliance.
* **pgvector**:
    * *Reason:* Transforms PostgreSQL into a high-performance Vector Database. Allows for Hybrid Search (combining SQL filters like salary > 50k with Semantic Vector Search) in a single query, eliminating the need for a separate vector DB like Pinecone.

## Backend API
* **FastAPI (with Pydantic v2)**:
    * *Reason:* The fastest Python web framework. Utilizes Pydantic v2 (Rust-core) for ultra-fast data validation and serialization. Supports strictly typed interactions with AI agents.

## Frontend
* **Next.js (React)**:
    * *Reason:* Provides Server-Side Rendering (SSR) for SEO and performance.
* **Tailwind CSS**: For rapid UI styling.
* **Shadcn UI**:
    * *Reason:* A collection of professional, reusable components to build a dashboard-quality interface (Datatables, Cards, Dialogs) quickly.

## DevOps & Orchestration
* **GitHub Actions**:
    * *Reason:* Acts as a free scheduler (Cron) to run the daily job scraping pipeline.
* **Docker**:
    * *Reason:* Orchestrates the multi-container environment (API, DB, Adminer) ensuring consistency across Dev/Prod.
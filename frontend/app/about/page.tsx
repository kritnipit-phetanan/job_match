"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Nav */}
      <nav className="w-full border-b border-border bg-card/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-3xl mx-auto flex items-center justify-between px-6 h-14">
          <Link href="/" className="text-lg font-semibold tracking-tight text-foreground hover:opacity-80 transition-opacity">
            JobMatcher
          </Link>
          <Link href="/" className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors font-medium">
            <ArrowLeft className="w-4 h-4" /> Back
          </Link>
        </div>
      </nav>

      {/* Content */}
      <main className="max-w-3xl mx-auto px-6 py-10 flex-1">
        <h1 className="text-3xl font-bold tracking-tight text-foreground mb-6">About JobMatcher</h1>

        <div className="space-y-6 text-foreground/90 leading-relaxed">
          <section>
            <h2 className="text-xl font-semibold text-foreground mb-2">What is JobMatcher?</h2>
            <p>
              JobMatcher is an AI-powered job matching platform that helps you discover career opportunities that truly fit your skills and experience.
              Simply upload your resume in PDF format, and our system will analyze it using advanced semantic search to surface the most relevant job listings from our database.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-2">How it works</h2>
            <ol className="list-decimal list-inside space-y-2 ml-1">
              <li><strong>Upload your resume</strong> — We parse your PDF and extract key information about your skills, experience, and career goals.</li>
              <li><strong>AI-powered matching</strong> — Using Gemini embedding models, we convert your resume into a semantic vector and compare it against thousands of job listings.</li>
              <li><strong>Smart ranking</strong> — Results are ranked by match score, with experience-level adjustments and skill gap analysis powered by AI.</li>
              <li><strong>Cover letter generation</strong> — For any matched job, you can instantly generate a tailored cover letter.</li>
            </ol>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-2">Tech Stack</h2>
            <ul className="list-disc list-inside space-y-1 ml-1 text-muted-foreground">
              <li><strong className="text-foreground">Frontend</strong> — Next.js, React, Tailwind CSS, Recharts</li>
              <li><strong className="text-foreground">Backend</strong> — FastAPI (Python)</li>
              <li><strong className="text-foreground">Database</strong> — PostgreSQL + pgvector (Supabase)</li>
              <li><strong className="text-foreground">AI / ML</strong> — Google Gemini (embedding & generation)</li>
              <li><strong className="text-foreground">Data Pipeline</strong> — Playwright (scraping), custom ETL pipeline</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-2">Market Analytics</h2>
            <p>
              Beyond resume matching, JobMatcher provides real-time market analytics including the most in-demand skills and salary trends
              across the job market. These insights help you understand where your skills stand and which areas to focus on for career growth.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-2">Data Freshness</h2>
            <p>
              Our job database is refreshed nightly through an automated scraping and ETL pipeline.
              Jobs that haven&apos;t been updated in over 30 days are automatically deactivated to ensure you only see current, active opportunities.
            </p>
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border py-4 mt-auto">
        <div className="max-w-3xl mx-auto px-6 flex items-center justify-between text-sm text-muted-foreground">
          <span>&copy; 2026 JobMatcher</span>
          <div className="flex gap-6">
            <Link href="/about" className="hover:text-foreground transition-colors font-medium text-foreground">About</Link>
            <Link href="/privacy" className="hover:text-foreground transition-colors">Privacy</Link>
            <Link href="/terms" className="hover:text-foreground transition-colors">Terms</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}

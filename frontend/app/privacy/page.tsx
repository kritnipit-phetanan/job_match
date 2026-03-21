"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function PrivacyPage() {
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
        <h1 className="text-3xl font-bold tracking-tight text-foreground mb-2">Privacy Policy</h1>
        <p className="text-sm text-muted-foreground mb-8">Last updated: March 22, 2026</p>

        <div className="space-y-6 text-foreground/90 leading-relaxed">
          <section>
            <h2 className="text-xl font-semibold text-foreground mb-2">Overview</h2>
            <p>
              JobMatcher is committed to protecting your privacy. This policy explains what data we collect,
              how we use it, and your rights regarding your information.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-2">Resume Data — No Storage</h2>
            <div className="bg-secondary/50 border border-border rounded-lg p-4 my-3">
              <p className="font-semibold text-foreground mb-1">🔒 We do NOT store your resume.</p>
              <p className="text-sm text-muted-foreground">
                Your resume file is processed entirely in memory on our servers. It is converted to text, analyzed by AI,
                and matched against job listings — all in real time during your session. Once processing is complete,
                your resume data is immediately discarded and never saved to any database, file system, or storage service.
              </p>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-2">Data & AI Processing</h2>
            <p className="text-muted-foreground">
              We only temporarily process your resume text via Google Gemini API to generate match scores, skill gaps, and cover letters. 
              No personal data is saved to our database, and we only store publicly obtained job listings.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-2">Cookies & Analytics</h2>
            <p>
              JobMatcher does not use cookies for tracking purposes. We do not use any third-party analytics or advertising services.
              No personal data is shared with third parties beyond the AI processing described above.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-2">Contact</h2>
            <p>
              If you have any questions about this privacy policy, please reach out via our GitHub repository.
            </p>
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border py-4 mt-auto">
        <div className="max-w-3xl mx-auto px-6 flex items-center justify-between text-sm text-muted-foreground">
          <span>&copy; 2026 JobMatcher</span>
          <div className="flex gap-6">
            <Link href="/about" className="hover:text-foreground transition-colors">About</Link>
            <Link href="/privacy" className="hover:text-foreground transition-colors font-medium text-foreground">Privacy</Link>
            <Link href="/terms" className="hover:text-foreground transition-colors">Terms</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}

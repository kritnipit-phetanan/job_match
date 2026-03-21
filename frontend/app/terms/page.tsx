"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function TermsPage() {
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
        <h1 className="text-3xl font-bold tracking-tight text-foreground mb-2">Terms of Service</h1>
        <p className="text-sm text-muted-foreground mb-8">Last updated: March 22, 2026</p>

        <div className="space-y-6 text-foreground/90 leading-relaxed">
          <section>
            <ul className="list-disc list-inside space-y-3 ml-1 text-muted-foreground">
              <li>
                <strong className="text-foreground">Usage:</strong> JobMatcher is an AI resume matching tool. You are responsible for the content you upload and agree not to misuse the service.
              </li>
              <li>
                <strong className="text-foreground">Job Data:</strong> Listings are sourced from public platforms. While we auto-deactivate jobs older than 30 days, we cannot guarantee the complete accuracy or availability of every listing.
              </li>
              <li>
                <strong className="text-foreground">AI Limitations:</strong> Match scores, skill gaps, and generated cover letters are AI-generated suggestions. We do not guarantee employment outcomes or perfectly accurate analysis.
              </li>
              <li>
                <strong className="text-foreground">Liability:</strong> The service is provided "as is". We are not liable for direct or indirect damages, data loss, or actions taken based on our AI analysis.
              </li>
              <li>
                <strong className="text-foreground">Intellectual Property:</strong> You own your resume. We own the JobMatcher platform code and design.
              </li>
            </ul>
          </section>
          
          <p className="text-sm text-muted-foreground italic mt-8">
            These terms may be updated at any time. Continued use constitutes acceptance. For questions, contact us via our GitHub repo.
          </p>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border py-4 mt-auto">
        <div className="max-w-3xl mx-auto px-6 flex items-center justify-between text-sm text-muted-foreground">
          <span>&copy; 2026 JobMatcher</span>
          <div className="flex gap-6">
            <Link href="/about" className="hover:text-foreground transition-colors">About</Link>
            <Link href="/privacy" className="hover:text-foreground transition-colors">Privacy</Link>
            <Link href="/terms" className="hover:text-foreground transition-colors font-medium text-foreground">Terms</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}

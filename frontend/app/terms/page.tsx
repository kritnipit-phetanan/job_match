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
            <h2 className="text-xl font-semibold text-foreground mb-2">1. Acceptance of Terms</h2>
            <p>
              By accessing and using JobMatcher, you agree to be bound by these Terms of Service.
              If you do not agree to these terms, please do not use our service.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-2">2. Description of Service</h2>
            <p>
              JobMatcher provides an AI-powered resume matching service that allows users to upload their resumes
              and receive job recommendations based on semantic similarity. The service also offers market analytics
              including skill demand trends and salary information.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-2">3. Use of Service</h2>
            <ul className="list-disc list-inside space-y-1 ml-1 text-muted-foreground">
              <li>You must provide accurate information when using the service.</li>
              <li>You are responsible for the content of the resumes you upload.</li>
              <li>You agree not to use the service for any unlawful or prohibited purpose.</li>
              <li>You agree not to attempt to reverse-engineer, scrape, or interfere with the service&apos;s operation.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-2">4. Job Listing Data</h2>
            <p>
              Job listings displayed on JobMatcher are sourced from publicly available job posting platforms.
              We make reasonable efforts to keep data up to date but cannot guarantee the accuracy,
              completeness, or availability of any job listing. Jobs that haven&apos;t been updated in over 30 days
              are automatically deactivated.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-2">5. AI-Generated Content</h2>
            <p>
              Match scores, skill gap analysis, and generated cover letters are produced by artificial intelligence
              and should be treated as suggestions only. JobMatcher does not guarantee:
            </p>
            <ul className="list-disc list-inside space-y-1 ml-1 text-muted-foreground mt-2">
              <li>The accuracy or relevance of match results</li>
              <li>The quality or appropriateness of generated cover letters</li>
              <li>The completeness of skill gap analysis</li>
              <li>Employment outcomes based on using the service</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-2">6. Limitation of Liability</h2>
            <p>
              JobMatcher is provided &ldquo;as is&rdquo; and &ldquo;as available&rdquo; without any warranties, express or implied.
              We are not liable for any direct, indirect, incidental, or consequential damages arising from
              your use of or inability to use the service, including but not limited to:
            </p>
            <ul className="list-disc list-inside space-y-1 ml-1 text-muted-foreground mt-2">
              <li>Inaccurate or outdated job information</li>
              <li>Errors in AI-generated analysis or content</li>
              <li>Service disruptions or data loss</li>
              <li>Actions taken based on information provided by the service</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-2">7. Intellectual Property</h2>
            <p>
              You retain all rights to the resumes you upload. Any cover letters generated by the service
              are provided for your personal use. The JobMatcher platform, including its design, code,
              and underlying algorithms, remains our intellectual property.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-2">8. Changes to Terms</h2>
            <p>
              We reserve the right to modify these terms at any time. Continued use of the service after
              changes constitutes acceptance of the updated terms.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-2">9. Contact</h2>
            <p>
              For questions regarding these terms, please reach out via our GitHub repository.
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
            <Link href="/privacy" className="hover:text-foreground transition-colors">Privacy</Link>
            <Link href="/terms" className="hover:text-foreground transition-colors font-medium text-foreground">Terms</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}

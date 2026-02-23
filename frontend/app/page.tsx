"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { UploadCloud, Home as HomeIcon } from "lucide-react";

const ResumeUpload = dynamic(() => import("@/components/ui/ResumeUpload"), {
  ssr: false,
});

const SkillHeatmap = dynamic(() => import("@/components/ui/SkillHeatmap"), {
  ssr: false,
});

const SalaryTrends = dynamic(() => import("@/components/ui/SalaryTrends"), {
  ssr: false,
});

function NavBar({ onHomeClick, hasResults }: { onHomeClick: (e?: React.MouseEvent) => void, hasResults: boolean }) {
  return (
    <nav className="w-full border-b border-border bg-card/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-6xl mx-auto flex items-center justify-between px-6 h-14">
        <span className="text-lg font-semibold tracking-tight text-foreground cursor-pointer" onClick={onHomeClick}>
          JobMatcher
        </span>
        <div className="flex items-center gap-6 text-sm text-muted-foreground">
          {hasResults ? (
            <button onClick={onHomeClick} className="flex items-center gap-1.5 hover:text-foreground transition-colors font-medium">
              <HomeIcon className="w-4 h-4" /> Home
            </button>
          ) : (
            <button onClick={onHomeClick} className="flex items-center gap-1.5 hover:text-foreground transition-colors font-medium">
              <HomeIcon className="w-4 h-4" /> Home
            </button>
          )}
        </div>
      </div>
    </nav>
  );
}

export default function Home() {
  const [hasResults, setHasResults] = useState(false);
  const [resetKey, setResetKey] = useState(0);
  const [activeChart, setActiveChart] = useState<"demand" | "salary">("demand");

  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showConfirmHome, setShowConfirmHome] = useState(false);

  const requestGoHome = (e?: React.MouseEvent) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    if (hasResults) {
      setShowConfirmHome(true);
    } else {
      confirmGoHome();
    }
  };

  const confirmGoHome = () => {
    setShowConfirmHome(false);
    setHasResults(false);
    setShowUploadModal(false);
    // Add small delay to let state flush, ensuring clean unmount
    setTimeout(() => setResetKey(prev => prev + 1), 10);
  };

  return (
    <div className="min-h-screen bg-background flex flex-col relative">
      <NavBar onHomeClick={requestGoHome} hasResults={hasResults} />
      <main className="max-w-6xl w-full mx-auto px-6 py-2 flex flex-col gap-3 flex-1">

        {!hasResults && (
          <div className="flex flex-col gap-4 animate-in fade-in duration-500">
            {/* Hero */}
            <section className="text-center pt-2">
              <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-foreground">
                Find your perfect match
              </h1>
              <p className="text-muted-foreground mt-1 text-base max-w-xl mx-auto">
                Match your resume with AI semantic search.
              </p>
              <div className="mt-4 flex justify-center">
                <button
                  onClick={() => setShowUploadModal(true)}
                  className="flex items-center gap-2 px-6 py-3 bg-primary text-primary-foreground font-semibold rounded-full shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300 text-sm"
                >
                  <UploadCloud className="w-5 h-5" />
                  Upload Resume to Match
                </button>
              </div>
            </section>

            {/* Market Analytics (Single view with toggle, uses CSS hiding for caching) */}
            <section id="market" className="flex flex-col items-center gap-2 w-full max-w-5xl mx-auto mt-0">
              <div className="w-full relative">
                <div className={activeChart === "demand" ? "block animate-in fade-in duration-300" : "hidden"}>
                  <SkillHeatmap activeChart={activeChart} setActiveChart={setActiveChart} />
                </div>
                <div className={activeChart === "salary" ? "block animate-in fade-in duration-300" : "hidden"}>
                  <SalaryTrends activeChart={activeChart} setActiveChart={setActiveChart} />
                </div>
              </div>
            </section>
          </div>
        )}

        {/* Resume Upload + Results */}
        <section id="upload" className={`w-full ${hasResults ? "animate-in fade-in zoom-in-95 duration-300" : ""}`}>
          <ResumeUpload
            key={resetKey}
            onStateChange={setHasResults}
            hasResults={hasResults}
            isModalOpen={showUploadModal}
            onCloseModal={() => setShowUploadModal(false)}
          />
        </section>

      </main>

      {/* Footer */}
      <footer className="border-t border-border py-4 mt-auto">
        <div className="max-w-6xl mx-auto px-6 flex items-center justify-between text-sm text-muted-foreground">
          <span>&copy; 2026 JobMatcher</span>
          <div className="flex gap-6">
            <span>About</span>
            <span>Privacy</span>
            <span>Terms</span>
          </div>
        </div>
      </footer>

      {/* Custom Confirm Home Modal */}
      {showConfirmHome && (
        <div className="fixed inset-0 z-[200] bg-background/80 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-card w-full max-w-sm rounded-2xl shadow-2xl border border-border p-6 relative">
            <h3 className="text-lg font-semibold text-foreground mb-2">Back to Home?</h3>
            <p className="text-sm text-muted-foreground mb-6">Do you want to go back to home? Your results will be cleared.</p>
            <div className="flex justify-end gap-3">
              <button
                className="px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-secondary rounded-lg transition-colors"
                onClick={() => setShowConfirmHome(false)}
              >
                Cancel
              </button>
              <button
                className="px-4 py-2 bg-primary text-primary-foreground text-sm font-medium rounded-lg shadow-sm hover:opacity-90 transition-opacity"
                onClick={confirmGoHome}
              >
                Yes, clear results
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
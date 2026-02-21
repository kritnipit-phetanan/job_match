"use client";

import dynamic from "next/dynamic";

const ResumeUpload = dynamic(() => import("@/components/ui/ResumeUpload"), {
  ssr: false,
});

const SkillHeatmap = dynamic(() => import("@/components/ui/SkillHeatmap"), {
  ssr: false,
});

const SalaryTrends = dynamic(() => import("@/components/ui/SalaryTrends"), {
  ssr: false,
});

export default function Home() {
  return (
    <main className="min-h-screen bg-background flex flex-col items-center justify-center p-4 gap-8">
      {/* วาง Component อัปโหลดตรงกลางจอ */}
      <ResumeUpload />
      {/* Analytics Section */}
      <div className="w-full max-w-5xl flex flex-col gap-8">
        <SkillHeatmap />
        <SalaryTrends />
      </div>
    </main>
  );
}
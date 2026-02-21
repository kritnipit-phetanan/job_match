"use client";

import dynamic from "next/dynamic";

const ResumeUpload = dynamic(() => import("@/components/ui/ResumeUpload"), {
  ssr: false,
});

const SkillHeatmap = dynamic(() => import("@/components/ui/SkillHeatmap"), {
  ssr: false,
});

export default function Home() {
  return (
    <main className="min-h-screen bg-background flex flex-col items-center justify-center p-4 gap-8">
      {/* วาง Component อัปโหลดตรงกลางจอ */}
      <ResumeUpload />
      {/* Market Demand Heatmap — แสดง Hot Skills จากงานทั้งหมด */}
      <div className="w-full max-w-5xl">
        <SkillHeatmap />
      </div>
    </main>
  );
}
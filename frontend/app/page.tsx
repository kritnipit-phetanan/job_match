import ResumeUpload from "@/components/ui/ResumeUpload";

export default function Home() {
  return (
    <main className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
      {/* วาง Component อัปโหลดตรงกลางจอ */}
      <ResumeUpload />
    </main>
  );
}
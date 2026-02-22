"use client";

import React, { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import {
    UploadCloud, FileText, X, Loader2, AlertCircle,
    Briefcase, MapPin, Building, Clock, ExternalLink, Sparkles, FileSignature
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import axios from "axios";

export default function ResumeUpload() {
    const [file, setFile] = useState<File | null>(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const [matchedJobs, setMatchedJobs] = useState<any[] | null>(null);
    const [resumeMarkdown, setResumeMarkdown] = useState<string>(""); // เก็บ Resume Text ไว้ส่งให้ Gemini

    // State สำหรับ Cover Letter
    const [generatingJobId, setGeneratingJobId] = useState<number | null>(null);
    const [coverLetters, setCoverLetters] = useState<Record<number, string>>({});

    // State สำหรับ Gap
    const [showGaps, setShowGaps] = useState<Record<number, boolean>>({});

    const onDrop = useCallback((acceptedFiles: File[]) => {
        if (acceptedFiles.length > 0) {
            setFile(acceptedFiles[0]);
            setError(null);
            setMatchedJobs(null);
            setCoverLetters({});
        }
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: { "application/pdf": [".pdf"] },
        maxFiles: 1,
    });

    // 1. ยิง API ค้นหางาน
    const handleAnalyze = async () => {
        if (!file) return;
        setIsAnalyzing(true);
        setError(null);
        setMatchedJobs(null);

        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/resume/analyze`, formData, {
                headers: { "Content-Type": "multipart/form-data" },
                params: { limit: 5 }
            });
            setMatchedJobs(response.data.jobs);
            setResumeMarkdown(response.data.resume_markdown); // เก็บ Text ไว้ใช้ต่อ
        } catch (err: any) {
            console.error("API Error:", err);
            setError(err.response?.data?.detail || "ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ได้");
        } finally {
            setIsAnalyzing(false);
        }
    };

    // 2. ฟังก์ชัน Effect พิมพ์ทีละตัวอักษร
    const typeWriterEffect = (text: string, jobId: number) => {
        let currentText = "";
        let i = 0;

        // พิมพ์ตัวอักษรใหม่ทุกๆ 15 มิลลิวินาที
        const interval = setInterval(() => {
            currentText += text.charAt(i);
            setCoverLetters(prev => ({ ...prev, [jobId]: currentText }));
            i++;
            if (i >= text.length) {
                clearInterval(interval);
                setGeneratingJobId(null); // พิมพ์เสร็จแล้ว ปิดสถานะ Loading
            }
        }, 15);
    };

    // 3. ยิง API ให้ Gemini เขียนจดหมาย
    const handleGenerateCoverLetter = async (job: any) => {
        setGeneratingJobId(job.id);
        setCoverLetters(prev => ({ ...prev, [job.id]: "" })); // เคลียร์ข้อความเก่า (ถ้ามี)

        try {
            const jobContext = job.description || `
        Job Title: ${job.title}
        Company: ${job.company}
        Required Skills: ${job.skills ? job.skills.join(", ") : "Not specified"}
        Experience Required: ${job.experience_years}
      `;

            const response = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/resume/generate-cover-letter`, {
                resume_markdown: resumeMarkdown,
                job_description: jobContext
            });

            const fullText = response.data.cover_letter;
            // เริ่มเล่น Effect พิมพ์ดีด
            typeWriterEffect(fullText, job.id);

        } catch (err: any) {
            console.error("Gemini API Error:", err);
            // ถอดข้อความ Error ที่ส่งมาจาก Backend เพื่อให้ Frontend แสดงผลได้ตรงประเด็นขึ้น
            const errorMsg = err.response?.data?.detail || "❌ ขออภัย AI กำลังประมวลผลให้คนอื่นอยู่ กรุณาลองใหม่อีกครั้ง";
            setCoverLetters(prev => ({ ...prev, [job.id]: errorMsg }));
            setGeneratingJobId(null);
        }
    };

    // // 4. ยิง API วิเคราะห์ Skill Gap
    // const handleAnalyzeGap = async (job: any) => {
    //     if (!job.skills || job.skills.length === 0) return;

    //     setAnalyzingGapId(job.id);
    //     try {
    //         const response = await axios.post("http://192.168.1.2:8000/resume/skill-gap", {
    //             resume_markdown: resumeMarkdown,
    //             job_skills: job.skills // ส่งรายการ Skill ดิบๆ ไปให้ AI
    //         });

    //         const data = response.data.data;
    //         // เอาผลลัพธ์มาเก็บลง State แยกตาม ID ของงาน
    //         setSkillGaps(prev => ({
    //             ...prev,
    //             [job.id]: {
    //                 matched: data.matched_skills || [],
    //                 missing: data.missing_skills || []
    //             }
    //         }));
    //     } catch (err: any) {
    //         console.error("Skill Gap API Error:", err);
    //         const errorMsg = err.response?.data?.detail || "ขออภัย AI เซิร์ฟเวอร์กำลังทำงานหนัก กรุณาลองใหม่ในอีกสักครู่";
    //         alert(errorMsg);
    //     } finally {
    //         setAnalyzingGapId(null);
    //     }
    // };

    const getScoreColor = (score: number) => {
        if (score >= 75) return "text-green-600 dark:text-green-400";
        if (score >= 60) return "text-yellow-600 dark:text-yellow-400";
        return "text-muted-foreground";
    };

    return (
        <div className="w-full max-w-5xl mx-auto flex flex-col gap-8 py-8 px-4">
            {/* ----------------- ส่วนอัปโหลดไฟล์ (เหมือนเดิม) ----------------- */}
            <Card className="w-full shadow-sm border-border">
                {/* ... (โค้ดส่วน Upload เหมือนเดิมเป๊ะ ขอข้ามเพื่อความกระชับ) ... */}
                <CardContent className="p-8">
                    <div className="mb-8 text-center">
                        <h2 className="text-3xl font-bold tracking-tight text-foreground">JobMatcher AI 🧠</h2>
                        <p className="text-muted-foreground mt-2">อัปโหลด Resume ของคุณ (PDF) เพื่อค้นหางานที่ Match ที่สุด</p>
                    </div>

                    {!file ? (
                        <div {...getRootProps()} className={`border-2 border-dashed rounded-xl p-12 flex flex-col items-center justify-center cursor-pointer transition-all duration-200 ${isDragActive ? "border-primary bg-primary/5 scale-[1.02]" : "border-muted-foreground/25 hover:bg-secondary/50 hover:border-primary/50"}`}>
                            <input {...getInputProps()} />
                            <UploadCloud className={`w-14 h-14 mb-4 transition-colors ${isDragActive ? "text-primary" : "text-muted-foreground"}`} />
                            <p className="text-lg font-medium text-center">{isDragActive ? "วางไฟล์ที่นี่ได้เลย! 📥" : "ลากไฟล์ PDF มาวาง หรือคลิกเพื่อเลือกไฟล์"}</p>
                        </div>
                    ) : (
                        <div className="flex flex-col items-center p-8 border rounded-xl bg-secondary/20 animate-in fade-in zoom-in duration-300">
                            <FileText className="w-16 h-16 text-primary mb-4" />
                            <p className="text-xl font-medium text-foreground text-center line-clamp-1">{file.name}</p>
                            {error && (
                                <div className="flex items-center gap-2 text-destructive bg-destructive/10 px-4 py-2 rounded-md mt-4">
                                    <AlertCircle className="w-4 h-4" /> <span className="text-sm font-medium">{error}</span>
                                </div>
                            )}
                            <div className="flex gap-4 w-full justify-center mt-8">
                                <Button variant="outline" onClick={() => { setFile(null); setMatchedJobs(null); setError(null); setCoverLetters({}); }} disabled={isAnalyzing} className="w-32"><X className="w-4 h-4 mr-2" /> ยกเลิก</Button>
                                <Button onClick={handleAnalyze} disabled={isAnalyzing} className="w-48">
                                    {isAnalyzing ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> กำลังวิเคราะห์...</> : "✨ วิเคราะห์ Resume"}
                                </Button>
                            </div>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* ----------------- ส่วนแสดงผลการ์ดงาน (Dashboard) ----------------- */}
            {matchedJobs && (
                <div className="flex flex-col gap-4 animate-in slide-in-from-bottom-4 duration-500">
                    <h3 className="text-2xl font-bold flex items-center gap-2">🎯 งานที่เหมาะกับคุณ ({matchedJobs.length})</h3>

                    <div className="grid grid-cols-1 gap-4">
                        {matchedJobs.map((job) => (
                            <Card key={job.id} className="hover:shadow-md transition-shadow border-border overflow-hidden">
                                <CardContent className="p-6 flex flex-col gap-6">

                                    {/* ข้อมูลด้านบน */}
                                    <div className="flex flex-col md:flex-row justify-between gap-6">
                                        <div className="flex-1 space-y-4">
                                            <div>
                                                <h4 className="text-xl font-bold text-primary">{job.title}</h4>
                                                <div className="flex flex-wrap items-center gap-4 mt-2 text-sm text-muted-foreground">
                                                    <span className="flex items-center gap-1"><Building className="w-4 h-4" /> {job.company || "ไม่ระบุบริษัท"}</span>
                                                    <span className="flex items-center gap-1"><MapPin className="w-4 h-4" /> {job.location || "ไม่ระบุสถานที่"}</span>
                                                    <span className="flex items-center gap-1"><Briefcase className="w-4 h-4" /> {job.experience_years}</span>
                                                </div>
                                            </div>
                                            <div className="flex flex-wrap gap-2">
                                                {/* --- พื้นที่แสดงผล Skills --- */}
                                                <div className="flex flex-col gap-3 mt-4">
                                                    {showGaps[job.id] ? (
                                                        // แสดงผลแบบแยก มี/ขาด (ข้อมูลมารออยู่แล้ว ไม่ต้องโหลด)
                                                        <div className="flex flex-col gap-2 animate-in fade-in zoom-in duration-300">
                                                            {job.matched_skills && job.matched_skills.length > 0 && (
                                                                <div className="flex flex-wrap gap-2 items-center">
                                                                    <span className="text-sm font-semibold text-green-600 w-16">✅ มี:</span>
                                                                    {job.matched_skills.map((skill: string, idx: number) => (
                                                                        <Badge key={`m-${idx}`} className="bg-green-100 text-green-800 border-green-200">{skill}</Badge>
                                                                    ))}
                                                                </div>
                                                            )}
                                                            {job.missing_skills && job.missing_skills.length > 0 && (
                                                                <div className="flex flex-wrap gap-2 items-center">
                                                                    <span className="text-sm font-semibold text-red-600 w-16">❌ ขาด:</span>
                                                                    {job.missing_skills.map((skill: string, idx: number) => (
                                                                        <Badge key={`x-${idx}`} variant="outline" className="bg-red-50 text-red-600 border-red-200">{skill}</Badge>
                                                                    ))}
                                                                </div>
                                                            )}
                                                            <Button variant="ghost" size="sm" className="h-6 mt-2 text-xs w-24" onClick={() => setShowGaps(prev => ({ ...prev, [job.id]: false }))}>
                                                                ซ่อน Skill Gap
                                                            </Button>
                                                        </div>
                                                    ) : (
                                                        // แสดงผลแบบรวมปกติ
                                                        <div className="flex flex-wrap items-center gap-2">
                                                            {job.skills?.slice(0, 7).map((skill: string, idx: number) => (
                                                                <Badge key={idx} variant="secondary" className="font-normal">{skill}</Badge>
                                                            ))}
                                                            {job.skills?.length > 7 && (
                                                                <Badge variant="outline" className="font-normal text-muted-foreground">+{job.skills.length - 7} อื่นๆ</Badge>
                                                            )}

                                                            {/* ปุ่มกดเปิดดู Gap (สลับ UI ทันที ไม่ต้องรอ API) */}
                                                            <Button
                                                                variant="ghost"
                                                                size="sm"
                                                                className="h-6 px-2 text-xs text-primary font-semibold hover:bg-primary/10 ml-2"
                                                                onClick={() => setShowGaps(prev => ({ ...prev, [job.id]: true }))}
                                                            >
                                                                🔍 ดู Skill Gap
                                                            </Button>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </div>

                                        <div className="flex flex-col justify-between md:items-end w-full md:w-64 space-y-4 md:space-y-0">
                                            <div className="w-full bg-secondary/50 p-4 rounded-lg">
                                                <div className="flex justify-between items-end mb-2">
                                                    <span className="text-sm font-medium">Match Score</span>
                                                    <span className={`text-2xl font-bold ${getScoreColor(job.match_score)}`}>{job.match_score}%</span>
                                                </div>
                                                <Progress value={job.match_score} className="h-2" />
                                            </div>

                                            <div className="flex flex-col gap-2 w-full">
                                                {/* ปุ่มกด Generate Cover Letter */}
                                                <Button
                                                    className="w-full gap-2 transition-all"
                                                    variant="default"
                                                    onClick={() => handleGenerateCoverLetter(job)}
                                                    disabled={generatingJobId === job.id}
                                                >
                                                    {generatingJobId === job.id ? (
                                                        <><Loader2 className="w-4 h-4 animate-spin" /> กำลังเขียน...</>
                                                    ) : (
                                                        <><Sparkles className="w-4 h-4" /> เขียน Cover Letter</>
                                                    )}
                                                </Button>
                                                <Button className="w-full gap-2" variant="outline" asChild>
                                                    <a href={job.link} target="_blank" rel="noopener noreferrer">ดูรายละเอียดงาน <ExternalLink className="w-4 h-4" /></a>
                                                </Button>
                                            </div>
                                        </div>
                                    </div>

                                    {/* ---------------- พื้นที่แสดง Cover Letter แบบ Real-time ---------------- */}
                                    {(coverLetters[job.id] !== undefined || generatingJobId === job.id) && (
                                        <div className="mt-2 p-6 bg-primary/5 rounded-xl border border-primary/20 animate-in slide-in-from-top-2">
                                            <h5 className="text-sm font-bold flex items-center gap-2 mb-4 text-primary">
                                                <FileSignature className="w-5 h-5" />
                                                AI-Generated Cover Letter
                                            </h5>
                                            <div className="text-sm md:text-base whitespace-pre-wrap text-foreground/90 leading-relaxed font-serif">
                                                {coverLetters[job.id]}
                                                {/* เคอร์เซอร์กะพริบตอนกำลังพิมพ์ */}
                                                {generatingJobId === job.id && (
                                                    <span className="inline-block w-2 h-4 ml-1 bg-primary animate-pulse relative top-1"></span>
                                                )}
                                            </div>
                                        </div>
                                    )}

                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
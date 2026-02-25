"use client";

import React, { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import {
    UploadCloud, FileText, X, Loader2, AlertCircle,
    Briefcase, MapPin, Building, ExternalLink, Sparkles, FileSignature,
    CheckCircle, XCircle, ChevronDown, ChevronUp
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import axios from "axios";

// Circular score indicator - slightly larger now
function ScoreCircle({ score }: { score: number }) {
    const radius = 38; // increased from 36
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (score / 100) * circumference;
    const color = score >= 75 ? "#22c55e" : score >= 60 ? "#ca8a04" : "#a1a1aa";

    return (
        <div className="relative w-28 h-28 flex items-center justify-center">
            <svg className="w-28 h-28 -rotate-90" viewBox="0 0 92 92">
                <circle cx="46" cy="46" r={radius} fill="none" stroke="var(--border)" strokeWidth="4" />
                <circle
                    cx="46" cy="46" r={radius} fill="none"
                    stroke={color} strokeWidth="4" strokeLinecap="round"
                    strokeDasharray={circumference} strokeDashoffset={offset}
                    className="transition-all duration-700 ease-out"
                />
            </svg>
            <span className="absolute text-2xl font-bold" style={{ color }}>
                {Number(score).toFixed(0)}%
            </span>
        </div>
    );
}

interface ResumeUploadProps {
    onStateChange?: (hasResults: boolean) => void;
    hasResults?: boolean;
    isModalOpen?: boolean;
    onCloseModal?: () => void;
}

export default function ResumeUpload({ onStateChange, hasResults, isModalOpen, onCloseModal }: ResumeUploadProps) {
    const [file, setFile] = useState<File | null>(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const [matchedJobs, setMatchedJobs] = useState<any[] | null>(null);
    const [resumeMarkdown, setResumeMarkdown] = useState<string>("");

    // ... (rest of the state from original setup)
    const [generatingJobId, setGeneratingJobId] = useState<number | null>(null);
    const [coverLetters, setCoverLetters] = useState<Record<number, string>>({});
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

    const handleAnalyze = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!file) return;
        setIsAnalyzing(true);
        setError(null);
        setMatchedJobs(null);

        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/resume/analyze`, formData, {
                headers: { "Content-Type": "multipart/form-data" },
                params: { limit: 10 }
            });
            setMatchedJobs(response.data.jobs);
            setResumeMarkdown(response.data.resume_markdown);
            if (onStateChange) onStateChange(true);
        } catch (err: any) {
            console.error("API Error:", err);
            setError(err.response?.data?.detail || "Could not connect to the server");
        } finally {
            setIsAnalyzing(false);
        }
    };

    const typeWriterEffect = (text: string, jobId: number) => {
        let currentText = "";
        let i = 0;
        const interval = setInterval(() => {
            currentText += text.charAt(i);
            setCoverLetters(prev => ({ ...prev, [jobId]: currentText }));
            i++;
            if (i >= text.length) {
                clearInterval(interval);
                setGeneratingJobId(null);
            }
        }, 15);
    };

    const handleGenerateCoverLetter = async (job: any) => {
        setGeneratingJobId(job.id);
        setCoverLetters(prev => ({ ...prev, [job.id]: "" }));

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
            typeWriterEffect(response.data.cover_letter, job.id);
        } catch (err: any) {
            console.error("API Error:", err);
            const errorMsg = err.response?.data?.detail || "AI is currently busy. Please try again.";
            setCoverLetters(prev => ({ ...prev, [job.id]: errorMsg }));
            setGeneratingJobId(null);
        }
    };

    return (
        <div className="w-full max-w-[1000px] mx-auto flex flex-col gap-6">

            {/* ---- Upload Area Modal (Only show if NO results and modal is open) ---- */}
            {!hasResults && isModalOpen && (
                <div className="fixed inset-0 z-[100] bg-background/80 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200">
                    <div className="bg-card w-full max-w-lg rounded-2xl shadow-2xl border border-border relative p-1 mt-[-10vh]">
                        {onCloseModal && (
                            <button
                                onClick={onCloseModal}
                                className="absolute z-10 top-4 right-4 text-muted-foreground hover:text-foreground transition-colors"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        )}
                        <Card className="border-0 shadow-none bg-transparent">
                            <CardContent className="p-6">
                                <div className="mb-6">
                                    <h3 className="text-xl font-semibold tracking-tight text-foreground">Upload Resume</h3>
                                    <p className="text-sm text-muted-foreground mt-1">We'll find the best matching jobs for your skills.</p>
                                </div>
                                {!file ? (
                                    <div
                                        {...getRootProps()}
                                        className={`border-2 border-dashed rounded-xl py-8 px-6 flex flex-col items-center justify-center cursor-pointer transition-all duration-200 ${isDragActive
                                            ? "border-primary bg-primary/5 scale-[1.01]"
                                            : "border-border hover:border-primary/50 hover:bg-secondary/30"
                                            }`}
                                    >
                                        <input {...getInputProps()} />
                                        <UploadCloud className={`w-10 h-10 mb-3 ${isDragActive ? "text-primary" : "text-muted-foreground"}`} />
                                        <p className="text-base font-medium">
                                            {isDragActive ? "Drop it here" : "Drop your resume (PDF) here"}
                                        </p>
                                        <p className="text-sm text-muted-foreground mt-1">or browse to upload</p>
                                    </div>
                                ) : (
                                    <div className="flex flex-col items-center p-6 border rounded-xl bg-secondary/20 animate-in fade-in zoom-in duration-300">
                                        <FileText className="w-10 h-10 text-primary mb-3" />
                                        <p className="text-base font-medium text-foreground line-clamp-1">{file.name}</p>
                                        {error && (
                                            <div className="flex items-center gap-2 text-destructive bg-destructive/10 px-4 py-2 rounded-md mt-4">
                                                <AlertCircle className="w-4 h-4" /> <span className="text-sm">{error}</span>
                                            </div>
                                        )}
                                        <div className="flex gap-3 mt-5">
                                            <Button
                                                variant="outline" size="sm"
                                                onClick={() => { setFile(null); setMatchedJobs(null); setError(null); setCoverLetters({}); }}
                                                disabled={isAnalyzing}
                                            >
                                                <X className="w-4 h-4 mr-1" /> Cancel
                                            </Button>
                                            <Button type="button" size="sm" onClick={handleAnalyze} disabled={isAnalyzing}>
                                                {isAnalyzing ? (
                                                    <><Loader2 className="w-4 h-4 mr-1 animate-spin" /> Analyzing...</>
                                                ) : "Analyze Resume"}
                                            </Button>
                                        </div>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </div>
                </div>
            )}

            {/* ---- Matched Jobs (Takes over view) ---- */}
            {matchedJobs && hasResults && (
                <div className="flex flex-col gap-5">
                    <h3 className="text-xl font-semibold tracking-tight px-4">
                        Matched Jobs
                        <span className="text-muted-foreground font-normal ml-2 text-base">({matchedJobs.length})</span>
                    </h3>

                    <div className="flex flex-col gap-4">
                        {matchedJobs.map((job) => (
                            <Card key={job.id} className="hover:shadow-md transition-shadow border-border">
                                <CardContent className="p-6 py-7 flex flex-col gap-4">

                                    {/* Top row: info + score */}
                                    <div className="flex flex-col md:flex-row justify-between gap-5">
                                        <div className="flex-1 space-y-3">
                                            <div>
                                                <h4 className="text-lg font-semibold text-foreground">{job.title}</h4>
                                                <div className="flex flex-wrap items-center gap-4 mt-1.5 text-sm text-muted-foreground">
                                                    <span className="flex items-center gap-1"><Building className="w-3.5 h-3.5" /> {job.company || "N/A"}</span>
                                                    <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5" /> {job.location || "N/A"}</span>
                                                    <span className="flex items-center gap-1"><Briefcase className="w-3.5 h-3.5" /> {job.experience_years}</span>
                                                </div>
                                            </div>

                                            {/* Skills */}
                                            <div className="flex flex-col gap-2">
                                                {showGaps[job.id] ? (
                                                    <div className="flex flex-col gap-2 animate-in fade-in duration-200">
                                                        {job.matched_skills?.length > 0 && (
                                                            <div className="flex flex-wrap gap-1.5 items-center">
                                                                <CheckCircle className="w-3.5 h-3.5 text-green-600 mr-1" />
                                                                {job.matched_skills.map((skill: string, idx: number) => (
                                                                    <Badge key={`m-${idx}`} className="bg-green-50 text-green-700 border-green-200 text-xs">{skill}</Badge>
                                                                ))}
                                                            </div>
                                                        )}
                                                        {job.missing_skills?.length > 0 && (
                                                            <div className="flex flex-wrap gap-1.5 items-center">
                                                                <XCircle className="w-3.5 h-3.5 text-red-500 mr-1" />
                                                                {job.missing_skills.map((skill: string, idx: number) => (
                                                                    <Badge key={`x-${idx}`} variant="outline" className="bg-red-50/50 text-red-600 border-red-200 text-xs">{skill}</Badge>
                                                                ))}
                                                            </div>
                                                        )}
                                                        <Button variant="ghost" size="sm" className="h-6 text-xs w-fit mt-1" onClick={() => setShowGaps(prev => ({ ...prev, [job.id]: false }))}>
                                                            <ChevronUp className="w-3 h-3 mr-1" /> Hide Gap
                                                        </Button>
                                                    </div>
                                                ) : (
                                                    <div className="flex flex-wrap items-center gap-1.5">
                                                        {job.skills?.slice(0, 6).map((skill: string, idx: number) => (
                                                            <Badge key={idx} variant="secondary" className="font-normal text-xs">{skill}</Badge>
                                                        ))}
                                                        {job.skills?.length > 6 && (
                                                            <Badge variant="outline" className="font-normal text-xs text-muted-foreground">+{job.skills.length - 6}</Badge>
                                                        )}
                                                        <Button
                                                            variant="ghost" size="sm"
                                                            className="h-6 px-2 text-xs text-primary font-medium ml-1"
                                                            onClick={() => setShowGaps(prev => ({ ...prev, [job.id]: true }))}
                                                        >
                                                            <ChevronDown className="w-3 h-3 mr-1" /> Skill Gap
                                                        </Button>
                                                    </div>
                                                )}
                                            </div>
                                        </div>

                                        {/* Right side: score + actions */}
                                        <div className="flex flex-col items-center justify-start gap-2.5 md:w-[150px] shrink-0">
                                            <ScoreCircle score={job.match_score} />
                                            <div className="flex w-full flex-col gap-2 mt-1">
                                                <Button
                                                    size="sm" className="w-full gap-1.5 text-xs h-8"
                                                    onClick={() => handleGenerateCoverLetter(job)}
                                                    disabled={generatingJobId === job.id}
                                                >
                                                    {generatingJobId === job.id ? (
                                                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                                    ) : (
                                                        <><Sparkles className="w-3.5 h-3.5" /> Cover Letter</>
                                                    )}
                                                </Button>
                                                <Button size="sm" variant="outline" className="w-full gap-1.5 text-xs h-8" asChild>
                                                    <a href={job.link} target="_blank" rel="noopener noreferrer">
                                                        View Job <ExternalLink className="w-3 h-3" />
                                                    </a>
                                                </Button>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Cover Letter (typewriter) */}
                                    {(coverLetters[job.id] !== undefined || generatingJobId === job.id) && (
                                        <div className="p-4 bg-secondary/30 rounded-lg border border-border mt-1 animate-in slide-in-from-top-2">
                                            <h5 className="text-sm font-semibold flex items-center gap-1.5 mb-2.5 text-primary">
                                                <FileSignature className="w-4 h-4" />
                                                AI-Generated Cover Letter
                                            </h5>
                                            <div className="text-sm whitespace-pre-wrap text-foreground/85 leading-relaxed">
                                                {coverLetters[job.id]}
                                                {generatingJobId === job.id && (
                                                    <span className="inline-block w-1.5 h-4 ml-0.5 bg-primary animate-pulse relative top-0.5" />
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
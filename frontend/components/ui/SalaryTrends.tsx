"use client";

import React, { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Card, CardContent } from "@/components/ui/card";
import { Loader2, DollarSign } from "lucide-react";
import axios from "axios";

interface SalarySkill {
    name: string;
    job_count: number;
    avg_min: number;
    avg_max: number;
    avg_salary: number;
}

// Warm purple-brown tones
const SALARY_COLORS = [
    "#6b3a2a", "#7d4a36", "#8f5a42",
    "#a16b4e", "#b37c5a", "#c48d66",
    "#d69e72", "#e0b08a", "#eac2a2",
    "#f0d4ba",
];

function getSalaryColor(index: number, total: number): string {
    const ratio = index / Math.max(total - 1, 1);
    const colorIndex = Math.min(
        Math.floor(ratio * SALARY_COLORS.length),
        SALARY_COLORS.length - 1
    );
    return SALARY_COLORS[colorIndex];
}

function formatSalary(value: number): string {
    if (value >= 1000) return `${(value / 1000).toFixed(0)}k`;
    return value.toLocaleString();
}

function SalaryTooltip({ active, payload }: any) {
    if (!active || !payload?.[0]) return null;
    const data = payload[0].payload;
    return (
        <div className="bg-card text-foreground border border-border rounded-lg shadow-lg px-3 py-2">
            <p className="font-semibold text-sm">{data.name}</p>
            <div className="mt-1 space-y-0.5 text-xs">
                <p className="text-muted-foreground">
                    Avg <span className="font-semibold text-foreground">{data.avg_salary.toLocaleString()}</span>/mo
                </p>
                <p className="text-muted-foreground">
                    Range {data.avg_min.toLocaleString()} – {data.avg_max.toLocaleString()}
                </p>
                <p className="text-muted-foreground">
                    From <span className="font-semibold text-foreground">{data.job_count}</span> jobs
                </p>
            </div>
        </div>
    );
}

export default function SalaryTrends({ activeChart, setActiveChart }: { activeChart?: string, setActiveChart?: (v: any) => void }) {
    const [skills, setSkills] = useState<SalarySkill[]>([]);
    const [totalJobs, setTotalJobs] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        axios.get(`${process.env.NEXT_PUBLIC_API_URL}/analytics/salary-trends`, { params: { limit: 15 } })
            .then(res => {
                setSkills(res.data.skills);
                setTotalJobs(res.data.total_jobs_with_salary);
            })
            .catch(err => {
                console.error("Salary Trends API Error:", err);
                setError("Could not load salary data");
            })
            .finally(() => setLoading(false));
    }, []);

    if (loading) {
        return (
            <Card className="w-full h-[500px] shadow-sm border-border">
                <CardContent className="p-10 flex flex-col items-center justify-center gap-2 h-full">
                    <Loader2 className="w-6 h-6 animate-spin text-primary" />
                    <p className="text-muted-foreground text-sm">Loading salary data...</p>
                </CardContent>
            </Card>
        );
    }

    if (error || skills.length === 0) return null;

    return (
        <Card className="w-full h-[500px] shadow-sm border-border flex flex-col">
            <CardContent className="px-5 py-4 flex-1 flex flex-col relative w-full">
                <div className="mb-2 flex flex-col items-center justify-center w-full relative">
                    {/* Centered Toggles */}
                    <div className="flex items-center gap-1 p-1 bg-secondary rounded-full shadow-inner border border-border/50 z-10 w-fit">
                        <button
                            onClick={() => setActiveChart?.("demand")}
                            className={`px-8 py-1.5 rounded-full text-sm font-bold transition-all duration-300 ${activeChart === "demand"
                                ? "bg-card text-foreground shadow-sm ring-1 ring-border"
                                : "text-muted-foreground hover:text-foreground hover:bg-white/50"
                                }`}
                        >
                            Market Demand
                        </button>
                        <button
                            onClick={() => setActiveChart?.("salary")}
                            className={`px-8 py-1.5 rounded-full text-sm font-bold transition-all duration-300 ${(!activeChart || activeChart === "salary")
                                ? "bg-card text-foreground shadow-sm ring-1 ring-border"
                                : "text-muted-foreground hover:text-foreground hover:bg-white/50"
                                }`}
                        >
                            Salary Trends
                        </button>
                    </div>
                    {/* Subtitle */}
                    <p className="text-xs text-muted-foreground mt-2">
                        Average salary by skill from {totalJobs} listings
                    </p>

                    {/* Legend (Absolute right, hidden on very small screens) */}
                    <div className="absolute right-0 top-0 hidden sm:flex flex-col items-end gap-1">
                        <span className="text-[9px] text-muted-foreground/80 font-medium uppercase tracking-wider">Salary</span>
                        <div className="flex items-center gap-1.5">
                            <span className="text-[10px] text-foreground font-medium">High</span>
                            <div className="h-2.5 w-20 rounded-full" style={{ background: "linear-gradient(to right, #6b3a2a, #f0d4ba)" }} />
                            <span className="text-[10px] text-muted-foreground">Low</span>
                        </div>
                        <p className="text-[9px] text-muted-foreground mt-1 whitespace-nowrap hidden sm:block">
                            * Only skills with 3+ salary data points shown
                        </p>
                    </div>
                </div>

                <div className="w-full flex-1">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={skills} layout="vertical" margin={{ left: -15, right: 10, top: 0, bottom: 0 }}>
                            <XAxis type="number" tickFormatter={formatSalary}
                                tick={{ fontSize: 12, fill: "var(--muted-foreground)" }}
                                axisLine={false} tickLine={false}
                            />
                            <YAxis
                                type="category" dataKey="name" width={90}
                                tick={{ fontSize: 12, fill: "var(--muted-foreground)" }}
                                interval={0}
                                axisLine={false} tickLine={false}
                            />
                            <Tooltip content={<SalaryTooltip />} cursor={{ fill: "var(--accent)", opacity: 0.3 }} />
                            <Bar dataKey="avg_salary" radius={[0, 4, 4, 0]} barSize={16}>
                                {skills.map((entry, index) => (
                                    <Cell key={entry.name} fill={getSalaryColor(index, skills.length)} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </CardContent>
        </Card>
    );
}

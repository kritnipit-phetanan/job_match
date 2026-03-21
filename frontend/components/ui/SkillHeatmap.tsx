"use client";

import React, { useEffect, useState, useMemo } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Card, CardContent } from "@/components/ui/card";
import { Loader2, TrendingUp } from "lucide-react";
import axios from "axios";

interface SkillData {
    name: string;
    count: number;
}

// Warm palette: deep amber → light gold
const WARM_COLORS = [
    "#7c4a00", "#8b5a0a", "#a06b14",
    "#b57d1e", "#c49528", "#d4a832",
    "#e0be50", "#ecd06e", "#f5e08c",
    "#faeaaa",
];

function getWarmColor(index: number, total: number): string {
    const ratio = index / Math.max(total - 1, 1);
    const colorIndex = Math.min(
        Math.floor(ratio * WARM_COLORS.length),
        WARM_COLORS.length - 1
    );
    return WARM_COLORS[colorIndex];
}

function measureTextWidth(text: string, fontSize: number = 12): number {
    if (typeof document === "undefined") return text.length * 7;
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    if (!ctx) return text.length * 7;
    ctx.font = `${fontSize}px Inter, sans-serif`;
    return ctx.measureText(text).width;
}

function ChartTooltip({ active, payload }: any) {
    if (!active || !payload?.[0]) return null;
    const data = payload[0].payload;
    return (
        <div className="bg-card text-foreground border border-border rounded-lg shadow-lg px-3 py-2">
            <p className="font-semibold text-sm">{data.name}</p>
            <p className="text-xs text-muted-foreground mt-0.5">
                Found in <span className="font-semibold text-foreground">{data.count}</span> jobs
            </p>
        </div>
    );
}

export default function SkillHeatmap({ activeChart, setActiveChart }: { activeChart?: string, setActiveChart?: (v: any) => void }) {
    const [skills, setSkills] = useState<SkillData[]>([]);
    const [totalJobs, setTotalJobs] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        axios.get(`${process.env.NEXT_PUBLIC_API_URL}/analytics/hot-skills`, { params: { limit: 15 } })
            .then(res => {
                setSkills(res.data.skills);
                setTotalJobs(res.data.total_jobs);
            })
            .catch(err => {
                console.error("Hot Skills API Error:", err);
                setError("Could not load market data");
            })
            .finally(() => setLoading(false));
    }, []);

    const yAxisWidth = useMemo(() => {
        if (skills.length === 0) return 90;
        const maxWidth = Math.max(...skills.map(s => measureTextWidth(s.name, 12)));
        return Math.max(90, Math.ceil(maxWidth + 12));
    }, [skills]);

    if (loading) {
        return (
            <Card className="w-full h-[500px] shadow-sm border-border">
                <CardContent className="p-10 flex flex-col items-center justify-center gap-2 h-full">
                    <Loader2 className="w-6 h-6 animate-spin text-primary" />
                    <p className="text-muted-foreground text-sm">Loading market data...</p>
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
                            className={`px-8 py-1.5 rounded-full text-sm font-bold transition-all duration-300 ${(!activeChart || activeChart === "demand")
                                ? "bg-card text-foreground shadow-sm ring-1 ring-border"
                                : "text-muted-foreground hover:text-foreground hover:bg-white/50"
                                }`}
                        >
                            Market Demand
                        </button>
                        <button
                            onClick={() => setActiveChart?.("salary")}
                            className={`px-8 py-1.5 rounded-full text-sm font-bold transition-all duration-300 ${activeChart === "salary"
                                ? "bg-card text-foreground shadow-sm ring-1 ring-border"
                                : "text-muted-foreground hover:text-foreground hover:bg-white/50"
                                }`}
                        >
                            Salary Trends
                        </button>
                    </div>
                    {/* Subtitle */}
                    <p className="text-xs text-muted-foreground mt-2">
                        Top skills from all job listings
                    </p>

                    {/* Legend (Absolute right, hidden on very small screens) */}
                    <div className="absolute right-0 top-0 hidden sm:flex flex-col items-end gap-1">
                        <span className="text-[9px] text-muted-foreground/80 font-medium uppercase tracking-wider">Demand</span>
                        <div className="flex items-center gap-1.5">
                            <span className="text-[10px] text-foreground font-medium">High</span>
                            <div className="h-2.5 w-20 rounded-full" style={{ background: "linear-gradient(to right, #7c4a00, #faeaaa)" }} />
                            <span className="text-[10px] text-muted-foreground">Low</span>
                        </div>
                    </div>
                </div>

                <div className="w-full flex-1">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={skills} layout="vertical" margin={{ left: 0, right: 10, top: 0, bottom: 0 }}>
                            <XAxis type="number" hide />
                            <YAxis
                                type="category" dataKey="name" width={yAxisWidth}
                                tick={{ fontSize: 12, fill: "var(--muted-foreground)" }}
                                interval={0}
                                axisLine={false} tickLine={false}
                            />
                            <Tooltip content={<ChartTooltip />} cursor={{ fill: "var(--accent)", opacity: 0.3 }} />
                            <Bar dataKey="count" radius={[0, 4, 4, 0]} barSize={16}>
                                {skills.map((entry, index) => (
                                    <Cell key={entry.name} fill={getWarmColor(index, skills.length)} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </CardContent>
        </Card>
    );
}

"use client";

import React, { useEffect, useState } from "react";
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ErrorBar
} from "recharts";
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

// ----- Gradient สีฟ้า → ม่วง -----
const SALARY_COLORS = [
    "#7c3aed", "#8b5cf6", "#a78bfa",  // ม่วง (สูงสุด)
    "#6366f1", "#818cf8",              // indigo
    "#3b82f6", "#60a5fa",              // ฟ้า
    "#06b6d4", "#22d3ee",              // cyan
    "#14b8a6", "#2dd4bf",              // teal (ต่ำสุด)
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
    if (value >= 1000) {
        return `฿${(value / 1000).toFixed(0)}k`;
    }
    return `฿${value.toLocaleString()}`;
}

// ----- Custom Tooltip -----
function SalaryTooltip({ active, payload }: any) {
    if (!active || !payload?.[0]) return null;
    const data = payload[0].payload;
    return (
        <div className="bg-popover text-popover-foreground border rounded-lg shadow-lg px-4 py-3">
            <p className="font-bold text-sm">{data.name}</p>
            <div className="mt-1.5 space-y-0.5 text-xs">
                <p className="text-muted-foreground">
                    เฉลี่ย <span className="font-semibold text-foreground">฿{data.avg_salary.toLocaleString()}</span>/เดือน
                </p>
                <p className="text-muted-foreground">
                    ช่วง ฿{data.avg_min.toLocaleString()} – ฿{data.avg_max.toLocaleString()}
                </p>
                <p className="text-muted-foreground">
                    จาก <span className="font-semibold text-foreground">{data.job_count}</span> งาน
                </p>
            </div>
        </div>
    );
}

export default function SalaryTrends() {
    const [skills, setSkills] = useState<SalarySkill[]>([]);
    const [totalJobs, setTotalJobs] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        axios.get(`${process.env.NEXT_PUBLIC_API_URL}/analytics/salary-trends`, { params: { limit: 20 } })
            .then(res => {
                // เพิ่ม errorBar data สำหรับแสดง range
                const enriched = res.data.skills.map((s: SalarySkill) => ({
                    ...s,
                    errorLow: s.avg_salary - s.avg_min,
                    errorHigh: s.avg_max - s.avg_salary,
                }));
                setSkills(enriched);
                setTotalJobs(res.data.total_jobs_with_salary);
            })
            .catch(err => {
                console.error("Salary Trends API Error:", err);
                setError("ไม่สามารถโหลดข้อมูลเงินเดือนได้");
            })
            .finally(() => setLoading(false));
    }, []);

    if (loading) {
        return (
            <Card className="w-full shadow-sm border-border">
                <CardContent className="p-12 flex flex-col items-center justify-center gap-3">
                    <Loader2 className="w-8 h-8 animate-spin text-primary" />
                    <p className="text-muted-foreground text-sm">กำลังโหลดข้อมูลเงินเดือน...</p>
                </CardContent>
            </Card>
        );
    }

    if (error || skills.length === 0) {
        return null;
    }

    return (
        <Card className="w-full shadow-sm border-border overflow-hidden">
            <CardContent className="p-6 md:p-8">
                {/* Header */}
                <div className="mb-6">
                    <h2 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2.5">
                        <DollarSign className="w-6 h-6 text-violet-500" />
                        Salary Trends by Skill
                    </h2>
                    <p className="text-muted-foreground mt-1.5 text-sm">
                        เงินเดือนเฉลี่ยต่อ Skill จากงานที่เปิดเผยเงินเดือน <span className="font-semibold text-foreground">{totalJobs}</span> ตำแหน่ง
                    </p>
                </div>

                {/* Bar Chart */}
                <div className="w-full h-[620px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                            data={skills}
                            layout="vertical"
                            margin={{ left: 10, right: 40, top: 5, bottom: 5 }}
                        >
                            <XAxis
                                type="number"
                                tickFormatter={formatSalary}
                                tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
                                axisLine={false}
                                tickLine={false}
                            />
                            <YAxis
                                type="category"
                                dataKey="name"
                                width={130}
                                tick={{ fontSize: 13, fill: "var(--foreground)" }}
                                axisLine={false}
                                tickLine={false}
                            />
                            <Tooltip content={<SalaryTooltip />} cursor={{ fill: "var(--accent)", opacity: 0.5 }} />
                            <Bar dataKey="avg_salary" radius={[0, 8, 8, 0]} barSize={20}>
                                {skills.map((entry, index) => (
                                    <Cell
                                        key={entry.name}
                                        fill={getSalaryColor(index, skills.length)}
                                        style={{ filter: "drop-shadow(0 1px 3px rgba(0,0,0,0.12))" }}
                                    />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                {/* Footer note */}
                <p className="text-xs text-muted-foreground text-center mt-2">
                    * แสดงเฉพาะ Skills ที่มีข้อมูลเงินเดือนอย่างน้อย 3 งาน | เส้นขีดแสดงช่วงเงินเดือนเฉลี่ย (min–max)
                </p>
            </CardContent>
        </Card>
    );
}

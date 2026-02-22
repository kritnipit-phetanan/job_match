"use client";

import React, { useEffect, useState } from "react";
import {
    Treemap, ResponsiveContainer, Tooltip,
    BarChart, Bar, XAxis, YAxis, Cell
} from "recharts";
import { Card, CardContent } from "@/components/ui/card";
import { Loader2, Flame, TrendingUp } from "lucide-react";
import axios from "axios";

interface SkillData {
    name: string;
    count: number;
}

// ----- Color Palette (เขียว → เหลือง → ส้ม → แดง ตามความร้อน) -----
const HEATMAP_COLORS = [
    "#22c55e", "#4ade80", "#86efac",  // เขียว (cold)
    "#facc15", "#eab308", "#f59e0b",  // เหลือง-ส้ม (warm)
    "#f97316", "#ef4444", "#dc2626",  // แดง (hot)
    "#b91c1c",                         // แดงเข้ม (hottest)
];

function getHeatColor(index: number, total: number): string {
    // index 0 = hot สุด (count สูงสุด) → สีแดง
    const ratio = index / Math.max(total - 1, 1);
    const colorIndex = Math.min(
        Math.floor(ratio * HEATMAP_COLORS.length),
        HEATMAP_COLORS.length - 1
    );
    // Reverse: อันดับ 1 = สีแดง, อันดับสุดท้าย = สีเขียว
    return HEATMAP_COLORS[HEATMAP_COLORS.length - 1 - colorIndex];
}

// ----- Custom Treemap Cell Content -----
function TreemapCell(props: any) {
    const { x, y, width, height, name, count } = props;
    if (width < 30 || height < 20) return null; // ซ่อน cell เล็กเกินไป

    return (
        <g>
            <rect
                x={x} y={y} width={width} height={height}
                rx={6} ry={6}
                style={{ fill: props.fill, stroke: "rgba(255,255,255,0.3)", strokeWidth: 1.5 }}
            />
            {width > 50 && height > 35 && (
                <>
                    <text
                        x={x + width / 2} y={y + height / 2 - 6}
                        textAnchor="middle" dominantBaseline="central"
                        className="fill-white font-semibold drop-shadow-sm"
                        style={{ fontSize: Math.min(14, width / 6) }}
                    >
                        {name}
                    </text>
                    <text
                        x={x + width / 2} y={y + height / 2 + 12}
                        textAnchor="middle" dominantBaseline="central"
                        className="fill-white/80"
                        style={{ fontSize: Math.min(11, width / 8) }}
                    >
                        {count} งาน
                    </text>
                </>
            )}
        </g>
    );
}

// ----- Custom Tooltip -----
function HeatmapTooltip({ active, payload }: any) {
    if (!active || !payload?.[0]) return null;
    const data = payload[0].payload;
    return (
        <div className="bg-popover text-popover-foreground border rounded-lg shadow-lg px-4 py-2.5">
            <p className="font-bold text-sm">{data.name || data.root?.name}</p>
            <p className="text-xs text-muted-foreground mt-0.5">
                ปรากฏใน <span className="font-semibold text-foreground">{data.count ?? data.value}</span> งาน
            </p>
        </div>
    );
}

export default function SkillHeatmap() {
    const [skills, setSkills] = useState<SkillData[]>([]);
    const [totalJobs, setTotalJobs] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        axios.get(`${process.env.NEXT_PUBLIC_API_URL}/analytics/hot-skills`, { params: { limit: 30 } })
            .then(res => {
                setSkills(res.data.skills);
                setTotalJobs(res.data.total_jobs);
            })
            .catch(err => {
                console.error("Hot Skills API Error:", err);
                setError("ไม่สามารถโหลดข้อมูล Hot Skills ได้");
            })
            .finally(() => setLoading(false));
    }, []);

    if (loading) {
        return (
            <Card className="w-full shadow-sm border-border">
                <CardContent className="p-12 flex flex-col items-center justify-center gap-3">
                    <Loader2 className="w-8 h-8 animate-spin text-primary" />
                    <p className="text-muted-foreground text-sm">กำลังโหลดข้อมูลตลาดแรงงาน...</p>
                </CardContent>
            </Card>
        );
    }

    if (error || skills.length === 0) {
        return null; // ซ่อนถ้าไม่มีข้อมูล
    }

    // เตรียมข้อมูลสำหรับ Treemap (ต้องมี field `size`)
    const treemapData = skills.map((s, i) => ({
        name: s.name,
        size: s.count,
        count: s.count,
        fill: getHeatColor(i, skills.length),
    }));

    // Bar chart: top 15
    const barData = skills.slice(0, 15);
    const maxCount = barData[0]?.count || 1;

    return (
        <Card className="w-full shadow-sm border-border overflow-hidden">
            <CardContent className="p-6 md:p-8">
                {/* Header */}
                <div className="mb-6">
                    <h2 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2.5">
                        <Flame className="w-6 h-6 text-orange-500" />
                        Market Demand Heatmap
                    </h2>
                    <p className="text-muted-foreground mt-1.5 text-sm">
                        Hot Skills ที่ตลาดต้องการมากที่สุดจากงานทั้งหมด <span className="font-semibold text-foreground">{totalJobs}</span> ตำแหน่ง
                    </p>
                </div>

                {/* Treemap */}
                <div className="mb-8">
                    <h3 className="text-sm font-semibold text-muted-foreground mb-3 flex items-center gap-1.5">
                        📊 Skill Demand Map — ยิ่งช่องใหญ่ ยิ่งเป็นที่ต้องการ
                    </h3>
                    <div className="w-full h-[280px] md:h-[340px] rounded-xl overflow-hidden border bg-secondary/20">
                        <ResponsiveContainer width="100%" height="100%">
                            <Treemap
                                data={treemapData}
                                dataKey="size"
                                aspectRatio={4 / 3}
                                stroke="none"
                                content={<TreemapCell />}
                            >
                                <Tooltip content={<HeatmapTooltip />} />
                            </Treemap>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Horizontal Bar Chart */}
                <div>
                    <h3 className="text-sm font-semibold text-muted-foreground mb-3 flex items-center gap-1.5">
                        <TrendingUp className="w-4 h-4" /> Top 15 Skills — เรียงตามจำนวนงาน
                    </h3>
                    <div className="w-full h-[480px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={barData} layout="vertical" margin={{ left: 10, right: 30, top: 5, bottom: 5 }}>
                                <XAxis type="number" hide />
                                <YAxis
                                    type="category" dataKey="name" width={120}
                                    tick={{ fontSize: 13, fill: "var(--foreground)" }}
                                    axisLine={false} tickLine={false}
                                />
                                <Tooltip content={<HeatmapTooltip />} />
                                <Bar dataKey="count" radius={[0, 6, 6, 0]} barSize={22}>
                                    {barData.map((entry, index) => (
                                        <Cell
                                            key={entry.name}
                                            fill={getHeatColor(index, barData.length)}
                                            style={{ filter: "drop-shadow(0 1px 2px rgba(0,0,0,0.15))" }}
                                        />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Legend */}
                <div className="mt-4 flex items-center justify-center gap-2 text-xs text-muted-foreground">
                    <span className="inline-block w-3 h-3 rounded-sm bg-[#22c55e]" /> น้อย
                    <span className="inline-block w-3 h-3 rounded-sm bg-[#facc15]" /> ปานกลาง
                    <span className="inline-block w-3 h-3 rounded-sm bg-[#ef4444]" /> มาก
                    <span className="inline-block w-3 h-3 rounded-sm bg-[#b91c1c]" /> มากที่สุด 🔥
                </div>
            </CardContent>
        </Card>
    );
}

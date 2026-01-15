"use client";

import React, { useState, useEffect } from 'react';
import { APP_API_URL } from '../../config';

interface DataPoint {
    name: string;
    score: number;
    severity: string;
    timestamp: string;
}

export default function NucleusWellnessChart() {
    const [sessionId, setSessionId] = useState("test-session-1"); // Default for dev
    const [metric, setMetric] = useState<"gad7" | "phq9">("gad7");
    const [data, setData] = useState<DataPoint[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const maxScore = metric === "gad7" ? 21 : 27; // PHQ-9 is 27
    const height = 200;
    const width = 600;

    useEffect(() => {
        if (!sessionId) return;
        fetchData();
    }, [sessionId, metric]);

    const fetchData = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`${APP_API_URL}/api/assessment/history?session_id=${sessionId}`);
            const json = await res.json();

            if (json.success === false) {
                // Don't error immediately on empty history, just show empty
                if (json.error === "session_id required") setError("Please enter Session ID");
                else setData([]); // Assume no data if error isn't specific
                return;
            }

            // Filter by selected metric and transform
            // API returns: [{ type: "gad7", score: 10, timestamp: "..." }]
            // We need to reverse chart (oldest left, newest right)
            const filtered = json
                .filter((item: any) => item.type === metric)
                .sort((a: any, b: any) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
                .map((item: any) => ({
                    name: new Date(item.timestamp).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
                    score: item.score,
                    severity: item.severity,
                    timestamp: item.timestamp
                }));

            // If empty, add a placeholder or keep empty
            setData(filtered);

        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    // Calculate SVG points
    const points = data.length > 0 ? data.map((d, i) => {
        const x = (i / (data.length - 1 || 1)) * width; // Avoid div by zero
        const y = height - (d.score / maxScore) * height;
        return `${x},${y}`;
    }).join(' ') : "";

    const currentScore = data.length > 0 ? data[data.length - 1].score : 0;
    const currentSeverity = data.length > 0 ? data[data.length - 1].severity : "NO_DATA";

    return (
        <div className="p-6 border border-green-500/30 bg-black/40 rounded-lg backdrop-blur-sm shadow-[0_0_15px_rgba(0,255,65,0.1)] font-mono transaction-all duration-300">
            {/* Header / Controls */}
            <div className="flex justify-between items-start mb-6 gap-4">
                <div>
                    <h2 className="text-xl font-bold text-green-400 flex items-center gap-2">
                        OUTCOME_TRACKING
                        <select
                            value={metric}
                            onChange={(e) => setMetric(e.target.value as any)}
                            className="bg-black/50 border border-green-500/30 text-xs text-green-500 px-2 py-1 rounded focus:outline-none focus:border-green-400"
                        >
                            <option value="gad7">GAD-7 (ANXIETY)</option>
                            <option value="phq9">PHQ-9 (DEPRESSION)</option>
                        </select>
                    </h2>
                    <p className="text-xs text-green-500/60 mt-1 flex items-center gap-2">
                        STATUS: {currentSeverity}
                        {loading && <span className="animate-pulse text-green-400"> // SYNCING...</span>}
                    </p>
                </div>

                <div className="flex flex-col items-end gap-2">
                    <div className="text-right">
                        <span className="text-3xl font-bold text-green-500">{currentScore}</span>
                        <span className="text-xs text-green-600 block">CURRENT</span>
                    </div>
                    <input
                        type="text"
                        value={sessionId}
                        onChange={(e) => setSessionId(e.target.value)}
                        placeholder="SESSION_ID"
                        className="bg-black/30 border border-green-900/50 text-right text-[10px] text-green-500/50 focus:text-green-400 focus:border-green-500/50 w-32 p-1 rounded transition-colors"
                    />
                </div>
            </div>

            {/* Error State */}
            {error && (
                <div className="h-[200px] flex items-center justify-center text-red-500 text-xs border border-red-900/30 bg-red-900/10 rounded">
                    ERROR: {error}
                </div>
            )}

            {/* Chart Area */}
            {!error && (
                <div className="relative h-[200px] w-full overflow-hidden">
                    {/* Grid Lines */}
                    <div className="absolute inset-0 border-l border-b border-green-500/20"></div>
                    {[0, maxScore * 0.33, maxScore * 0.66, maxScore].map((score) => (
                        <div key={score} className="absolute w-full border-t border-green-500/10 text-[10px] text-green-500/30"
                            style={{ bottom: `${(score / maxScore) * 100}%` }}>
                            <span className="ml-1">{Math.round(score)}</span>
                        </div>
                    ))}

                    {data.length === 0 ? (
                        <div className="absolute inset-0 flex items-center justify-center text-green-500/20 text-sm">
                            NO DATA POINTS FOUND
                        </div>
                    ) : (
                        <svg
                            viewBox={`0 0 ${width} ${height}`}
                            className="w-full h-full overflow-visible"
                            role="img"
                            aria-label={`Line chart showing ${metric} scores`}
                        >
                            <linearGradient id={`${metric}-gradient`} x1="0" x2="0" y1="0" y2="1">
                                <stop offset="0%" stopColor="#00FF41" stopOpacity="0.2" />
                                <stop offset="100%" stopColor="#00FF41" stopOpacity="0" />
                            </linearGradient>

                            {data.length > 1 && (
                                <>
                                    <path
                                        d={`M0,${height} ${points} L${width},${height} Z`}
                                        fill={`url(#${metric}-gradient)`}
                                    />
                                    <polyline
                                        fill="none"
                                        stroke="#00FF41"
                                        strokeWidth="2"
                                        points={points}
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        className="drop-shadow-[0_0_5px_rgba(0,255,65,0.5)]"
                                    />
                                </>
                            )}

                            {/* Data Points */}
                            {data.map((d, i) => {
                                const x = (i / (data.length - 1 || 1)) * width;
                                const y = height - (d.score / maxScore) * height;
                                return (
                                    <circle key={i} cx={x} cy={y} r="4" fill="#000" stroke="#00FF41" strokeWidth="2"
                                        className="cursor-pointer hover:r-6 transition-all"
                                    >
                                        <title>{d.timestamp}: {d.score} ({d.severity})</title>
                                    </circle>
                                );
                            })}
                        </svg>
                    )}
                </div>
            )}

            {/* X-Axis Labels */}
            <div className="flex justify-between mt-2 text-[10px] text-green-500/40">
                {data.length > 0 && data.map((d, i) => (
                    <span key={i}>{d.name}</span>
                ))}
            </div>
        </div>
    );
}

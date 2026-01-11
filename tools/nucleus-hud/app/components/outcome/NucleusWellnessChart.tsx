
"use client";

import React from 'react';

// Data model matching Generic Task
const data = [
    { name: 'Week 1', gad7: 12 },
    { name: 'Week 2', gad7: 10 },
    { name: 'Week 3', gad7: 8 },
    { name: 'Week 4', gad7: 5 },
];

export default function NucleusWellnessChart() {
    const maxScore = 21; // GAD-7 Max
    const height = 200;
    const width = 600;

    // Calculate SVG points
    const points = data.map((d, i) => {
        const x = (i / (data.length - 1)) * width;
        const y = height - (d.gad7 / maxScore) * height;
        return `${x},${y}`;
    }).join(' ');

    return (
        <div className="p-6 border border-green-500/30 bg-black/40 rounded-lg backdrop-blur-sm shadow-[0_0_15px_rgba(0,255,65,0.1)] font-mono">
            <div className="flex justify-between items-end mb-6">
                <div>
                    <h2 className="text-xl font-bold text-green-400">ANXIETY_INDEX <span className="text-xs text-green-600">[GAD-7]</span></h2>
                    <p className="text-xs text-green-500/60 mt-1">STATUS: IMPROVING</p>
                </div>
                <div className="text-right">
                    <span className="text-3xl font-bold text-green-500">{data[data.length - 1].gad7}</span>
                    <span className="text-xs text-green-600 block">CURRENT</span>
                </div>
            </div>

            <div className="relative h-[200px] w-full overflow-hidden">
                {/* Grid Lines */}
                <div className="absolute inset-0 border-l border-b border-green-500/20"></div>
                {[0, 7, 14, 21].map((score) => (
                    <div key={score} className="absolute w-full border-t border-green-500/10 text-[10px] text-green-500/30"
                        style={{ bottom: `${(score / maxScore) * 100}%` }}>
                        <span className="ml-1">{score}</span>
                    </div>
                ))}

                {/* SVG Chart */}
                <svg
                    viewBox={`0 0 ${width} ${height}`}
                    className="w-full h-full overflow-visible"
                    role="img"
                    aria-label="Line chart showing GAD-7 anxiety scores decreasing from 12 to 5 over 4 weeks"
                >
                    {/* Area Gradient */}
                    <linearGradient id="gradient" x1="0" x2="0" y1="0" y2="1">
                        <stop offset="0%" stopColor="#00FF41" stopOpacity="0.2" />
                        <stop offset="100%" stopColor="#00FF41" stopOpacity="0" />
                    </linearGradient>

                    <path
                        d={`M0,${height} ${points} L${width},${height} Z`}
                        fill="url(#gradient)"
                    />

                    <polyline
                        fill="none"
                        stroke="#00FF41"
                        strokeWidth="2"
                        points={points}
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    />

                    {/* Data Points */}
                    {data.map((d, i) => {
                        const x = (i / (data.length - 1)) * width;
                        const y = height - (d.gad7 / maxScore) * height;
                        return (
                            <circle key={i} cx={x} cy={y} r="4" fill="#000" stroke="#00FF41" strokeWidth="2" />
                        );
                    })}
                </svg>
            </div>

            {/* X-Axis Labels */}
            <div className="flex justify-between mt-2 text-xs text-green-500/50">
                {data.map((d) => <span key={d.name}>{d.name}</span>)}
            </div>
        </div>
    );
}

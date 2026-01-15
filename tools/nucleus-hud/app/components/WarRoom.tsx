"use client";

import { useState } from 'react';

export default function WarRoom() {
    const [proposition, setProposition] = useState("");
    const [simulating, setSimulating] = useState(false);
    const [result, setResult] = useState<any>(null);

    const runSimulation = async () => {
        if (!proposition.trim()) return;
        setSimulating(true);
        setResult(null);

        try {
            const res = await fetch('/api/oracle/simulate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ proposition })
            });
            const data = await res.json();
            setResult(data);
        } catch (e) {
            console.error(e);
            setResult({ verdict: "ERROR", critique: "Communication with Nucleus failed." });
        } finally {
            setSimulating(false);
        }
    };

    return (
        <div className="mt-6 p-6 rounded-lg bg-black/80 border border-green-500/20 backdrop-blur-xl relative overflow-hidden group">
            {/* Background Decor */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-green-500/5 rounded-full blur-[100px] pointer-events-none"></div>

            <div className="relative z-10">
                <h3 className="text-green-500 font-mono text-sm tracking-[0.2em] mb-4 flex items-center gap-2">
                    <span className="text-lg">⚔️</span>
                    WAR ROOM // ADVERSARIAL SIMULATION
                </h3>

                <div className="flex gap-4 mb-6">
                    <textarea
                        value={proposition}
                        onChange={(e) => setProposition(e.target.value)}
                        placeholder="Enter strategic proposition for simulation..."
                        className="flex-1 bg-black/50 border border-green-900/50 rounded p-4 text-green-100 font-serif italic focus:border-green-500/50 focus:outline-none focus:ring-1 focus:ring-green-500/20 transition-all h-24 resize-none placeholder:text-green-900"
                    />
                    <button
                        onClick={runSimulation}
                        disabled={simulating || !proposition}
                        className="px-6 rounded border border-green-500/30 bg-green-900/10 hover:bg-green-500/20 hover:border-green-500 text-green-400 font-mono text-sm tracking-wider uppercase transition-all disabled:opacity-50 disabled:cursor-not-allowed group-hover:shadow-[0_0_20px_rgba(74,222,128,0.1)]"
                    >
                        {simulating ? (
                            <span className="flex items-center gap-2">
                                <span className="w-2 h-2 bg-green-500 rounded-full animate-ping"></span>
                                SIMULATING...
                            </span>
                        ) : (
                            "RUN\nSIMULATION"
                        )}
                    </button>
                </div>

                {result && (
                    <div className="animate-in fade-in slide-in-from-top-4 border-t border-green-900/50 pt-4">
                        <div className="flex items-center gap-4 mb-2">
                            <span className="text-xs text-green-600 font-mono uppercase">Verdict</span>
                            <span className={`text-xl font-bold font-mono ${result.verdict.includes('KILL') ? 'text-red-500' : 'text-green-400'}`}>
                                {result.verdict}
                            </span>
                        </div>
                        <p className="text-sm text-green-400/80 font-mono leading-relaxed border-l-2 border-green-900/50 pl-4">
                            {result.critique}
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}

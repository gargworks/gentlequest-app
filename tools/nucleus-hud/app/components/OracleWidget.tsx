"use client";

import { useState, useEffect } from 'react';

interface Decision {
    timestamp: string;
    proposition: string;
    verdict: string;
    critique: string;
}

export default function OracleWidget() {
    const [decision, setDecision] = useState<Decision | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchDecision = async () => {
            try {
                const res = await fetch('/api/oracle/decisions');
                if (res.ok) {
                    const data = await res.json();
                    if (data.decision) {
                        setDecision(data.decision);
                    }
                }
            } catch (e) {
                console.error("Oracle Fetch Error", e);
            } finally {
                setLoading(false);
            }
        };

        fetchDecision();
        const interval = setInterval(fetchDecision, 5000);
        return () => clearInterval(interval);
    }, []);

    if (loading) return <div className="animate-pulse h-32 bg-green-900/10 rounded-lg border border-green-900/30"></div>;

    if (!decision) {
        return (
            <div className="p-4 rounded-lg bg-black/40 border border-green-900/30 backdrop-blur">
                <h3 className="text-green-500 font-mono text-sm tracking-widest mb-2 flex items-center gap-2">
                    <span className="w-2 h-2 bg-green-900 rounded-full"></span>
                    ORACLE // IDLE
                </h3>
                <p className="text-green-400/50 text-xs font-mono">No strategic simulations recorded.</p>
            </div>
        );
    }

    const isKill = decision.verdict.includes("KILL") || decision.verdict.includes("FAIL");
    const isProceed = decision.verdict.includes("PROCEED") || decision.verdict.includes("PASS");

    const verdictColor = isKill ? "text-red-500" : (isProceed ? "text-green-400" : "text-yellow-500");
    const borderColor = isKill ? "border-red-900/30" : (isProceed ? "border-green-500/30" : "border-yellow-900/30");
    const bgGlow = isKill ? "shadow-[0_0_15px_rgba(239,68,68,0.1)]" : (isProceed ? "shadow-[0_0_15px_rgba(74,222,128,0.1)]" : "");

    return (
        <div className={`p-4 rounded-lg bg-black/60 border ${borderColor} backdrop-blur ${bgGlow} transition-all duration-500`}>
            <div className="flex justify-between items-start mb-3">
                <h3 className="text-green-500 font-mono text-sm tracking-widest flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${isKill ? 'bg-red-500 animate-pulse' : 'bg-green-500 animate-pulse'}`}></span>
                    ORACLE // LATEST VERDICT
                </h3>
                <span className="text-xs font-mono text-green-700/50">{new Date(decision.timestamp).toLocaleDateString()}</span>
            </div>

            <div className="mb-4">
                <p className="text-xs text-green-600 font-mono uppercase mb-1">Proposition</p>
                <p className="text-sm text-green-100/90 font-serif italic leading-relaxed">"{decision.proposition}"</p>
            </div>

            <div className="border-t border-green-900/30 pt-3">
                <div className="flex justify-between items-center">
                    <span className="text-xs text-green-600 font-mono uppercase">Consensus</span>
                    <span className={`text-lg font-bold font-mono tracking-tighter ${verdictColor} animate-in fade-in slide-in-from-bottom-2`}>
                        {decision.verdict}
                    </span>
                </div>
            </div>
        </div>
    );
}

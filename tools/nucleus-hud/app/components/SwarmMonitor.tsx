
"use client";

import { useEffect, useState } from "react";
import { API_URL } from "../config";

interface SwarmPlan {
    session_id: string;
    mission: string;
    status: string;
    agents: string[];
}

export default function SwarmMonitor() {
    const [swarms, setSwarms] = useState<SwarmPlan[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchSwarms = () => {
            fetch(`${API_URL}/api/swarms`)
                .then((res) => res.json())
                .then((data) => {
                    if (data.swarms) {
                        setSwarms(data.swarms);
                    }
                })
                .catch((err) => console.error("Failed to load swarms", err))
                .finally(() => setLoading(false));
        };

        fetchSwarms();
        const interval = setInterval(fetchSwarms, 5000); // Poll every 5s

        return () => clearInterval(interval);
    }, []);

    return (
        <div className="bg-black/40 border border-green-500/20 p-6 rounded-xl backdrop-blur-sm">
            <h2 className="text-xl font-bold mb-4 font-mono text-green-400 flex items-center gap-2">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                ACTIVE SWARMS
            </h2>

            {loading && swarms.length === 0 ? (
                <div className="text-green-500/50 font-mono animate-pulse">Scanning neural network...</div>
            ) : swarms.length === 0 ? (
                <div className="text-green-500/30 font-mono italic">No active swarms detected. System dormant.</div>
            ) : (
                <div className="space-y-4">
                    {swarms.map((swarm) => (
                        <div
                            key={swarm.session_id}
                            className="border border-green-500/30 bg-green-900/10 p-4 rounded-lg hover:border-green-500/60 transition-colors"
                        >
                            <div className="flex justify-between items-start mb-2">
                                <span className="text-xs text-green-500/50 font-mono">{swarm.session_id}</span>
                                <span className="px-2 py-0.5 rounded text-xs bg-green-500/20 text-green-300 font-mono uppercase">
                                    {swarm.status}
                                </span>
                            </div>

                            <div className="font-bold text-green-100 mb-2">{swarm.mission}</div>

                            <div className="flex gap-2">
                                {swarm.agents.map((agent) => (
                                    <span
                                        key={agent}
                                        className="px-2 py-1 rounded bg-blue-500/10 text-blue-300 border border-blue-500/20 text-xs font-mono"
                                    >
                                        @{agent}
                                    </span>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

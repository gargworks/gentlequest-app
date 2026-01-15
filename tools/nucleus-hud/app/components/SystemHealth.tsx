"use client";

import { useState, useEffect } from 'react';

interface PulseData {
    status: string;
    timestamp: string;
    uptime?: number;
    version?: string;
    cpu?: number;
    memory?: number;
    agent_count?: number;
}

export default function SystemHealth() {
    const [pulse, setPulse] = useState<PulseData | null>(null);
    const [error, setError] = useState<boolean>(false);

    useEffect(() => {
        const fetchStatus = async () => {
            try {
                // Fetch from our local Next.js API route which reads .brain/pulse.json
                const res = await fetch('/api/status');
                if (res.ok) {
                    const data = await res.json();
                    setPulse(data);
                    setError(false);
                } else {
                    setError(true);
                }
            } catch (e) {
                setError(true);
            }
        };

        fetchStatus();
        const interval = setInterval(fetchStatus, 2000); // Poll every 2 seconds
        return () => clearInterval(interval);
    }, []);

    if (error) {
        return (
            <div className="flex items-center space-x-2 text-red-500">
                <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
                <span className="text-xs font-mono uppercase tracking-wider">DISCONNECTED</span>
            </div>
        );
    }

    if (!pulse) {
        return (
            <div className="flex items-center space-x-2 text-gray-500">
                <div className="w-3 h-3 bg-gray-500 rounded-full" />
                <span className="text-xs font-mono uppercase tracking-wider">SYNCING...</span>
            </div>
        );
    }

    return (
        <div className="flex items-center gap-4 text-green-500 font-mono text-xs">
            <div className="flex items-center space-x-2" title={`Last Beat: ${new Date(pulse.timestamp).toLocaleTimeString()}`}>
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.6)]" />
                <span className="uppercase tracking-wider font-bold">ONLINE</span>
            </div>

            {/* Extended Metrics */}
            {pulse.cpu && (
                <div className="flex items-center gap-1 text-green-400/80">
                    <span>CPU:</span>
                    <span className="text-green-300">{pulse.cpu}%</span>
                </div>
            )}

            {pulse.memory && (
                <div className="flex items-center gap-1 text-green-400/80">
                    <span>MEM:</span>
                    <span className="text-green-300">{pulse.memory}%</span>
                </div>
            )}

            {pulse.agent_count !== undefined && (
                <div className="flex items-center gap-1 text-green-400/80">
                    <span>AGENTS:</span>
                    <span className="text-green-300">{pulse.agent_count}</span>
                </div>
            )}
        </div>
    );
}

"use client";

import { useState } from 'react';
import { API_URL } from '../config';
import { useVoice } from '../hooks/useVoice';

export default function ResearchWidget() {
    const [topic, setTopic] = useState('');
    const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
    const [message, setMessage] = useState('');
    const { speak } = useVoice();
    const [autopilot, setAutopilot] = useState(false);

    const [activeTab, setActiveTab] = useState<'research' | 'critique'>('research');
    const [critiqueResult, setCritiqueResult] = useState<any>(null);

    const toggleAutopilot = async () => {
        const newState = !autopilot;
        try {
            const res = await fetch(`${API_URL}/api/autopilot`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ active: newState })
            });
            if (res.ok) {
                setAutopilot(newState);
            }
        } catch (e) {
            console.error("Autopilot toggle failed", e);
        }
    };

    const handleIgnite = async () => {
        if (!topic.trim()) return;

        setStatus('loading');
        setCritiqueResult(null);

        if (activeTab === 'critique') {
            try {
                const res = await fetch(`${API_URL}/api/critique`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ file_path: topic }),
                });

                const data = await res.json();
                if (res.ok) {
                    setStatus('success');
                    setCritiqueResult(data);
                    speak(`Critique complete. File score: ${data.score || 0}`);
                } else {
                    setStatus('error');
                    setMessage(data.error || 'Critique Failed');
                }
            } catch (e) {
                setStatus('error');
                setMessage('Connection Failed');
            }
            return;
        }

        try {
            const res = await fetch(`${API_URL}/api/research`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic }),
            });

            const data = await res.json();

            if (res.ok) {
                setStatus('success');
                setMessage(data.message);
                setTopic('');
                speak(`Mission Ignited. Researcher dispatched for ${topic}`);
                setTimeout(() => setStatus('idle'), 3000);
            } else {
                setStatus('error');
                setMessage(data.error || 'Mission Failed');
                speak('Mission Failed.');
            }
        } catch (e) {
            setStatus('error');
            setMessage('Connection Failed');
            speak('Connection Failed.');
        }
    };

    return (
        <div className="border border-green-900/30 bg-black/40 p-6 rounded-xl backdrop-blur-sm relative overflow-hidden group">
            {/* Decorative corners */}
            <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-green-500/50" />
            <div className="absolute top-0 right-0 w-2 h-2 border-t border-r border-green-500/50" />
            <div className="absolute bottom-0 left-0 w-2 h-2 border-b border-l border-green-500/50" />
            <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-green-500/50" />

            <div className="flex justify-between items-center mb-4">
                <div className="flex items-center gap-4">
                    <button
                        onClick={() => setActiveTab('research')}
                        className={`text-xs font-bold tracking-widest flex items-center gap-2 ${activeTab === 'research' ? 'text-green-500' : 'text-zinc-600 hover:text-green-400'}`}
                    >
                        {activeTab === 'research' && <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />}
                        WEBOPS
                    </button>
                    <button
                        onClick={() => setActiveTab('critique')}
                        className={`text-xs font-bold tracking-widest flex items-center gap-2 ${activeTab === 'critique' ? 'text-amber-500' : 'text-zinc-600 hover:text-amber-400'}`}
                    >
                        {activeTab === 'critique' && <span className="w-2 h-2 bg-amber-500 rounded-full animate-pulse" />}
                        CRITIC
                    </button>
                </div>

                <button
                    onClick={toggleAutopilot}
                    className={`text-[10px] px-2 py-1 rounded border transition-colors font-mono uppercase tracking-wider ${autopilot
                        ? "bg-green-500/20 border-green-500 text-green-400 animate-pulse"
                        : "bg-black/40 border-zinc-800 text-zinc-600 hover:text-green-500"
                        }`}
                >
                    {autopilot ? "AUTOPILOT ENGAGED" : "ENABLE AUTOPILOT"}
                </button>
            </div>

            <div className="space-y-3">
                <div className="relative">
                    <input
                        type="text"
                        value={topic}
                        onChange={(e) => setTopic(e.target.value)}
                        placeholder={activeTab === 'critique' ? "Enter absolute file path to critique..." : "Enter Mission Target..."}
                        className={`w-full bg-black/50 border rounded px-3 py-2 text-sm placeholder-opacity-50 focus:outline-none transition-colors font-mono ${activeTab === 'critique'
                                ? 'border-amber-900/50 text-amber-100 placeholder-amber-900 focus:border-amber-500'
                                : 'border-green-900/50 text-green-100 placeholder-green-900 focus:border-green-500'
                            }`}
                        disabled={status === 'loading'}
                        onKeyDown={(e) => e.key === 'Enter' && handleIgnite()}
                    />
                </div>

                <button
                    onClick={handleIgnite}
                    disabled={status === 'loading' || !topic.trim()}
                    className={`w-full py-2 rounded text-xs font-bold tracking-widest uppercase transition-all
                        ${status === 'loading'
                            ? 'bg-zinc-800 text-zinc-500 cursor-wait'
                            : activeTab === 'critique'
                                ? 'bg-amber-900/40 text-amber-500 border border-amber-900/50 hover:bg-amber-900/60 hover:border-amber-500'
                                : 'bg-green-900/20 text-green-500 border border-green-900/30 hover:bg-green-900/40 hover:border-green-500'
                        }`}
                >
                    {status === 'loading' ? 'PROCESSING...' : activeTab === 'critique' ? 'INITIALIZE CRITIQUE' : 'IGNITE MISSION'}
                </button>

                {status === 'error' && (
                    <div className="text-red-500 text-xs font-mono text-center mt-2 animate-pulse">
                        ⚠ {message}
                    </div>
                )}

                {status === 'success' && activeTab === 'research' && (
                    <div className="text-green-500 text-xs font-mono text-center mt-2">
                        ✓ {message}
                    </div>
                )}

                {critiqueResult && (
                    <div className="mt-4 p-3 bg-black/60 border border-amber-900/50 rounded text-xs font-mono max-h-60 overflow-y-auto">
                        <div className="flex justify-between mb-2 border-b border-amber-900/30 pb-1">
                            <span className={critiqueResult.status === 'FAIL' ? 'text-red-500 font-bold' : 'text-amber-500'}>
                                STATUS: {critiqueResult.status}
                            </span>
                            <span className="text-zinc-400">SCORE: {critiqueResult.score}/100</span>
                        </div>
                        <ul className="space-y-2">
                            {critiqueResult.issues?.map((issue: any, i: number) => (
                                <li key={i} className="flex gap-2 text-zinc-300">
                                    <span className={issue.severity === 'CRITICAL' ? 'text-red-500' : 'text-amber-500'}>[{issue.severity}]</span>
                                    <span>{issue.message}</span>
                                </li>
                            ))}
                            {(!critiqueResult.issues || critiqueResult.issues.length === 0) && (
                                <li className="text-green-500">No issues found. Clean code.</li>
                            )}
                        </ul>
                    </div>
                )}
            </div>
        </div>
    );
}


"use client";

import { useEffect, useState, useRef } from "react";
import { API_URL } from "../config";

interface NucleusEvent {
    event_id: string;
    timestamp: string;
    emitter: string;
    event_type: string;
    severity: string;
    payload: any;
}

export default function EventStream() {
    const [events, setEvents] = useState<NucleusEvent[]>([]);
    const [status, setStatus] = useState<"connecting" | "live" | "offline">("connecting");
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        // SSE Connection to Nucleus Server
        const eventSource = new EventSource(`${API_URL}/api/events`);

        eventSource.onopen = () => {
            setStatus("live");
        };

        eventSource.onmessage = (e) => {
            try {
                const raw = JSON.parse(e.data);
                if (raw.error) {
                    console.error("Stream Error:", raw.error);
                    return;
                }

                const newEvent: NucleusEvent = typeof raw === 'string' ? JSON.parse(raw) : raw;

                setEvents((prev) => {
                    // Keep max 50 events for performance
                    const updated = [...prev, newEvent];
                    return updated.slice(-50);
                });

            } catch (err) {
                console.error("Parse Error:", err);
            }
        };

        eventSource.onerror = () => {
            setStatus("offline");
            eventSource.close();
            // Auto-retry in 5s handled by browser usually, but we can force re-mount or let user manual refresh
        };

        return () => {
            eventSource.close();
        };
    }, []);

    // Auto-scroll
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [events]);

    return (
        <div className="w-full h-[60vh] bg-black/90 border border-green-900/50 rounded-lg p-4 font-mono text-xs overflow-hidden flex flex-col shadow-[0_0_20px_rgba(0,255,0,0.1)]">
            <div className="flex justify-between items-center border-b border-green-900/30 pb-2 mb-2">
                <h2 className="text-green-500 font-bold uppercase tracking-widest flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${status === 'live' ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></span>
                    Neural Feed
                </h2>
                <span className="text-zinc-600">LIVE // :9999</span>
            </div>

            <div className="flex-1 overflow-y-auto space-y-3 scrollbar-hide">
                {events.length === 0 && (
                    <div className="text-zinc-700 italic text-center mt-20">Waiting for cortical activity...</div>
                )}

                {events.map((evt, i) => (
                    <div key={i} className="group flex gap-3 opacity-80 hover:opacity-100 transition-opacity">
                        <div className="text-zinc-500 w-24 shrink-0 truncate">
                            {evt.timestamp.split('T')[1]?.split('.')[0]}
                        </div>
                        <div className="w-24 shrink-0 text-blue-400 font-bold truncate">
                            {evt.emitter}
                        </div>
                        <div className="flex-1 text-green-400 break-words">
                            <span className="text-zinc-400 mr-2">[{evt.event_type}]</span>
                            {JSON.stringify(evt.payload || {}).slice(0, 100)}
                            {JSON.stringify(evt.payload || {}).length > 100 && "..."}
                        </div>
                    </div>
                ))}
                <div ref={bottomRef} />
            </div>
        </div>
    );
}

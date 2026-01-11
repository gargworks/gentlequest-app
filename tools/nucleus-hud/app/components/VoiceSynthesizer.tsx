"use client";

import { useEffect, useState, useRef } from "react";
import { API_URL } from "../config";

interface NucleusEvent {
    event_id: string;
    timestamp: string;
    emitter: string;
    event_type: string;
    payload: any;
}

export default function VoiceSynthesizer() {
    const [enabled, setEnabled] = useState(false);
    const [speaking, setSpeaking] = useState(false);
    const [lastEventId, setLastEventId] = useState<string | null>(null);
    const synthRef = useRef<SpeechSynthesis | null>(null);

    useEffect(() => {
        if (typeof window !== "undefined") {
            synthRef.current = window.speechSynthesis;
        }
    }, []);

    useEffect(() => {
        if (!enabled) return;

        const eventSource = new EventSource(`${API_URL}/api/events`);

        eventSource.onmessage = (e) => {
            try {
                const raw = JSON.parse(e.data);
                if (raw.error) return;

                const evt: NucleusEvent = typeof raw === 'string' ? JSON.parse(raw) : raw;

                // Dedup
                if (evt.event_id === lastEventId) return;
                setLastEventId(evt.event_id);

                handleEvent(evt);

            } catch (err) {
                // Silent fail
            }
        };

        return () => {
            eventSource.close();
        };
    }, [enabled, lastEventId]);

    const handleEvent = (evt: NucleusEvent) => {
        let textToSpeak = "";

        // 1. Mission Dispatched
        if (evt.emitter === "system" && evt.event_type === "mission_status") {
            if (evt.payload?.status === "sent") {
                textToSpeak = `Mission dispatched. ${evt.payload.mission}`;
            }
            if (evt.payload?.status === "complete") {
                textToSpeak = `Mission complete. ${evt.payload.mission}`;
            }
        }

        // 2. Emergency
        if (evt.event_type === "emergency") {
            textToSpeak = `Alert. ${evt.payload?.message || "unknown emergency"}`;
        }

        // 3. User Message Confirmation (Optional - "Copy that")
        if (evt.event_type === "user_message") {
            // textToSpeak = "Copy that."; // Maybe too chatty?
        }

        // 4. Agent Response (The grail)
        if (evt.event_type === "agent_response") {
            textToSpeak = evt.payload?.response || "";
        }

        if (textToSpeak && synthRef.current) {
            speak(textToSpeak);
        }
    };

    const speak = (text: string) => {
        if (!synthRef.current) return;

        // Cancel current
        synthRef.current.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;

        // Try to find a good sci-fi voice
        const voices = synthRef.current.getVoices();
        // Prefer "Google US English" or "Karen" or similar if available
        const preferred = voices.find(v => v.name.includes("Google US English")) || voices[0];
        if (preferred) utterance.voice = preferred;

        utterance.onstart = () => setSpeaking(true);
        utterance.onend = () => setSpeaking(false);

        synthRef.current.speak(utterance);
    };

    return (
        <button
            onClick={() => setEnabled(!enabled)}
            className={`flex items-center gap-2 px-3 py-1 rounded border transition-all ${enabled
                    ? "bg-green-900/30 border-green-500 text-green-400"
                    : "bg-black/50 border-zinc-800 text-zinc-600 hover:text-zinc-400"
                }`}
        >
            {enabled ? (
                speaking ? (
                    <span className="relative flex h-3 w-3">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                    </span>
                ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4">
                        <path d="M13.5 4.06c0-1.336-1.616-2.005-2.56-1.06l-4.5 4.5H4.508c-1.141 0-2.318.664-2.66 1.905A9.76 9.76 0 001.5 12c0 2.485.586 4.815 1.636 6.874.192.368.618.57 1.002.493l2.812-.562c.49-.098.983-.152 1.487-.152h.58l4.908 4.908c.944.944 2.56.274 2.56-1.06V4.06zM18.81 9.17a3 3 0 010 5.66M21.288 6.692a8 8 0 010 10.618" />
                    </svg>
                )
            ) : (
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4">
                    <path d="M13.5 4.06c0-1.336-1.616-2.005-2.56-1.06l-4.5 4.5H4.508c-1.141 0-2.318.664-2.66 1.905A9.76 9.76 0 001.5 12c0 2.485.586 4.815 1.636 6.874.192.368.618.57 1.002.493l2.812-.562c.49-.098.983-.152 1.487-.152h.58l4.908 4.908c.944.944 2.56.274 2.56-1.06V4.06zM17.75 7.75a.75.75 0 011.06 0l2.25 2.25a.75.75 0 010 1.06l-2.25 2.25a.75.75 0 01-1.06-1.06l.97-1.72-.97-1.72a.75.75 0 010-1.06z" />
                    <path d="M20.25 12l-.97 1.72.97 1.72a.75.75 0 001.06-1.06l-.97-1.72.97-1.72a.75.75 0 00-1.06 1.06z" />
                </svg>
            )}
            <span className="text-xs font-bold tracking-widest uppercase">
                {enabled ? (speaking ? "Active" : "Voice On") : "Voice Off"}
            </span>
        </button>
    );
}

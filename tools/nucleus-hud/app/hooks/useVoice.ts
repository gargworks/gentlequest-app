
"use client";

import { useState, useCallback, useEffect } from 'react';

export const useVoice = () => {
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    const speak = useCallback((text: string) => {
        if (!mounted || !window.speechSynthesis) return;

        // Cancel previous speech to avoid queue buildup
        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.volume = 0.8;

        // Try to select a "computer-like" voice if available
        const voices = window.speechSynthesis.getVoices();
        const preferredVoice = voices.find(v => v.name.includes("Google US English") || v.name.includes("Samantha"));
        if (preferredVoice) utterance.voice = preferredVoice;

        utterance.onstart = () => setIsSpeaking(true);
        utterance.onend = () => setIsSpeaking(false);
        utterance.onerror = () => setIsSpeaking(false);

        window.speechSynthesis.speak(utterance);
    }, [mounted]);

    return { speak, isSpeaking };
};

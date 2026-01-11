"use client";

import { useState } from 'react';
import { API_URL } from '../config';
import { useVoice } from '../hooks/useVoice';

export default function NeuralChat() {
    const [message, setMessage] = useState('');
    const [status, setStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle');
    const { speak } = useVoice();

    const handleSend = async () => {
        if (!message.trim()) return;

        setStatus('sending');
        try {
            const res = await fetch(`${API_URL}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message }),
            });

            if (res.ok) {
                setStatus('sent');
                setMessage('');
                speak('Uplink Confirmed. Message Transmitted.');
                setTimeout(() => setStatus('idle'), 2000);
            } else {
                setStatus('error');
                speak('Transmission Failed.');
            }
        } catch (e) {
            setStatus('error');
            speak('Transmission Failed.');
        }
    };

    return (
        <div className="border border-green-900/30 bg-black/40 p-6 rounded-xl backdrop-blur-sm flex flex-col h-full min-h-[200px] relative overflow-hidden">
            {/* Header */}
            <h2 className="text-sm font-bold text-green-500 mb-4 tracking-widest flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse" />
                NEURAL UPLINK // CHAT
            </h2>

            {/* Chat Area (Placeholder for history) */}
            <div className="flex-1 overflow-y-auto mb-4 space-y-2 p-2 rounded bg-black/20 border border-green-900/10 h-32">
                <div className="text-xs text-green-900 font-mono italic text-center mt-10">
                    Link Established. Awaiting Input.
                </div>
            </div>

            {/* Input Area */}
            <div className="relative">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                        placeholder="Message the Brain..."
                        className="flex-1 bg-black/50 border border-green-900/50 rounded px-3 py-2 text-sm text-green-100 placeholder-green-900/50 focus:outline-none focus:border-blue-500 transition-colors font-mono"
                        disabled={status === 'sending'}
                    />
                    <button
                        onClick={handleSend}
                        disabled={status === 'sending' || !message.trim()}
                        className={`px-4 py-2 rounded text-xs font-bold transition-all ${status === 'sending'
                            ? 'bg-blue-900/20 text-blue-500/50'
                            : 'bg-blue-600 hover:bg-blue-500 text-black hover:shadow-[0_0_10px_rgba(59,130,246,0.5)]'
                            }`}
                    >
                        {status === 'sending' ? 'TX...' : 'SEND'}
                    </button>
                </div>

                {/* Status Indicators */}
                {status === 'sent' && (
                    <div className="absolute -bottom-5 left-0 text-[10px] text-green-400 font-mono animate-in fade-in">
                        ✅ UPLINK SUCCESSFUL
                    </div>
                )}
                {status === 'error' && (
                    <div className="absolute -bottom-5 left-0 text-[10px] text-red-400 font-mono animate-in fade-in">
                        ❌ TX FAILED
                    </div>
                )}
            </div>
        </div>
    );
}

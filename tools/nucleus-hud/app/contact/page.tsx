
"use client";

import { useState } from 'react';

export default function ContactPage() {
    const [status, setStatus] = useState('idle');

    return (
        <div className="p-8 min-h-screen bg-black text-green-500 font-mono">
            <div className="border border-green-900/30 bg-black/40 p-6 rounded-xl backdrop-blur-sm max-w-2xl mx-auto">
                <h1 className="text-2xl font-bold mb-4 tracking-widest uppercase flex items-center gap-2">
                    <span className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
                    Secure Uplink
                </h1>

                <form className="space-y-4">
                    <div>
                        <label className="block text-xs font-bold mb-2 uppercase tracking-wide">Signal Source</label>
                        <input type="text" className="w-full bg-black/50 border border-green-900/50 rounded px-4 py-2 text-green-100 focus:border-green-500 focus:outline-none" placeholder="CALLSIGN" />
                    </div>
                    <div>
                        <label className="block text-xs font-bold mb-2 uppercase tracking-wide">Transmission</label>
                        <textarea className="w-full bg-black/50 border border-green-900/50 rounded px-4 py-2 text-green-100 focus:border-green-500 focus:outline-none h-32" placeholder="MESSAGE CONTENT..." />
                    </div>
                    <button className="w-full bg-green-900/20 text-green-500 border border-green-900/30 py-3 rounded uppercase font-bold tracking-widest hover:bg-green-900/40 hover:border-green-500 transition-all">
                        Transmit
                    </button>
                </form>
            </div>
        </div>
    );
}

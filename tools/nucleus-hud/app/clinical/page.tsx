
"use client";

import React from 'react';
import NucleusPHQ9 from '../components/clinical/NucleusPHQ9';

export default function ClinicalPage() {
    return (
        <div className="container mx-auto p-4 min-h-screen">
            <header className="mb-8">
                <h1 className="text-3xl font-bold text-green-500 mb-2">CLINICAL_TESTING_SUITE</h1>
                <p className="text-green-500/60 font-mono text-sm">Validating Assessment Logic & Safety Protocols</p>
            </header>

            <main className="grid grid-cols-1 gap-8">
                <section>
                    <div className="mb-4 flex items-center gap-2">
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                        <h2 className="text-xl font-bold text-green-400">PHQ-9 STANDARD</h2>
                    </div>
                    <NucleusPHQ9 />
                </section>
            </main>
        </div>
    );
}

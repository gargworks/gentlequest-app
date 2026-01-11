
"use client";

import React, { useState } from 'react';
import NucleusCrisisModal from './NucleusCrisisModal';

// Context: PHQ-9 Standard
const questions = [
    "Little interest or pleasure in doing things",
    "Feeling down, depressed, or hopeless",
    "Trouble falling or staying asleep, or sleeping too much",
    "Feeling tired or having little energy",
    "Poor appetite or overeating",
    "Feeling bad about yourself",
    "Trouble concentrating on things",
    "Moving or speaking so slowly that other people could have noticed",
    "Thoughts that you would be better off dead"
];

const options = [
    { value: 0, label: "Not at all" },
    { value: 1, label: "Several days" },
    { value: 2, label: "More than half the days" },
    { value: 3, label: "Nearly every day" }
];

export default function NucleusPHQ9() {
    const [scores, setScores] = useState<number[]>(new Array(9).fill(0));
    const [total, setTotal] = useState(0);
    const [submitted, setSubmitted] = useState(false);

    // Context: Crisis Detection Logic (Question 9 is critical)
    const isCrisis = scores[8] > 0;

    const handleChange = (index: number, value: string) => {
        const newScores = [...scores];
        newScores[index] = parseInt(value);
        setScores(newScores);
        setTotal(newScores.reduce((a, b) => a + b, 0));
    };

    const handleSubmit = () => {
        // In real app: call API to save
        setSubmitted(true);
    };

    return (
        <div className="p-6 border border-green-500/30 bg-black/80 rounded-lg backdrop-blur-md shadow-[0_0_20px_rgba(0,255,65,0.1)] font-mono text-green-500 max-w-3xl mx-auto">
            <div className="flex justify-between items-center mb-6 border-b border-green-500/30 pb-4">
                <h1 className="text-2xl font-bold text-green-400">CLINICAL_ASSESSMENT <span className="text-xs">[PHQ-9]</span></h1>
                <div className="text-right">
                    <span className="text-xs text-green-500/60 block">SESSION ID</span>
                    <span className="text-sm font-bold">ACTIVE</span>
                </div>
            </div>

            <NucleusCrisisModal
                isOpen={isCrisis}
                onConfirmSafe={() => console.log("User confirmed safety")}
                reason="PHQ-9 Question 9 Flagged"
            />

            {!submitted ? (
                <div className="space-y-6">
                    {questions.map((q, i) => (
                        <fieldset key={i} className="p-4 border border-green-500/10 rounded hover:bg-green-500/5 transition-colors">
                            <legend className="text-sm font-bold mb-3 text-green-300">
                                <span className="mr-2 opacity-50">{String(i + 1).padStart(2, '0')}.</span>
                                {q}
                            </legend>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                {options.map((opt) => (
                                    <label key={opt.value} className={`
                    flex flex-col items-center justify-center p-3 border rounded cursor-pointer transition-all
                    ${scores[i] === opt.value
                                            ? 'bg-green-500/20 border-green-500 shadow-[0_0_10px_rgba(0,255,65,0.2)]'
                                            : 'border-green-500/20 hover:border-green-500/50'}
                  `}>
                                        <input
                                            type="radio"
                                            name={`q${i}`}
                                            value={opt.value}
                                            className="sr-only" // Hidden radio, styled label
                                            onChange={(e) => handleChange(i, e.target.value)}
                                            checked={scores[i] === opt.value}
                                            aria-label={`${opt.label} for Question ${i + 1}`}
                                        />
                                        <span className="text-xs text-center">{opt.label}</span>
                                    </label>
                                ))}
                            </div>
                        </fieldset>
                    ))}

                    <div className="mt-8 pt-6 border-t border-green-500/30 flex justify-between items-center">
                        <div className="text-xl">
                            SCORE: <span className="font-bold text-green-400">{total}</span>
                        </div>
                        <button
                            onClick={handleSubmit}
                            className="px-6 py-2 bg-green-500/20 hover:bg-green-500/40 border border-green-500 text-green-400 font-bold rounded transition-all shadow-[0_0_15px_rgba(0,255,65,0.2)] hover:shadow-[0_0_25px_rgba(0,255,65,0.4)]"
                        >
                            SUBMIT_ASSESSMENT
                        </button>
                    </div>
                </div>
            ) : (
                <div className="text-center py-12">
                    <h2 className="text-3xl font-bold text-green-400 mb-4">ASSESSMENT_COMPLETE</h2>
                    <p className="mb-6">Data logged to secure storage.</p>
                    <div className="inline-block p-4 border border-green-500 rounded">
                        TOTAL SCORE: {total} / 27
                    </div>
                </div>
            )}
        </div>
    );
}

import { NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs/promises';

export const dynamic = 'force-dynamic';

interface Decision {
    timestamp: string;
    proposition: string;
    verdict: string;
    critique: string;
}

export async function GET() {
    try {
        const brainPath = path.resolve(process.cwd(), '../../.brain');
        const decisionPath = path.join(brainPath, 'decisions', 'DECISION_RECORD_PHASE61.md');

        try {
            await fs.access(decisionPath);
        } catch {
            return NextResponse.json({ decision: null });
        }

        const content = await fs.readFile(decisionPath, 'utf-8');
        const entries = content.split('# Session:');

        // Get the last valid entry
        const lastEntry = entries.filter(e => e.trim().length > 0).pop();

        if (!lastEntry) {
            return NextResponse.json({ decision: null });
        }

        // Extremely basic parsing (robust enough for the Simulator format)
        // Format:
        // TIMESTAMP
        // ## Proposition
        // TEXT
        // ## The Round Table Verdict
        // ...

        const lines = lastEntry.split('\n');
        const timestamp = lines[0].trim();

        let proposition = "Unknown";
        let verdict = "Unknown";
        let critique = "";

        const propIndex = lines.findIndex(l => l.includes('## Proposition'));
        const verdictIndex = lines.findIndex(l => l.includes('## The Round Table Verdict'));
        const finalIndex = lines.findIndex(l => l.includes('## Final Decision'));

        if (propIndex !== -1 && verdictIndex !== -1) {
            proposition = lines.slice(propIndex + 1, verdictIndex).join('\n').trim();
        }

        if (finalIndex !== -1) {
            const finalLines = lines.slice(finalIndex + 1);
            verdict = finalLines.find(l => l.includes('Synthesized Verdict') || l.includes('MOCK DECISION')) || "PENDING";
            // Clean up
            verdict = verdict.replace('[Synthesized Verdict:', '').replace(']', '').trim();
        }

        if (verdictIndex !== -1 && finalIndex !== -1) {
            critique = lines.slice(verdictIndex + 1, finalIndex).join('\n').trim();
        }

        const decision: Decision = {
            timestamp,
            proposition,
            verdict,
            critique
        };

        return NextResponse.json({ decision });

    } catch (error) {
        console.error('Oracle Decision Read Error:', error);
        return NextResponse.json({ error: 'Failed to read oracle decisions' }, { status: 500 });
    }
}

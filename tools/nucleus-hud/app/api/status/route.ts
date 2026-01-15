import { NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs/promises';

// Force dynamic - this is a real-time status check
export const dynamic = 'force-dynamic';

export async function GET() {
    // 1. Production/Docker: Fetch from Backend API
    const backendUrl = process.env.NEXT_PUBLIC_APP_API_URL || process.env.NEXT_PUBLIC_API_URL;

    if (backendUrl) {
        try {
            const res = await fetch(`${backendUrl}/api/health`, {
                headers: { 'Cache-Control': 'no-cache' },
                cache: 'no-store'
            });

            if (res.ok) {
                const data = await res.json();
                return NextResponse.json(data);
            }
            console.warn(`Backend status check failed: ${res.status}`);
        } catch (e) {
            console.warn(`Backend status connection failed:`, e);
        }
    }

    // 2. Dev Mode Fallback: Read local .brain file
    try {
        const brainPath = path.resolve(process.cwd(), '../../.brain');
        const pulsePath = path.join(brainPath, 'pulse.json');

        await fs.access(pulsePath);
        const fileContent = await fs.readFile(pulsePath, 'utf-8');
        const pulseData = JSON.parse(fileContent);

        return NextResponse.json(pulseData);
    } catch (localError) {
        return NextResponse.json({
            status: 'offline',
            message: 'Pulse unavailable. Backend unreachable and local file not found.',
            timestamp: new Date().toISOString()
        }, { status: 503 });
    }
}

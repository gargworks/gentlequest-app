import { NextResponse } from 'next/server';
import path from 'path';
import { exec } from 'child_process';
import util from 'util';

const execPromise = util.promisify(exec);

export const maxDuration = 60; // Allow 60s for simulation

export async function POST(req: Request) {
    try {
        const body = await req.json();
        const { proposition, mock } = body;

        if (!proposition) {
            return NextResponse.json({ error: 'Proposition is required' }, { status: 400 });
        }

        // Paths
        // In dev: process.cwd() is tools/nucleus-hud
        const rootDir = path.resolve(process.cwd(), '../..');
        const scriptPath = path.join(rootDir, 'scripts', 'gladiator_simulator.py');
        const venvPython = path.join(rootDir, 'mcp-server-nucleus', '.venv', 'bin', 'python');

        // Escape quotes for shell safety (basic)
        const safeProp = proposition.replace(/"/g, '\\"');

        // Command
        let cmd = `${venvPython} ${scriptPath} "${safeProp}" --save`;

        // Mock Mode Override
        const env = { ...process.env };
        if (mock) {
            env['MOCK_SIMULATION'] = '1';
        }
        // Ensure Vertex/API Key is passed
        // Next.js might not inherit all shell envs if not in .env.local, but process.env usually has them if started from shell.

        console.log(`⚔️ WAR ROOM: Executing ${cmd}`);

        const { stdout, stderr } = await execPromise(cmd, {
            cwd: rootDir,
            env: env
        });

        if (stderr && !stderr.includes('WARNING')) { // Ignore warnings
            console.warn('Simulation Stderr:', stderr);
        }

        return NextResponse.json({
            output: stdout,
            verdict: stdout // Frontend can parse if needed, getting raw for now
        });

    } catch (error: any) {
        console.error('Simulation Error:', error);
        return NextResponse.json({
            error: 'Simulation Failed',
            details: error.message
        }, { status: 500 });
    }
}

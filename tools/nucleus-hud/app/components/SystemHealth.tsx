
"use client";

import { useState, useEffect } from 'react';
import { API_URL } from '../config';

interface HealthData {
    status: string;
    timestamp: string;
    uptime: number;
    version: string;
}

export default function SystemHealth() {
    const [health, setHealth] = useState<HealthData | null>(null);
    const [error, setError] = useState<boolean>(false);

    useEffect(() => {
        const fetchHealth = async () => {
            try {
                const res = await fetch(`${API_URL}/api/health`);
                if (res.ok) {
                    const data = await res.json();
                    setHealth(data);
                    setError(false);
                } else {
                    setError(true);
                }
            } catch (e) {
                setError(true);
            }
        };

        fetchHealth();
        const interval = setInterval(fetchHealth, 5000); // Poll every 5 seconds
        return () => clearInterval(interval);
    }, []);

    if (error) {
        return (
            <div className="flex items-center space-x-2 text-red-500">
                <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
                <span className="text-xs font-mono uppercase">OFFLINE</span>
            </div>
        );
    }

    if (!health) {
        return (
            <div className="flex items-center space-x-2 text-gray-500">
                <div className="w-3 h-3 bg-gray-500 rounded-full" />
                <span className="text-xs font-mono uppercase">CONNECTING...</span>
            </div>
        );
    }

    return (
        <div className="flex items-center space-x-2 text-green-500" title={`Uptime: ${Math.floor(health.uptime)}s`}>
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
            <span className="text-xs font-mono uppercase">ONLINE v{health.version}</span>
        </div>
    );
}

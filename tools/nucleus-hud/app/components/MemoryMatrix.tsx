"use client";

import { useEffect, useState } from "react";
import { API_URL } from "../config";

interface MemoryNode {
    id: string;
    path: string;
    type: "strategy" | "agent" | "data" | "memory" | "other";
    size: number;
    last_modified: number;
}

export default function MemoryMatrix() {
    const [nodes, setNodes] = useState<MemoryNode[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchMemory = async () => {
            try {
                const res = await fetch(`${API_URL}/api/memory`);
                if (res.ok) {
                    const data = await res.json();
                    setNodes(data);
                }
            } catch (e) {
                console.error("Failed to fetch memory matrix", e);
            } finally {
                setLoading(false);
            }
        };

        fetchMemory();
        // Poll every 5 seconds for updates
        const interval = setInterval(fetchMemory, 5000);
        return () => clearInterval(interval);
    }, []);

    const getColor = (type: string) => {
        switch (type) {
            case "strategy": return "bg-red-500/80 hover:bg-red-400";
            case "agent": return "bg-blue-500/80 hover:bg-blue-400";
            case "data": return "bg-green-500/80 hover:bg-green-400";
            case "memory": return "bg-purple-500/80 hover:bg-purple-400";
            default: return "bg-zinc-700/80 hover:bg-zinc-600";
        }
    };

    if (loading) return <div className="text-xs text-zinc-600 animate-pulse">Initializing Neural Link...</div>;

    // Sort by type for visual clustering
    const sortedNodes = [...nodes].sort((a, b) => a.type.localeCompare(b.type));

    return (
        <div className="w-full bg-black/40 border border-green-900/30 rounded-lg p-4">
            <div className="flex justify-between items-center mb-3">
                <h3 className="text-green-500 font-bold text-xs uppercase tracking-widest flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-3 h-3">
                        <path d="M12 15a3 3 0 100-6 3 3 0 000 6z" />
                        <path fillRule="evenodd" d="M1.323 11.447C2.811 6.976 7.028 3.75 12.001 3.75c4.97 0 9.185 3.223 10.675 7.69.12.362.12.752 0 1.113-1.487 4.471-5.705 7.697-10.677 7.697-4.97 0-9.186-3.223-10.675-7.69a1.762 1.762 0 010-1.113zM17.25 12a5.25 5.25 0 11-10.5 0 5.25 5.25 0 0110.5 0z" clipRule="evenodd" />
                    </svg>
                    Memory Matrix
                    <span className="text-[10px] text-zinc-600 ml-2">({nodes.length} nodes)</span>
                </h3>
            </div>

            <div className="grid grid-cols-12 gap-1 max-h-[150px] overflow-y-auto scrollbar-hide">
                {sortedNodes.map((node) => (
                    <div
                        key={node.id}
                        className={`aspect-square rounded-[1px] cursor-help transition-all duration-300 ${getColor(node.type)}`}
                        title={`${node.path} (${(node.size / 1024).toFixed(1)}KB)`}
                    ></div>
                ))}
            </div>

            <div className="flex gap-4 mt-2 text-[10px] text-zinc-500 font-mono">
                <div className="flex items-center gap-1"><div className="w-2 h-2 bg-red-500/80 rounded-[1px]"></div>Strategy</div>
                <div className="flex items-center gap-1"><div className="w-2 h-2 bg-blue-500/80 rounded-[1px]"></div>Agent</div>
                <div className="flex items-center gap-1"><div className="w-2 h-2 bg-green-500/80 rounded-[1px]"></div>Data</div>
                <div className="flex items-center gap-1"><div className="w-2 h-2 bg-purple-500/80 rounded-[1px]"></div>Mem</div>
            </div>
        </div>
    );
}

import React from 'react';

export interface Agent {
    id: string;
    name: string;
    description: string;
    latest_version: string;
    repo_url: string;
    tags: string[];
    installed?: boolean;
}

interface AgentCardProps {
    agent: Agent;
    onInstall: (id: string) => void;
}

export default function AgentCard({ agent, onInstall }: AgentCardProps) {
    return (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 hover:shadow-lg hover:shadow-cyan-900/20 transition-all">
            <div className="flex justify-between items-start mb-4">
                <div>
                    <h3 className="text-xl font-bold text-slate-100">{agent.name}</h3>
                    <code className="text-xs text-slate-500">{agent.id}</code>
                </div>
                <span className="px-2 py-1 text-xs font-mono bg-slate-900 rounded text-cyan-400">
                    v{agent.latest_version}
                </span>
            </div>

            <p className="text-slate-400 text-sm mb-6 h-12 overflow-hidden">
                {agent.description}
            </p>

            <div className="flex flex-wrap gap-2 mb-6">
                {agent.tags.map(tag => (
                    <span key={tag} className="px-2 py-0.5 text-xs rounded-full bg-slate-700 text-slate-300">
                        {tag}
                    </span>
                ))}
            </div>

            <div className="flex justify-between items-center mt-auto">
                <a
                    href={agent.repo_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-cyan-500 hover:text-cyan-400"
                >
                    View Source
                </a>

                <button
                    onClick={() => onInstall(agent.id)}
                    disabled={agent.installed}
                    className={`px-4 py-2 rounded text-sm font-semibold transition-colors ${agent.installed
                            ? 'bg-green-900/50 text-green-400 cursor-default'
                            : 'bg-cyan-600 hover:bg-cyan-500 text-white'
                        }`}
                >
                    {agent.installed ? 'INSTALLED' : 'GET AGENT'}
                </button>
            </div>
        </div>
    );
}

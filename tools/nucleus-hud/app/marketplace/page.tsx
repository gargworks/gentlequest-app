'use client';

import React, { useState, useEffect } from 'react';
import MarketplaceGrid from '../components/marketplace/MarketplaceGrid';
import { Agent } from '../components/marketplace/AgentCard';

// Mock Data for Phase 57
const MOCK_AGENTS: Agent[] = [
    {
        id: 'agent.std.librarian',
        name: 'Librarian',
        description: 'The keeper of knowledge. Organizes your brain and retrieves information instantly.',
        latest_version: '1.2.0',
        repo_url: 'https://github.com/nucleus/librarian',
        tags: ['memory', 'search', 'core'],
        installed: true
    },
    {
        id: 'agent.std.devops',
        name: 'DevOps Engineer',
        description: 'Automates deployment pipelines, manages Docker containers, and monitors system health.',
        latest_version: '0.8.5',
        repo_url: 'https://github.com/nucleus/devops',
        tags: ['infra', 'ci-cd', 'docker']
    },
    {
        id: 'agent.community.researcher',
        name: 'Deep Researcher',
        description: 'Performs deep hierarchical research on any topic, generating comprehensive reports.',
        latest_version: '2.0.1',
        repo_url: 'https://github.com/community/researcher',
        tags: ['research', 'web', 'analysis']
    },
    {
        id: 'agent.community.artist',
        name: 'Creative Director',
        description: 'Generates image assets and design suggestions using DALL-E 3 and stable diffusion.',
        latest_version: '1.0.0',
        repo_url: 'https://github.com/community/artist',
        tags: ['art', 'design', 'generative']
    }
];

export default function MarketplacePage() {
    const [query, setQuery] = useState('');
    const [agents, setAgents] = useState<Agent[]>(MOCK_AGENTS);

    // Filter logic
    const filteredAgents = agents.filter(agent =>
        agent.name.toLowerCase().includes(query.toLowerCase()) ||
        agent.description.toLowerCase().includes(query.toLowerCase()) ||
        agent.tags.some(tag => tag.toLowerCase().includes(query.toLowerCase()))
    );

    return (
        <div className="min-h-screen bg-slate-950 text-slate-100 p-8">
            <header className="mb-8">
                <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent mb-2">
                    Agent Marketplace
                </h1>
                <p className="text-slate-400">Discover and install capabilities for your Nucleus.</p>
            </header>

            <div className="mb-8 relative max-w-xl">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <svg className="h-5 w-5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                </div>
                <input
                    type="text"
                    className="block w-full pl-10 pr-3 py-3 bg-slate-900 border border-slate-700 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:outline-none text-slate-100 placeholder-slate-500"
                    placeholder="Search for agents (e.g., 'research', 'devops')..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                />
            </div>

            <MarketplaceGrid agents={filteredAgents} />
        </div>
    );
}

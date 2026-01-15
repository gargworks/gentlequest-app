import React from 'react';
import AgentCard, { Agent } from './AgentCard';

interface MarketplaceGridProps {
    agents: Agent[];
}

export default function MarketplaceGrid({ agents }: MarketplaceGridProps) {
    const handleInstall = (id: string) => {
        // In a real app, this would call an API or MCP tool
        console.log(`Requesting installation of ${id}`);
        alert(`Nucleus: Installing ${id}... (Check terminal)`);
    };

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {agents.map(agent => (
                <AgentCard
                    key={agent.id}
                    agent={agent}
                    onInstall={handleInstall}
                />
            ))}
        </div>
    );
}

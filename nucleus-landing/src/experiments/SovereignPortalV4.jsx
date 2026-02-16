import React from 'react';
import { Shield, Book, MessageSquare, Terminal, HelpCircle, Activity } from 'lucide-react';

const SovereignPortalV4 = () => {
    const GITHUB_URL = 'https://github.com/eidetic-works/nucleus-mcp';
    const DOCS_URL = 'https://github.com/eidetic-works/nucleus-mcp#installation';
    const DISCORD_URL = 'https://discord.gg/RJuBNNJ5MT';

    return (
        <section className="px-6 py-24 max-w-7xl mx-auto border-t border-white/5 bg-slate-900/40 rounded-3xl mt-20 relative overflow-hidden">
            <div className="absolute inset-0 bg-purple-500/5 blur-[120px] pointer-events-none"></div>

            <div className="relative z-10 grid md:grid-cols-2 gap-16 items-center">
                <div className="text-left space-y-6">
                    <div className="inline-flex items-center gap-2 px-3 py-1 bg-purple-500/10 border border-purple-500/20 rounded-full text-purple-300 text-[10px] font-mono uppercase tracking-widest">
                        <Shield className="w-3 h-3" /> System_Sovereignty: V4.0
                    </div>
                    <h2 className="text-4xl font-bold tracking-tight">
                        The Exit Path: <br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-violet-400">Total Local Sovereignty</span>
                    </h2>
                    <p className="text-slate-400 text-lg leading-relaxed max-w-lg">
                        Automated magic is for entry. True control requires precision. Use these verified paths to reclaim your compute, audit your agents, and join the Sovereign network.
                    </p>

                    <div className="flex flex-wrap gap-4 pt-4">
                        <a href={DISCORD_URL} target="_blank" rel="noopener noreferrer"
                            className="px-6 py-3 bg-purple-600 hover:bg-purple-500 text-white rounded-xl font-bold transition-all shadow-lg shadow-purple-500/20 flex items-center gap-2 group">
                            <MessageSquare className="w-4 h-4 group-hover:scale-110 transition-transform" />
                            Human_Support
                        </a>
                        <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer"
                            className="px-6 py-3 bg-slate-800 border border-white/10 hover:border-purple-500/50 text-slate-300 rounded-xl font-bold transition-all flex items-center gap-2 group">
                            <Activity className="w-4 h-4 group-hover:animate-pulse" />
                            Audit_Registry
                        </a>
                    </div>
                </div>

                <div className="grid sm:grid-cols-2 gap-6">
                    <SafetyCard
                        icon={<Terminal className="w-5 h-5 text-purple-400" />}
                        title="Manual Setup"
                        desc="Step-by-step verified guide for environments requiring absolute isolation."
                        link={DOCS_URL}
                        linkText="View_Docs"
                    />
                    <SafetyCard
                        icon={<HelpCircle className="w-5 h-5 text-blue-400" />}
                        title="Troubleshooting"
                        desc="Resolve 'Red Bubble' handshake errors and connection drifts."
                        link={`${GITHUB_URL}/issues`}
                        linkText="Get_Help"
                    />
                    <SafetyCard
                        icon={<Book className="w-5 h-5 text-green-400" />}
                        title="The Manifesto"
                        desc="Understand the 'Default-Deny' architecture and the future of local-first agents."
                        link={`${GITHUB_URL}/blob/main/docs/PROTOCOL_SPEC.md`}
                        linkText="Read_Logic"
                    />
                    <SafetyCard
                        icon={<Shield className="w-5 h-5 text-yellow-500" />}
                        title="Security Audit"
                        desc="Verify SHA-256 Decision Logs and agent behavioral boundaries."
                        link={`${GITHUB_URL}/blob/main/docs/SECURITY.md`}
                        linkText="Verify_DSoR"
                    />
                </div>
            </div>
        </section>
    );
};

const SafetyCard = ({ icon, title, desc, link, linkText }) => (
    <div className="p-6 rounded-2xl bg-white/5 border border-white/5 hover:border-purple-500/30 transition-all group backdrop-blur-sm">
        <div className="w-10 h-10 bg-slate-900 rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
            {icon}
        </div>
        <h3 className="font-bold text-white mb-2">{title}</h3>
        <p className="text-xs text-slate-500 leading-relaxed mb-4">{desc}</p>
        <a href={link} target="_blank" rel="noopener noreferrer"
            className="text-[10px] font-mono text-purple-400 hover:text-purple-300 uppercase tracking-widest flex items-center gap-1 group/link">
            {linkText} <span className="group-hover/link:translate-x-1 transition-transform">→</span>
        </a>
    </div>
);

export default SovereignPortalV4;

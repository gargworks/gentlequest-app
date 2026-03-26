import { Shield, Server, Terminal, Lock, Cpu, GitBranch, Github, Database, Share2, Activity, Zap, Users, PlayCircle } from 'lucide-react';
import { useState, useEffect } from 'react';

// Official Ecosystem Logos (LobeHub Monochrome Set - jsDelivr CDN)
const CLAUDE_LOGO = "https://cdn.jsdelivr.net/gh/lobehub/lobe-icons@master/packages/static-svg/icons/claude.svg";
const CURSOR_LOGO = "https://cdn.jsdelivr.net/gh/lobehub/lobe-icons@master/packages/static-svg/icons/cursor.svg";
const WINDSURF_LOGO = "https://cdn.jsdelivr.net/gh/lobehub/lobe-icons@master/packages/static-svg/icons/windsurf.svg";
const CHATGPT_LOGO = "https://cdn.jsdelivr.net/gh/lobehub/lobe-icons@master/packages/static-svg/icons/openai.svg";
const PERPLEXITY_LOGO = "https://cdn.jsdelivr.net/gh/lobehub/lobe-icons@master/packages/static-svg/icons/perplexity.svg";
const ANTIGRAVITY_LOGO = "/antigravity-white.png";
const OPENCLAW_LOGO = "https://cdn.jsdelivr.net/gh/lobehub/lobe-icons@master/packages/static-svg/icons/openclaw.svg";
const MCP_LOGO = "https://cdn.jsdelivr.net/gh/lobehub/lobe-icons@master/packages/static-svg/icons/mcp.svg";

import SovereignMonolith from './components/SovereignMonolith_FINAL';

function LaunchBanner() {
  return (
    <div className="bg-gradient-to-r from-purple-600 to-pink-600 py-1.5 px-6 text-center text-[10px] md:text-xs font-bold tracking-widest uppercase sticky top-0 z-50 shadow-lg backdrop-blur-md">
      <a
        href="https://www.producthunt.com/posts/nucleus-mcp?utm_source=badge-featured&utm_medium=badge&utm_souce=badge-nucleus-mcp"
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center justify-center gap-2 hover:opacity-90 transition-opacity"
      >
        <Zap className="w-3 h-3 fill-current" />
        Nucleus is Live on Product Hunt! Support the Sovereign Web
        <Share2 className="w-3 h-3" />
      </a>
    </div>
  );
}

function App() {
  const GITHUB_URL = 'https://github.com/eidetic-works/nucleus-mcp';
  const PYPI_URL = 'https://pypi.org/project/nucleus-mcp/';
  const DISCORD_URL = 'https://discord.gg/RJuBNNJ5MT';

  /* 
     METRICS SYSTEM 
     GitHub Stars: Real-time via API
     Cognitive Pulse: Representational Counter
     Active Nodes/DSoR: Projected Milestone Targets
  */
  const [stars, setStars] = useState(0);

  useEffect(() => {
    fetch('https://api.github.com/repos/eidetic-works/nucleus-mcp')
      .then(res => res.json())
      .then(data => setStars(data.stargazers_count || 0))
      .catch(() => setStars(0));
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-white selection:bg-purple-500/30">
      <LaunchBanner />
      {/* Navbar */}
      <nav className="px-6 py-4 flex justify-between items-center max-w-7xl mx-auto border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-purple-600 rounded-xl flex items-center justify-center">
            <Cpu className="w-6 h-6 text-white" />
          </div>
          <span className="text-xl font-bold tracking-tight">Nucleus™ <span className="hidden sm:inline text-purple-400 font-mono text-sm ml-1">v1.6</span></span>
        </div>
        <div className="hidden md:flex items-center gap-6">
          <a href="#governance" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">Features</a>
          <a href="#install" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">Install</a>
          <a href="#enterprise" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">Enterprise</a>
        </div>
        <div className="flex items-center gap-3">
          <a
            href={PYPI_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-400 hover:text-white transition-colors"
          >
            PyPI
          </a>
          <a
            href="https://www.npmjs.com/package/nucleus-mcp"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-400 hover:text-white transition-colors"
          >
            NPM
          </a>
          <a
            href={GITHUB_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 rounded-full text-sm font-medium transition-colors border border-white/10"
          >
            <Github className="w-4 h-4" />
            <span>{stars || 'Star'} on GitHub</span>
          </a>
        </div>
      </nav>

      <div className="bg-purple-900/10 border-b border-white/5 py-4">
        <div className="max-w-7xl mx-auto px-6 flex flex-wrap justify-center md:justify-between items-center gap-6 md:gap-4 font-mono text-[10px] md:text-xs tracking-widest uppercase text-slate-500">
          <div className="flex items-center gap-2">
            <Database className="w-3 h-3 text-purple-500" />
            <span>Persistent Memory <span className="text-purple-400">Engrams</span></span>
          </div>
          <div className="flex items-center gap-2">
            <Zap className="w-3 h-3 text-yellow-500" />
            <span>170+ <span className="text-yellow-400">MCP Tools</span></span>
          </div>
          <div className="flex items-center gap-2">
            <Shield className="w-3 h-3 text-green-500" />
            <span>Full <span className="text-green-400">Audit Trail</span></span>
          </div>
          <div className="hidden lg:flex items-center gap-2">
            <Activity className="w-3 h-3 text-cyan-500" />
            <span>Multi-Agent <span className="text-cyan-400">Coordination</span></span>
          </div>
        </div>
      </div>

      {/* Hero Section */}
      <section className="px-6 pt-28 pb-20 md:pt-32 md:pb-32 max-w-7xl mx-auto text-center">
        <div className="flex flex-wrap justify-center gap-4 mb-8 text-[10px] md:text-sm">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-purple-500/10 border border-purple-500/20 rounded-full text-purple-300 font-medium">
            <Shield className="w-3 h-3" />
            <span>MCP Server &middot; 100% Local</span>
          </div>
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-green-500/10 border border-green-500/20 rounded-full text-green-400 font-medium">
            <Lock className="w-3 h-3" />
            <span>Persistent Memory &middot; Full Governance</span>
          </div>
        </div>

        <h1 className="text-5xl md:text-7xl font-bold leading-tight mb-8 tracking-tight">
          <span className="sr-only">Nucleus AI: </span>
          Stop re-explaining your code to <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">AI Agents.</span>
        </h1>

        <p className="text-xl text-slate-400 mb-12 max-w-2xl mx-auto leading-relaxed">
          Give your AI agents a persistent brain. Memory that survives sessions, decisions that leave audit trails, governance that enforces boundaries — all running locally.
        </p>

        {/* Sovereign Monolith (Unified Entry Point) */}
        <div className="mb-12">
          <SovereignMonolith />
        </div>

        {/* Product Hunt Badge (Official Launch Embed) */}
        <div className="mb-12 flex justify-center">
          <div className="p-1 rounded-2xl bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-white/10 backdrop-blur-xl shadow-2xl transition-transform hover:scale-105 duration-500">
            <a href="https://www.producthunt.com/products/nucleus-mcp?embed=true&utm_source=badge-featured&utm_medium=badge&utm_campaign=badge-nucleus-mcp" target="_blank" rel="noopener noreferrer">
              <img
                src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=1079781&theme=dark"
                alt="Nucleus MCP - The Local-First Agentic Identity & Security Layer | Product Hunt"
                style={{ width: '250px', height: '54px' }}
                width="250"
                height="54"
              />
            </a>
          </div>
        </div>

        {/* Video Deep Dive Section */}
        <div className="mt-32 mb-32 max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-6 tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-purple-200 to-slate-400">
              See Nucleus in Action
            </h2>
            <p className="text-slate-400 text-lg max-w-2xl mx-auto mb-10">
              Watch the launch demo: Local-first memory for AI agents
            </p>

          </div>

          <div className="space-y-16">
            {/* Sovereign Trilogy (Lore & Vision) - PRIORITY 1 */}
            <div className="relative rounded-3xl overflow-hidden border border-white/10 shadow-2xl bg-slate-900/50 p-1">
              <div className="relative pb-[56.25%] h-0 rounded-2xl overflow-hidden">
                <iframe
                  className="absolute top-0 left-0 w-full h-full"
                  src="https://www.youtube.com/embed/D1B6m_F-h80"
                  title="Sovereign Trilogy"
                  frameBorder="0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                ></iframe>
              </div>
              <div className="p-6 border-t border-white/5 bg-slate-900/80 backdrop-blur-xl">
                <h3 className="text-xl font-bold mb-2">The Sovereign Trilogy</h3>
                <p className="text-sm text-slate-400">The vision behind the Recursive Aggregator.</p>
              </div>
            </div>

            {/* Main Launch Demo (v1.0.7 Target) - PRIORITY 2 */}
            <div className="relative rounded-3xl overflow-hidden border border-white/10 shadow-2xl bg-slate-900/50 p-1">
              <div className="relative pb-[56.25%] h-0 rounded-2xl overflow-hidden">
                <iframe
                  className="absolute top-0 left-0 w-full h-full"
                  src="https://www.youtube.com/embed/jI8TUpfjS1A"
                  title="Nucleus Launch Demo"
                  frameBorder="0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                ></iframe>
              </div>
              <div className="p-6 border-t border-white/5 bg-slate-900/80 backdrop-blur-xl">
                <h3 className="text-xl font-bold mb-2">Technical Walkthrough</h3>
                <p className="text-sm text-slate-400">How Nucleus gives AI agents persistent memory and governance.</p>
              </div>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-4 text-sm mb-16">
          <a
            href={DISCORD_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg font-medium transition-all duration-300 shadow-[0_0_20px_rgba(168,85,247,0.3)] hover:shadow-[0_0_30px_rgba(168,85,247,0.5)] active:scale-95"
          >
            Join Discord
          </a>
          <a
            href="https://youtu.be/jI8TUpfjS1A"
            target="_blank"
            rel="noopener noreferrer"
            className="px-6 py-3 bg-white/5 hover:bg-white/10 rounded-lg font-medium transition-colors border border-white/10"
          >
            Watch Launch Video
          </a>
        </div>

        {/* 
          BACKUP: Legacy Production UI (Unwired)
          Preserved for data persistence - removed from active flow in Sovereign 4 update.
          
          <div className="max-w-md mx-auto mb-16 bg-slate-900 border border-white/10 p-4 rounded-xl flex items-center justify-between font-mono text-sm group/legacy">
            <div className="flex items-center gap-2">
              <span className="text-purple-500">{'>'}</span>
              <span className="text-slate-300">pip install nucleus-mcp</span>
            </div>
            <button className="text-xs text-slate-500 group-hover/legacy:text-purple-400 transition-colors uppercase font-bold tracking-widest">
              COPY
            </button>
          </div>
        */}

        {/* Ecosystem Row */}
        <div id="ecosystem" className="pt-8 border-t border-white/5">
          <p className="text-xs font-mono text-slate-500 uppercase tracking-widest mb-8">Natively Supported Ecosystem</p>
          <div className="flex flex-wrap justify-center items-center gap-8 md:gap-16 opacity-50 hover:opacity-100 transition-all duration-700">
            <a
              href="https://modelcontextprotocol.io/quickstart/user"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 group cursor-pointer"
            >
              <div className="w-10 h-10 rounded-lg bg-slate-800/50 p-2 flex items-center justify-center border border-white/5 group-hover:border-purple-500/50 transition-all duration-500 shadow-[0_0_15px_rgba(168,85,247,0)] group-hover:shadow-[0_0_15px_rgba(168,85,247,0.3)] text-slate-400 group-hover:text-white">
                <img src={CLAUDE_LOGO} alt="Claude Desktop MCP integration with Nucleus AI" className="w-full h-full object-contain" style={{ filter: 'brightness(0) invert(1)' }} />
              </div>
              <span className="font-medium text-slate-400 group-hover:text-white transition-colors">Claude</span>
            </a>
            <a
              href="https://docs.cursor.com/mcp"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 group cursor-pointer"
            >
              <div className="w-10 h-10 rounded-lg bg-slate-800/50 p-2 flex items-center justify-center border border-white/5 group-hover:border-blue-500/50 transition-all duration-500 shadow-[0_0_15px_rgba(59,130,246,0)] group-hover:shadow-[0_0_15px_rgba(59,130,246,0.3)] text-slate-400 group-hover:text-white">
                <img src={CURSOR_LOGO} alt="Cursor IDE MCP integration with Nucleus AI" className="w-full h-full object-contain" style={{ filter: 'brightness(0) invert(1)' }} />
              </div>
              <div className="flex flex-col">
                <span className="font-medium text-slate-400 group-hover:text-white transition-colors">Cursor</span>
                <span className="text-[9px] text-blue-500/50 font-mono">Agent-Native</span>
              </div>
            </a>
            <a
              href="https://docs.windsurf.com/windsurf/cascade/mcp"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 group cursor-pointer"
            >
              <div className="w-10 h-10 rounded-lg bg-slate-800/50 p-2 flex items-center justify-center border border-white/5 group-hover:border-cyan-500/50 transition-all duration-500 shadow-[0_0_15px_rgba(6,182,212,0)] group-hover:shadow-[0_0_15px_rgba(6,182,212,0.3)] text-slate-300 group-hover:text-white">
                <img src={WINDSURF_LOGO} alt="Windsurf MCP integration with Nucleus AI" className="w-full h-full object-contain" style={{ filter: 'brightness(0) invert(1)' }} />
              </div>
              <div className="flex flex-col">
                <span className="font-medium text-slate-400 group-hover:text-white transition-colors">Windsurf</span>
                <span className="text-[9px] text-cyan-500/50 font-mono">Agent-Native</span>
              </div>
            </a>
            <a
              href="https://developers.openai.com/api/docs/guides/tools-connectors-mcp"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 group cursor-pointer"
            >
              <div className="w-10 h-10 rounded-lg bg-slate-800/50 p-2 flex items-center justify-center border border-white/5 group-hover:border-green-500/50 transition-all duration-500 shadow-[0_0_15px_rgba(34,197,94,0)] group-hover:shadow-[0_0_15px_rgba(34,197,94,0.3)] text-slate-400 group-hover:text-white">
                <img src={CHATGPT_LOGO} alt="ChatGPT MCP integration with Nucleus AI" className="w-full h-full object-contain" style={{ filter: 'brightness(0) invert(1)' }} />
              </div>
              <span className="font-medium text-slate-400 group-hover:text-white transition-colors">ChatGPT</span>
            </a>
            <a
              href="https://www.perplexity.ai/help-center/en/articles/11502712-local-and-remote-mcps-for-perplexity"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 group cursor-pointer"
            >
              <div className="w-10 h-10 rounded-lg bg-slate-800/50 p-2 flex items-center justify-center border border-white/5 group-hover:border-teal-500/50 transition-all duration-500 shadow-[0_0_15px_rgba(20,184,166,0)] group-hover:shadow-[0_0_15px_rgba(20,184,166,0.3)] text-slate-400 group-hover:text-white">
                <img src={PERPLEXITY_LOGO} alt="Perplexity MCP integration with Nucleus AI" className="w-full h-full object-contain" style={{ filter: 'brightness(0) invert(1)' }} />
              </div>
              <span className="font-medium text-slate-400 group-hover:text-white transition-colors">Perplexity</span>
            </a>
            <a
              href="https://antigravity.google/docs/mcp"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 group cursor-pointer"
            >
              <div className="w-10 h-10 rounded-lg bg-slate-800/50 p-2 flex items-center justify-center border border-white/5 group-hover:border-orange-500/50 transition-all duration-500 shadow-[0_0_15px_rgba(249,115,22,0)] group-hover:shadow-[0_0_15px_rgba(249,115,22,0.3)] text-slate-400 group-hover:text-white">
                <img src={ANTIGRAVITY_LOGO} alt="Antigravity MCP integration with Nucleus AI" className="w-full h-full object-contain" />
              </div>
              <div className="flex flex-col">
                <span className="font-medium text-slate-400 group-hover:text-white transition-colors">Antigravity</span>
                <span className="text-[9px] text-orange-500/50 font-mono">Agent-Native</span>
              </div>
            </a>
            <a
              href="https://docs.openclaw.ai"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 group cursor-pointer invisible lg:visible"
            >
              <div className="w-10 h-10 rounded-lg bg-slate-800/50 p-2 flex items-center justify-center border border-white/5 group-hover:border-white/50 transition-all duration-500 shadow-[0_0_15px_rgba(255,255,255,0)] group-hover:shadow-[0_0_15px_rgba(255,255,255,0.3)] text-slate-400 group-hover:text-white">
                <img src={OPENCLAW_LOGO} alt="OpenClaw MCP integration with Nucleus AI" className="w-full h-full object-contain" style={{ filter: 'brightness(0) invert(1)' }} />
              </div>
              <span className="font-medium text-slate-400 group-hover:text-white transition-colors">OpenClaw</span>
            </a>
          </div>
          <div className="mt-12 flex justify-center gap-6">
            <a href="https://cursor.directory/mcp/nucleus-mcp-the-sovereign-agent-control-plane" target="_blank" rel="noopener noreferrer" className="text-xs font-mono text-slate-500 hover:text-purple-400 transition-colors uppercase tracking-widest">Cursor Directory</a>
            <a href="https://glama.ai/mcp/servers/@eidetic-works/nucleus-mcp" target="_blank" rel="noopener noreferrer" className="text-xs font-mono text-slate-500 hover:text-orange-400 transition-colors uppercase tracking-widest">Glama Registry</a>
            <a href="https://www.pulsemcp.com/servers/eidetic-works-nucleus" target="_blank" rel="noopener noreferrer" className="text-xs font-mono text-slate-500 hover:text-blue-400 transition-colors uppercase tracking-widest">PulseMCP</a>
          </div>
        </div>
      </section>

      {/* Ledger Section (Live Interaction simulation) */}
      <section className="px-6 py-20 bg-slate-900/30 relative">
        <div className="absolute inset-0 bg-purple-500/5 blur-[120px] pointer-events-none"></div>
        <div className="max-w-4xl mx-auto relative z-10">
          <div className="bg-slate-950/50 backdrop-blur-xl rounded-2xl border border-white/10 overflow-hidden shadow-[0_0_50px_-12px_rgba(168,85,247,0.2)]">
            <div className="bg-white/5 px-4 py-2 border-b border-white/10 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]"></div>
                <div className="w-2 h-2 rounded-full bg-yellow-500 shadow-[0_0_8px_rgba(234,179,8,0.5)]"></div>
                <div className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]"></div>
              </div>
              <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">Nucleus Host Ledger (Live)</span>
              <div className="w-6"></div>
            </div>
            <div className="p-6 font-mono text-xs md:text-sm space-y-2 h-64 overflow-hidden relative">
              <div className="text-purple-400 italic mb-4">// Initializing sovereign boundary...</div>
              <div className="flex gap-4">
                <span className="text-slate-600">[20:13:02]</span>
                <span className="text-green-500">INIT</span>
                <span className="text-slate-300">Brain mounted at ~/.brain</span>
              </div>
              <div className="flex gap-4">
                <span className="text-slate-600">[20:13:05]</span>
                <span className="text-blue-500">AUTH</span>
                <span className="text-slate-300">Claude Session IPC Connected (Token Verified)</span>
              </div>
              <div className="flex gap-4">
                <span className="text-slate-600">[20:13:21]</span>
                <span className="text-purple-500">GOV</span>
                <span className="text-slate-300">Applied Rule: Default-Deny (Filesystem: Read-Only)</span>
              </div>
              <div className="flex gap-4">
                <span className="text-slate-600">[20:13:44]</span>
                <span className="text-yellow-500">MEM</span>
                <span className="text-slate-300">Engram Written: [Key: tech_stack] Value: React/MCP</span>
              </div>
              <div className="flex gap-4 animate-pulse">
                <span className="text-slate-600">[20:14:01]</span>
                <span className="text-cyan-500">SYNC</span>
                <span className="text-slate-300">Synchronizing memory with Cursor Hub...</span>
              </div>

              {/* Visual fade effect at bottom */}
              <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-slate-950 to-transparent"></div>
            </div>
          </div>
          <p className="mt-6 text-center text-slate-500 text-sm italic">
            "We built the transparency we wanted as developers." — Nucleus Team
          </p>
        </div>
      </section>


      {/* Differentiation Table */}
      <section className="px-6 py-20 bg-slate-900/50 border-y border-white/5">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">Context vs. Control</h2>
            <p className="text-slate-400">Why CLAUDE.md isn't enough for autonomous agents.</p>
          </div>

          <div className="overflow-hidden rounded-2xl border border-white/10 bg-slate-950">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-white/5 border-b border-white/10">
                  <th className="p-4 md:p-6 font-medium text-slate-400">Feature</th>
                  <th className="p-4 md:p-6 font-medium text-slate-400">CLAUDE.md (Static Context)</th>
                  <th className="p-4 md:p-6 font-bold text-purple-400 bg-purple-500/5">Nucleus (Agent Control Plane)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                <tr>
                  <td className="p-4 md:p-6 font-medium">State</td>
                  <td className="p-4 md:p-6 text-slate-400">Static (read-only text)</td>
                  <td className="p-4 md:p-6 bg-purple-500/5 font-medium text-white">Dynamic (Stateful DB)</td>
                </tr>
                <tr>
                  <td className="p-4 md:p-6 font-medium">Memory</td>
                  <td className="p-4 md:p-6 text-slate-400">Session-bound (forgotten)</td>
                  <td className="p-4 md:p-6 bg-purple-500/5 font-medium text-white">Engram Ledger (Persistent)</td>
                </tr>
                <tr>
                  <td className="p-4 md:p-6 font-medium">Security</td>
                  <td className="p-4 md:p-6 text-slate-400">None (Prompt injection risk)</td>
                  <td className="p-4 md:p-6 bg-purple-500/5 font-medium text-white">Enforced (Auth Boundary)</td>
                </tr>
                <tr>
                  <td className="p-4 md:p-6 font-medium">Tools</td>
                  <td className="p-4 md:p-6 text-slate-400">Suggestions only</td>
                  <td className="p-4 md:p-6 bg-purple-500/5 font-medium text-white">Orchestrated Execution</td>
                </tr>
                <tr>
                  <td className="p-4 md:p-6 font-medium">Provenance</td>
                  <td className="p-4 md:p-6 text-slate-400">None</td>
                  <td className="p-4 md:p-6 bg-purple-500/5 font-medium text-white">DSoR (Decision System of Record)</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Sovereign Pledge Section */}
      <section id="pledge" className="px-6 py-24 max-w-4xl mx-auto border-t border-white/5">
        <div className="p-12 rounded-3xl bg-gradient-to-br from-purple-900/20 to-pink-900/20 border border-purple-500/20 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-8 text-purple-500/10">
            <Shield className="w-64 h-64 -rotate-12" />
          </div>

          <div className="relative z-10">
            <h2 className="text-3xl font-bold mb-8 flex items-center gap-3">
              <Shield className="w-8 h-8 text-purple-400" />
              The Sovereign Pledge
            </h2>

            <div className="space-y-8">
              <PledgeItem
                title="Control, Not Just Context"
                desc={<><code>CLAUDE.md</code> is a map, but a map cannot drive a car. Nucleus is the driver. We move beyond static context to Active Control via Default-Deny policies.</>}
              />
              <PledgeItem
                title="DSoR: Decision System of Record"
                desc="Eliminate 'Black Box' decisions. Every agent interaction is SHA-256 hashed and logged with full decision provenance, proving not just what happened, but exactly why."
              />
              <PledgeItem
                title="Local Sovereignty First"
                desc="Your memory (Engrams) stays on your hardware. No cloud calls, no external dependencies. You own your data."
              />
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="governance" className="px-6 py-24 max-w-7xl mx-auto">
        <h2 className="text-3xl font-bold text-center mb-16">What Nucleus Does</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          <FeatureCard
            icon={<Database className="w-6 h-6 text-purple-400" />}
            title="Brain Persistence"
            desc="Engrams — persistent knowledge that survives across sessions. Write once, recall forever. No more re-explaining your project."
          />
          <FeatureCard
            icon={<Activity className="w-6 h-6 text-cyan-400" />}
            title="Heartbeat"
            desc="Proactive check-ins that catch stale blockers, velocity drops, and idle sessions before they cost you time."
          />
          <FeatureCard
            icon={<Terminal className="w-6 h-6 text-green-400" />}
            title="Multi-Provider Chat"
            desc="Built-in terminal chat with Gemini, Anthropic, and Groq. Hot-switch providers, native tool calling, session resume."
          />
          <FeatureCard
            icon={<Share2 className="w-6 h-6 text-pink-400" />}
            title="Multi-Agent Sync"
            desc="Task queues, agent slots, shared state, and brain sync. Multiple agents coordinate through the brain without direct communication."
          />
        </div>
        <div className="grid md:grid-cols-3 gap-8 mt-8">
          <FeatureCard
            icon={<Lock className="w-6 h-6 text-yellow-400" />}
            title="Governance"
            desc="HITL approval gates, kill switch, resource locking, default-deny policies. Trust is granted, never assumed."
          />
          <FeatureCard
            icon={<Shield className="w-6 h-6 text-blue-400" />}
            title="Audit Trail"
            desc="Every agent decision logged with reasoning. SHA-256 hashed interaction log. Full decision provenance."
          />
          <FeatureCard
            icon={<Server className="w-6 h-6 text-orange-400" />}
            title="170+ MCP Tools"
            desc="Memory, sessions, tasks, governance, compliance, orchestration — organized into facade tools for any MCP client."
          />
        </div>
      </section>

      {/* Install Section */}
      <section id="install" className="px-6 py-24 max-w-4xl mx-auto border-t border-white/5">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">Get Started</h2>
          <p className="text-slate-400">Three commands. Works with any MCP client.</p>
        </div>

        <div className="bg-slate-950/50 backdrop-blur-xl rounded-2xl border border-white/10 overflow-hidden shadow-[0_0_50px_-12px_rgba(168,85,247,0.2)] mb-12">
          <div className="bg-white/5 px-4 py-2 border-b border-white/10 flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-red-500"></div>
            <div className="w-2 h-2 rounded-full bg-yellow-500"></div>
            <div className="w-2 h-2 rounded-full bg-green-500"></div>
            <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider ml-2">Terminal</span>
          </div>
          <div className="p-6 font-mono text-sm space-y-3">
            <div><span className="text-purple-400">$</span> <span className="text-slate-300">pip install nucleus-mcp</span></div>
            <div><span className="text-purple-400">$</span> <span className="text-slate-300">nucleus self-setup</span></div>
            <div><span className="text-purple-400">$</span> <span className="text-slate-300">nucleus status --health</span></div>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          <div>
            <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
              <img src={CLAUDE_LOGO} alt="Claude Desktop MCP configuration" className="w-5 h-5" style={{ filter: 'brightness(0) invert(1)' }} />
              Claude Desktop / Cursor
            </h3>
            <div className="bg-slate-950/50 rounded-xl border border-white/10 p-4 font-mono text-xs overflow-x-auto">
              <pre className="text-slate-300">{`{
  "mcpServers": {
    "nucleus": {
      "command": "python3",
      "args": ["-m", "nucleus_mcp"],
      "env": {
        "NUCLEAR_BRAIN_PATH": "/path/to/.brain"
      }
    }
  }
}`}</pre>
            </div>
          </div>
          <div>
            <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
              <Terminal className="w-5 h-5 text-green-400" />
              Claude Code (.mcp.json)
            </h3>
            <div className="bg-slate-950/50 rounded-xl border border-white/10 p-4 font-mono text-xs overflow-x-auto">
              <pre className="text-slate-300">{`{
  "mcpServers": {
    "nucleus": {
      "command": "python3",
      "args": ["-m", "nucleus_mcp"],
      "env": {
        "NUCLEAR_BRAIN_PATH": ".brain"
      }
    }
  }
}`}</pre>
            </div>
          </div>
        </div>
      </section>

      {/* Media & Assets Section */}
      <section className="px-6 py-24 max-w-7xl mx-auto border-t border-white/5">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold mb-4">Official Brand Assets</h2>
          <p className="text-slate-400">High-resolution previews for the Sovereign Control Plane.</p>
        </div>

        <div className="grid md:grid-cols-2 gap-12">
          <div className="group space-y-4">
            <div className="aspect-video rounded-2xl overflow-hidden border border-white/10 bg-slate-900 transition-all group-hover:border-purple-500/50">
              <img
                src="/social-preview.png"
                alt="Nucleus AI social preview — local-first agent control plane"
                className="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all duration-500"
              />
            </div>
            <div className="flex justify-between items-center px-2">
              <span className="text-sm font-medium text-slate-400">Standard Preview</span>
              <a href="/social-preview.png" download className="text-xs text-purple-400 hover:text-purple-300 font-mono">1200x630.PNG</a>
            </div>
          </div>

          <div className="group space-y-4">
            <div className="aspect-video rounded-2xl overflow-hidden border border-white/10 bg-slate-900 transition-all group-hover:border-pink-500/50">
              <img
                src="/social-preview-hq.png"
                alt="Nucleus AI high-resolution social preview — sovereign agent memory and governance"
                className="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all duration-500"
              />
            </div>
            <div className="flex justify-between items-center px-2">
              <span className="text-sm font-medium text-slate-400">High Resolution (HQ)</span>
              <a href="/social-preview-hq.png" download className="text-xs text-pink-400 hover:text-pink-300 font-mono">1.2GB_VIBE.PNG</a>
            </div>
          </div>
        </div>
      </section>

      {/* Enterprise Section */}
      <section id="enterprise" className="px-6 py-24 max-w-7xl mx-auto border-t border-white/5">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold mb-4">Enterprise Ready</h2>
          <p className="text-slate-400 max-w-2xl mx-auto">Built for organizations that cannot compromise on data sovereignty. Air-gap deployable, compliance-ready, zero cloud dependency.</p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 mb-16">
          <div className="p-8 rounded-2xl bg-gradient-to-br from-purple-900/20 to-slate-900 border border-purple-500/20">
            <Shield className="w-8 h-8 text-purple-400 mb-4" />
            <h3 className="text-xl font-bold mb-2">Air-Gap Ready</h3>
            <p className="text-slate-400 text-sm">Deploy in fully disconnected environments. No cloud calls, no telemetry, no external dependencies.</p>
          </div>
          <div className="p-8 rounded-2xl bg-gradient-to-br from-blue-900/20 to-slate-900 border border-blue-500/20">
            <Lock className="w-8 h-8 text-blue-400 mb-4" />
            <h3 className="text-xl font-bold mb-2">Compliance First</h3>
            <p className="text-slate-400 text-sm">Full cryptographic audit trail. Every decision SHA-256 hashed. Built for ITAR, SOC2, and regulated industries.</p>
          </div>
          <div className="p-8 rounded-2xl bg-gradient-to-br from-green-900/20 to-slate-900 border border-green-500/20">
            <Users className="w-8 h-8 text-green-400 mb-4" />
            <h3 className="text-xl font-bold mb-2">Team Sync</h3>
            <p className="text-slate-400 text-sm">Share knowledge across your team without leaving your infrastructure. Git-based sync coming soon.</p>
          </div>
        </div>

        <div className="text-center">
          <a
            href="mailto:enterprise@nucleusos.dev?subject=Enterprise%20Inquiry"
            className="inline-flex items-center gap-2 px-8 py-4 bg-purple-600 hover:bg-purple-500 rounded-full text-white font-medium transition-colors"
          >
            Contact for Enterprise
          </a>
          <p className="text-slate-500 text-sm mt-4">Custom deployments • Priority support • SLA guarantees</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 py-12 border-t border-white/10">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-6">
            <a href={DISCORD_URL} target="_blank" rel="noopener" className="text-slate-400 hover:text-white transition-colors">Discord</a>
            <a href="https://youtube.com/@NucleusOS" target="_blank" rel="noopener" className="text-slate-400 hover:text-white transition-colors">YouTube</a>
            <a href="https://x.com/NucleusOS" target="_blank" rel="noopener" className="text-slate-400 hover:text-white transition-colors">X.com</a>
            <a href={GITHUB_URL} target="_blank" rel="noopener" className="text-slate-400 hover:text-white transition-colors">GitHub</a>
          </div>
          <p className="text-slate-500 text-sm">© 2026 Nucleus Sovereign OS. Built for the Sovereign Web.</p>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({ icon, title, desc }) {
  return (
    <div className="p-8 rounded-2xl bg-white/5 border border-white/5 hover:border-purple-500/30 transition-colors">
      <div className="w-12 h-12 bg-white/5 rounded-xl flex items-center justify-center mb-6">
        {icon}
      </div>
      <h3 className="text-xl font-bold mb-3">{title}</h3>
      <p className="text-slate-400 leading-relaxed">{desc}</p>
    </div>
  );
}

function PledgeItem({ title, desc }) {
  return (
    <div>
      <h4 className="text-lg font-bold text-white mb-2">{title}</h4>
      <p className="text-slate-400 leading-relaxed text-sm md:text-base">{desc}</p>
    </div>
  );
}

export default App;

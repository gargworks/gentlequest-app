import { Shield, Server, Terminal, Lock, Cpu, GitBranch, Github, Database } from 'lucide-react';

function App() {
  const GITHUB_URL = 'https://github.com/eidetic-works/mcp-server-nucleus-public';
  const PYPI_URL = 'https://pypi.org/project/mcp-server-nucleus/';
  const DISCORD_URL = 'https://discord.gg/RJuBNNJ5MT';

  return (
    <div className="min-h-screen bg-slate-950 text-white selection:bg-purple-500/30">
      {/* Navbar */}
      <nav className="px-6 py-4 flex justify-between items-center max-w-7xl mx-auto border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-purple-600 rounded-xl flex items-center justify-center">
            <Cpu className="w-6 h-6 text-white" />
          </div>
          <span className="text-xl font-bold tracking-tight">Nucleus <span className="text-purple-400 font-mono text-sm ml-1">v0.6.1 (DSoR)</span></span>
        </div>
        <div className="hidden md:flex items-center gap-6">
          <a href="#pledge" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">The Pledge</a>
          <a href="#governance" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">Governance</a>
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
            href={GITHUB_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 rounded-full text-sm font-medium transition-colors border border-white/10"
          >
            <Github className="w-4 h-4" />
            <span>Star on GitHub</span>
          </a>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="px-6 py-20 md:py-32 max-w-7xl mx-auto text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 bg-purple-500/10 border border-purple-500/20 rounded-full text-purple-300 text-sm font-medium mb-8">
          <Shield className="w-3 h-3" />
          <span>Nucleus OS – The Sovereign Agent Control Plane</span>
        </div>

        <h1 className="text-5xl md:text-7xl font-bold leading-tight mb-8 tracking-tight">
          Own your Agent Context with <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">Low-Level Sovereignty</span>
        </h1>

        <p className="text-xl text-slate-400 mb-12 max-w-2xl mx-auto leading-relaxed">
          The Recursive Aggregator that turns MCP servers into a unified, secure operating system for autonomous agents.
        </p>

        {/* Quick Start CTA */}
        <div className="flex flex-col md:flex-row items-center justify-center gap-6 mb-12">
          <div className="w-full max-w-md bg-slate-900 rounded-xl border border-white/10 p-4 flex items-center gap-4 shadow-2xl">
            <Terminal className="w-5 h-5 text-purple-400" />
            <code className="flex-1 text-left font-mono text-sm text-purple-300">
              pip install mcp-server-nucleus
            </code>
            <button
              onClick={() => navigator.clipboard.writeText('pip install mcp-server-nucleus')}
              className="text-xs font-medium text-gray-400 hover:text-white transition-colors uppercase tracking-wider"
            >
              Copy
            </button>
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-4 text-sm">
          <a
            href={DISCORD_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 rounded-lg font-medium transition-colors"
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
      </section>

      {/* Video Section */}
      <section className="px-6 py-20 max-w-5xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            See Nucleus in Action
          </h2>
          <p className="text-slate-400 text-lg">
            Watch the v0.6.0 launch demo: Local-first memory for AI agents
          </p>
        </div>

        <div className="relative rounded-2xl overflow-hidden border border-white/10 shadow-2xl">
          <div className="relative pb-[56.25%] h-0">
            <iframe
              className="absolute top-0 left-0 w-full h-full"
              src="https://www.youtube.com/embed/jI8TUpfjS1A"
              title="Nucleus v0.6.0 Launch"
              frameBorder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            ></iframe>
          </div>
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
                desc="`CLAUDE.md` is a map, but a map cannot drive a car. Nucleus is the driver. We move beyond static context to Active Control via Default-Deny policies."
              />
              <PledgeItem
                title="DSoR: Decision System of Record"
                desc="Eliminate 'Black Box' decisions. Every agent interaction is SHA-256 hashed and logged with full decision provenance, proving not just what happened, but exactly why."
              />
              <PledgeItem
                title="Local Sovereignty First"
                desc="Your strategic memory (Engrams) stays on your hardware. We build for the Chairman who demands truth and data ownership over cloud convenience."
              />
            </div>
          </div>
        </div>
      </section>

      {/* Governance Grid */}
      <section id="governance" className="px-6 py-24 max-w-7xl mx-auto">
        <h2 className="text-3xl font-bold text-center mb-16">The Governance Moat</h2>
        <div className="grid md:grid-cols-3 gap-8">
          <FeatureCard
            icon={<Lock className="w-6 h-6 text-purple-400" />}
            title="Default Deny"
            desc="All mounted servers start with zero network/filesystem access. Trust is explicitly granted, never assumed."
          />
          <FeatureCard
            icon={<GitBranch className="w-6 h-6 text-pink-400" />}
            title="Isolation Boundaries"
            desc="Tools cannot see each other or the full chat history. Nucleus mediates all context exchange."
          />
          <FeatureCard
            icon={<Server className="w-6 h-6 text-blue-400" />}
            title="Auth Firewall"
            desc="API tokens are stored in the Nucleus Host, never passed to agent prompts or logs."
          />
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

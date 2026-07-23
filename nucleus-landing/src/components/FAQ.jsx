import { Cpu, Shield, ChevronDown } from 'lucide-react';
import { useState } from 'react';

const FAQ_DATA = [
  {
    q: "What is Nucleus?",
    a: "Nucleus is a local-first MCP (Model Context Protocol) server that gives AI agents persistent memory, governance, and a full audit trail. It runs local-first on your hardware; optional cloud sync is opt-in and telemetry is opt-out via nucleus config --no-telemetry, acting as a sovereign control plane for AI coding assistants like Claude, Cursor, and Windsurf."
  },
  {
    q: "How does Nucleus work?",
    a: "Nucleus installs as a Python package and runs as an MCP server on your local machine. It provides 114+ tools that AI agents call to store memory (Engrams), log decisions, enforce governance policies, and coordinate multi-agent workflows. All data is stored locally in a .brain directory."
  },
  {
    q: "What is an Engram in Nucleus?",
    a: "An Engram is a unit of persistent memory that survives across AI sessions. When an AI agent learns something about your project — architecture decisions, coding preferences, team context — it writes an Engram that any future session can recall. This eliminates the need to re-explain your codebase every time."
  },
  {
    q: "Which AI tools does Nucleus integrate with?",
    a: "Nucleus integrates natively with any MCP-compatible client including Claude Desktop, Claude Code, Cursor, Windsurf, ChatGPT, Perplexity, and Antigravity. It works through the standard MCP protocol, so any tool that supports MCP servers can use Nucleus."
  },
  {
    q: "Is Nucleus free to use?",
    a: "Nucleus is open source and free for individual developers. The core MCP server, all 114+ tools, and the local-first architecture are available at no cost via PyPI and npm. Enterprise deployments with priority support and SLA guarantees are available by contacting the Nucleus team."
  },
  {
    q: "How does Nucleus handle AI compliance and audit trails?",
    a: "Every AI agent decision is logged with full provenance in the Decision System of Record (DSoR). Each interaction is SHA-256 hashed, creating a cryptographic audit trail that proves not just what happened, but exactly why. This makes Nucleus suitable for regulated industries requiring ITAR or SOC2 compliance."
  },
  {
    q: "What is the Decision System of Record (DSoR)?",
    a: "The DSoR is Nucleus's cryptographic audit log that records every agent decision with reasoning, context, and a SHA-256 hash. It eliminates black-box AI decisions by providing full decision provenance, allowing teams to verify and reproduce any agent action."
  },
  {
    q: "How does Nucleus enforce AI governance?",
    a: "Nucleus uses a default-deny security model where trust is granted, never assumed. It includes Human-in-the-Loop (HITL) approval gates, a kill switch for immediate agent termination, resource locking to prevent conflicts, and configurable governance policies that control what agents can and cannot do."
  },
  {
    q: "Can Nucleus run in air-gapped environments?",
    a: "Yes. Nucleus is designed for air-gap deployment with zero external dependencies. No cloud calls, no telemetry, no internet connection required. All memory, governance, and audit data stays on your local hardware, making it suitable for classified and highly regulated environments."
  },
  {
    q: "How is Nucleus different from CLAUDE.md or cursor rules?",
    a: "CLAUDE.md and cursor rules are static text files that provide read-only context. Nucleus is a dynamic control plane with a stateful database, persistent memory, enforced security boundaries, and orchestrated tool execution. Static context files are a map — Nucleus is the driver."
  },
  {
    q: "What is multi-agent coordination in Nucleus?",
    a: "Nucleus enables multiple AI agents to work simultaneously on the same project through shared task queues, agent slots, synchronized state, and brain sync. Agents coordinate through the central brain without direct communication, preventing conflicts and enabling parallel autonomous work."
  },
  {
    q: "How do I install Nucleus?",
    a: "Install Nucleus in three commands: run 'pip install nucleus-mcp' to install, then 'nucleus self-setup' to configure your brain directory, and 'nucleus status --health' to verify. Add the MCP server configuration to your AI client's settings to connect."
  },
  {
    q: "What is the Heartbeat feature?",
    a: "Heartbeat is Nucleus's proactive monitoring system that performs regular check-ins on your AI workflows. It catches stale blockers, velocity drops, and idle sessions before they cost you time, ensuring your AI agents stay productive and aligned with your goals."
  },
  {
    q: "Who is Nucleus built for?",
    a: "Nucleus is built for software developers and engineering teams who use AI coding assistants daily. It is especially valuable for teams that need persistent AI memory across sessions, auditable AI decisions for compliance, and governance controls for autonomous agent workflows."
  },
  {
    q: "Does Nucleus support multi-provider LLM chat?",
    a: "Yes. Nucleus includes a built-in terminal chat interface that supports Gemini, Anthropic, and Groq as LLM providers. You can hot-switch between providers mid-conversation, use native tool calling, and resume sessions across restarts."
  },
  {
    q: "Is my data safe with Nucleus?",
    a: "Nucleus follows a local-sovereignty-first principle. All data — memory, decisions, audit logs — stays on your hardware. There are no cloud calls, no external data transmission, and no third-party dependencies. You own and control 100% of your data at all times."
  },
  {
    q: "Can Nucleus be used for enterprise AI compliance?",
    a: "Yes. Nucleus is enterprise-ready with cryptographic audit trails, air-gap deployment support, default-deny governance policies, and full decision provenance. It is built for organizations in regulated industries including defense (ITAR), finance (SOC2), and healthcare that cannot compromise on data sovereignty."
  },
  {
    q: "What makes Nucleus different from other AI memory tools?",
    a: "Nucleus combines persistent memory, governance enforcement, and cryptographic audit trails in a single local-first MCP server. Unlike cloud-based memory solutions, Nucleus runs entirely on your hardware. Unlike simple context files, it provides active control with 114+ orchestrated tools."
  },
  {
    q: "How does Nucleus handle security?",
    a: "Nucleus enforces security through authentication boundaries, default-deny policies, Human-in-the-Loop approval gates, and resource locking. Every interaction is cryptographically hashed. The system is designed to prevent prompt injection and unauthorized agent actions while maintaining full auditability."
  },
  {
    q: "Where can I find Nucleus documentation and community support?",
    a: "Nucleus documentation and source code are available on GitHub at github.com/eidetic-works/nucleus-mcp. The package is published on PyPI and npm. Join the Nucleus Discord community for support, feature discussions, and to connect with other developers using AI governance tools."
  }
];

function FAQItem({ question, answer, isOpen, onToggle }) {
  return (
    <div className="border-b border-white/5 last:border-b-0">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between py-6 px-2 text-left group"
      >
        <h3 className="text-lg font-medium text-white group-hover:text-purple-300 transition-colors pr-4">
          {question}
        </h3>
        <ChevronDown className={`w-5 h-5 text-slate-500 flex-shrink-0 transition-transform duration-200 ${isOpen ? 'rotate-180 text-purple-400' : ''}`} />
      </button>
      {isOpen && (
        <div className="px-2 pb-6">
          <p className="text-slate-400 leading-relaxed">{answer}</p>
        </div>
      )}
    </div>
  );
}

export default function FAQ() {
  const [openIndex, setOpenIndex] = useState(0);

  const faqJsonLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": FAQ_DATA.map(({ q, a }) => ({
      "@type": "Question",
      "name": q,
      "acceptedAnswer": {
        "@type": "Answer",
        "text": a
      }
    }))
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white selection:bg-purple-500/30">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }}
      />

      {/* Navbar */}
      <nav className="px-6 py-4 flex justify-between items-center max-w-7xl mx-auto border-b border-white/5">
        <a href="/" className="flex items-center gap-3">
          <div className="w-10 h-10 bg-purple-600 rounded-xl flex items-center justify-center">
            <Cpu className="w-6 h-6 text-white" />
          </div>
          <span className="text-xl font-bold tracking-tight">Nucleus™</span>
        </a>
        <div className="flex items-center gap-6">
          <a href="/" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">Home</a>
          <a href="/faq" className="text-sm font-medium text-purple-400 transition-colors">FAQ</a>
          <a
            href="https://github.com/eidetic-works/nucleus-mcp"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 rounded-full text-sm font-medium transition-colors border border-white/10"
          >
            GitHub
          </a>
        </div>
      </nav>

      {/* Hero */}
      <section className="px-6 pt-20 pb-8 max-w-4xl mx-auto text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 bg-purple-500/10 border border-purple-500/20 rounded-full text-purple-300 font-medium text-sm mb-6">
          <Shield className="w-3 h-3" />
          <span>Frequently Asked Questions</span>
        </div>
        <h1 className="text-4xl md:text-5xl font-bold leading-tight mb-6 tracking-tight">
          Everything about{' '}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">Nucleus</span>
        </h1>
        <p className="text-lg text-slate-400 max-w-2xl mx-auto">
          The local-first MCP server that gives AI agents persistent memory, governance, and a full cryptographic audit trail.
        </p>
      </section>

      {/* FAQ Accordion */}
      <section className="px-6 py-12 max-w-3xl mx-auto">
        <div className="bg-white/5 border border-white/10 rounded-2xl px-6 md:px-8">
          {FAQ_DATA.map((faq, i) => (
            <FAQItem
              key={i}
              question={faq.q}
              answer={faq.a}
              isOpen={openIndex === i}
              onToggle={() => setOpenIndex(openIndex === i ? -1 : i)}
            />
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="px-6 py-16 max-w-4xl mx-auto text-center">
        <h2 className="text-2xl font-bold mb-4">Ready to get started?</h2>
        <p className="text-slate-400 mb-8">Install Nucleus in under a minute. Works with any MCP client.</p>
        <div className="flex flex-wrap justify-center gap-4">
          <a
            href="https://github.com/eidetic-works/nucleus-mcp"
            target="_blank"
            rel="noopener noreferrer"
            className="px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg font-medium transition-all duration-300 shadow-[0_0_20px_rgba(168,85,247,0.3)]"
          >
            View on GitHub
          </a>
          <a
            href="/"
            className="px-6 py-3 bg-white/5 hover:bg-white/10 rounded-lg font-medium transition-colors border border-white/10"
          >
            Back to Home
          </a>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 py-12 border-t border-white/10">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-6">
            <a href="https://discord.gg/RJuBNNJ5MT" target="_blank" rel="noopener" className="text-slate-400 hover:text-white transition-colors">Discord</a>
            <a href="https://youtube.com/@NucleusOS" target="_blank" rel="noopener" className="text-slate-400 hover:text-white transition-colors">YouTube</a>
            <a href="https://x.com/NucleusOS" target="_blank" rel="noopener" className="text-slate-400 hover:text-white transition-colors">X.com</a>
            <a href="https://github.com/eidetic-works/nucleus-mcp" target="_blank" rel="noopener" className="text-slate-400 hover:text-white transition-colors">GitHub</a>
          </div>
          <p className="text-slate-500 text-sm">© 2026 Nucleus Sovereign OS. Built for the Sovereign Web.</p>
        </div>
      </footer>
    </div>
  );
}

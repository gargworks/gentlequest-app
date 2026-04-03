import { Check, X, Shield, Zap } from 'lucide-react';

const PLANS = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    description: "Full MCP server, open source",
    cta: "pip install nucleus-mcp",
    ctaStyle: "border border-white/20 text-white hover:bg-white/10",
    features: [
      { text: "114+ MCP tools", included: true },
      { text: "Persistent memory (Engrams)", included: true },
      { text: "Session management", included: true },
      { text: "Governance & HITL gates", included: true },
      { text: "Audit trail (DSoR)", included: true },
      { text: "Multi-agent orchestration", included: true },
      { text: "Signed audit reports", included: false },
      { text: "Compliance exports (PDF/HTML)", included: false },
    ],
  },
  {
    name: "Pro",
    price: "$19",
    period: "/month",
    annual: "$149/year (save 35%)",
    description: "Verifiable AI governance",
    cta: "Get Nucleus Pro",
    ctaStyle: "bg-emerald-500 text-black font-bold hover:bg-emerald-400",
    highlight: true,
    features: [
      { text: "Everything in Free", included: true },
      { text: "Cryptographically signed reports", included: true },
      { text: "Compliance exports (DORA, SOC2, MAS)", included: true },
      { text: "Ed25519 verifiable audit trails", included: true },
      { text: "Priority GitHub Issues", included: true },
      { text: "Compliance playbook guides", included: true },
      { text: "CLI Pro badge & status", included: true },
      { text: "Offline — no cloud dependency", included: true },
    ],
  },
];

export default function Pricing() {
  return (
    <section id="pricing" className="py-20 px-6">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-white mb-3">
            Simple pricing. No cloud lock-in.
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto">
            Nucleus is open source and free forever. Pro adds cryptographic proof
            that your AI agents are governed — the document you show auditors.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {PLANS.map((plan) => (
            <div
              key={plan.name}
              className={`rounded-xl p-8 ${
                plan.highlight
                  ? "bg-gradient-to-b from-emerald-500/10 to-transparent border-2 border-emerald-500/30"
                  : "bg-white/5 border border-white/10"
              }`}
            >
              {plan.highlight && (
                <div className="flex items-center gap-2 text-emerald-400 text-xs font-semibold uppercase tracking-wider mb-4">
                  <Shield className="w-3 h-3" />
                  <span>Recommended for teams</span>
                </div>
              )}

              <h3 className="text-xl font-bold text-white">{plan.name}</h3>
              <p className="text-slate-400 text-sm mt-1">{plan.description}</p>

              <div className="mt-4 mb-6">
                <span className="text-4xl font-bold text-white">{plan.price}</span>
                <span className="text-slate-400 ml-1">{plan.period}</span>
                {plan.annual && (
                  <p className="text-emerald-400 text-xs mt-1">{plan.annual}</p>
                )}
              </div>

              <button
                className={`w-full py-3 px-4 rounded-lg text-sm font-medium transition-colors ${plan.ctaStyle}`}
              >
                {plan.cta}
              </button>

              <ul className="mt-8 space-y-3">
                {plan.features.map((f, i) => (
                  <li key={i} className="flex items-start gap-3 text-sm">
                    {f.included ? (
                      <Check className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
                    ) : (
                      <X className="w-4 h-4 text-slate-600 mt-0.5 shrink-0" />
                    )}
                    <span className={f.included ? "text-slate-300" : "text-slate-600"}>
                      {f.text}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <p className="text-center text-slate-500 text-xs mt-8">
          All plans run 100% locally. No data leaves your machine. MIT license.
        </p>
      </div>
    </section>
  );
}

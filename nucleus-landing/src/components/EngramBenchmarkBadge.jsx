import React from 'react';
import { Database } from 'lucide-react';
import engramMetrics from '../data/engramMetrics.json';

export default function EngramBenchmarkBadge() {
  const formattedEngrams = engramMetrics.totalEngrams.toLocaleString();
  const formattedSessions = engramMetrics.sessionsIndexed.toLocaleString();
  const latency = engramMetrics.writeLatencyMs;

  return (
    <a
      href="https://benchmarks.nucleusos.dev"
      target="_blank"
      rel="noopener noreferrer"
      title="View full benchmark methodology"
      className="inline-flex items-center gap-2 px-4 py-1.5 bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/30 rounded-full text-purple-300 text-xs md:text-sm font-medium transition-all duration-300 hover:border-purple-400/50 hover:shadow-[0_0_15px_rgba(168,85,247,0.25)] group"
    >
      <Database className="w-4 h-4 text-purple-400 group-hover:scale-110 transition-transform" />
      <span>
        Powered by <strong className="text-purple-200 font-semibold">{formattedEngrams}</strong> Captured Engrams across <strong className="text-purple-200 font-semibold">{formattedSessions}</strong> Sessions (&lt;{latency}ms write)
      </span>
    </a>
  );
}

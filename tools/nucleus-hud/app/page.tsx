
"use client";

import EventStream from "./components/EventStream";
import TaskBoard from "./components/TaskBoard";
import SwarmMonitor from "./components/SwarmMonitor";
import SystemHealth from "./components/SystemHealth";
import ResearchWidget from "./components/ResearchWidget";
import NeuralChat from "./components/NeuralChat";
import VoiceSynthesizer from "./components/VoiceSynthesizer";
import MemoryMatrix from "./components/MemoryMatrix";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-8 md:p-12 bg-black overflow-hidden relative">
      {/* Background Ambience */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-green-900/20 rounded-full blur-[128px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-900/10 rounded-full blur-[128px]" />
      </div>

      {/* Header */}
      <div className="z-10 w-full max-w-7xl items-center justify-between font-mono text-sm lg:flex mb-8 border-b border-green-900/50 pb-4">
        <p className="flex items-center gap-4 text-green-500">
          <span className="font-bold text-xl tracking-widest text-white">NUCLEUS // HUD</span>
          <span className="text-xs bg-green-900/30 px-2 py-0.5 rounded text-green-300 border border-green-500/20">v1.0.0</span>
          <SystemHealth />
          <div className="h-4 w-px bg-green-900/50 mx-2"></div>
          <VoiceSynthesizer />
        </p>
        <div className="flex gap-4 opacity-50 hover:opacity-100 transition-opacity">
          <a href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:9999"}/api/tasks`} target="_blank" className="hover:text-green-400">TASK.MD</a>
          <a href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:9999"}/api/events`} target="_blank" className="hover:text-green-400">EVENTS.JSONL</a>
        </div>
      </div>

      {/* Main Grid */}
      <div className="z-10 w-full max-w-7xl grid grid-cols-1 lg:grid-cols-3 gap-6 animate-in fade-in duration-700">

        {/* Column 1: Cortex Stream (Full Width on Mobile, Main col on Desktop) */}
        <div className="lg:col-span-3">
          <EventStream />
        </div>

        {/* Column 2: Plan (Left) */}
        <div className="lg:col-span-2 space-y-4">
          <TaskBoard />
        </div>

        {/* Column 3: Active Swarms (Right - New) */}
        <div className="lg:col-span-1 space-y-4">
          <SwarmMonitor />
          <ResearchWidget />
          <NeuralChat />
          <MemoryMatrix />
        </div>
      </div>
    </main>
  );
}

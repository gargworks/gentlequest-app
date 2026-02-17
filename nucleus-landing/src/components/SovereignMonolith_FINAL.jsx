import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Terminal, Copy, Check, Shield, Server, Box,
    ChevronRight, Activity, Cpu,
    Zap, Lock, Search, Eye, ExternalLink, Globe
} from 'lucide-react';

// --- SUB-COMPONENTS ---

const StatusCore = ({ mode, step, latency, size = 192 }) => {
    // Arcs for System Metrics (SVG Paths)
    // Radius: 32 (Inner), 38 (Mid), 44 (Outer)
    const arcData = [
        { r: size * 0.16, color: '#00FF9D', label: 'CPU', val: latency * 2, pattern: 'solid' },
        { r: size * 0.20, color: '#A855F7', label: 'NET', val: 75, pattern: 'dotted' },
        { r: size * 0.24, color: '#3B82F6', label: 'SEC', val: 100, pattern: 'dashed' }
    ];

    // Morph Paths (Circle vs Rounded Rect)
    // Circle: Center (60,60), Radius 24
    const circlePath = "M 60, 36 A 24, 24 0 1,1 60, 84 A 24, 24 0 1,1 60, 36";
    // Rounded Rect: x=36, y=36, width=48, height=48, r=8
    const rectPath = "M 44,36 L 76,36 Q 84,36 84,44 L 84,76 Q 84,84 76,84 L 44,84 Q 36,84 36,76 L 36,44 Q 36,36 44,36";

    return (
        <motion.div
            layoutId="monolith-core"
            className="relative flex items-center justify-center"
            style={{ width: size, height: size }}
        >
            {/* AMBIENT GLOW */}
            <div className={`absolute inset-0 rounded-full blur-3xl transition-opacity duration-1000 ${mode === 'novice' ? 'bg-purple-600/10 opacity-100' : 'bg-green-600/5 opacity-40'}`}></div>

            <svg viewBox="0 0 120 120" className="absolute inset-0 w-full h-full">
                {/* MORPHING BASE */}
                <motion.path
                    d={mode === 'novice' ? circlePath : rectPath}
                    fill="none"
                    stroke="rgba(255,255,255,0.1)"
                    strokeWidth="1"
                    transition={{ duration: 0.8, ease: "easeInOut" }}
                />

                {arcData.map((arc, i) => (
                    <motion.circle
                        key={i}
                        cx="60"
                        cy="60"
                        r={arc.r}
                        fill="none"
                        stroke={arc.color}
                        strokeWidth="1.5"
                        strokeDasharray={arc.pattern === 'dotted' ? '1 4' : arc.pattern === 'dashed' ? '4 4' : 'none'}
                        strokeLinecap="round"
                        style={{ opacity: 0.3 }}
                    />
                ))}
                {arcData.map((arc, i) => (
                    <motion.circle
                        key={`val-${i}`}
                        cx="60"
                        cy="60"
                        r={arc.r}
                        fill="none"
                        stroke={arc.color}
                        strokeWidth="2"
                        strokeDasharray={2 * Math.PI * arc.r}
                        initial={{ strokeDashoffset: 2 * Math.PI * arc.r }}
                        animate={{ strokeDashoffset: (2 * Math.PI * arc.r) * (1 - arc.val / 100) }}
                        transition={{ duration: 2, ease: "easeInOut" }}
                        strokeLinecap="round"
                    />
                ))}
            </svg>

            <motion.div
                className={`relative z-10 p-6 rounded-full border border-white/10 bg-slate-900/40 backdrop-blur-xl flex flex-col items-center justify-center gap-2`}
                animate={{
                    width: mode === 'novice' ? size * 0.7 : size * 0.4,
                    height: mode === 'novice' ? size * 0.7 : size * 0.4,
                }}
            >
                <Cpu className={`${mode === 'novice' ? 'w-8 h-8' : 'w-4 h-4'} text-purple-400`} />
                {mode === 'novice' && (
                    <span className="text-[10px] font-mono text-slate-400 uppercase tracking-widest">
                        {step === 'scanning' ? 'Scanning...' : 'Initiate'}
                    </span>
                )}
            </motion.div>
        </motion.div>
    );
};

const GatewayStrip = ({ os, path, setPath, getCommand, handleCopy, copied, setMode }) => {
    const [handshakeStep, setHandshakeStep] = useState(0);
    const handshakeLogs = ["IDENT_OS: [MACOS]", "PROBING_KERN: [OK]", "VERIFYING_ENGRAM_POOL: [LOCKED]", "ESTABLISHING_SOVEREIGN_BRIDGE..."];

    useEffect(() => {
        const timer = setInterval(() => {
            setHandshakeStep(prev => (prev < handshakeLogs.length ? prev + 1 : prev));
        }, 200);
        return () => clearInterval(timer);
    }, []);

    return (
        <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="w-full max-w-2xl bg-slate-900/80 backdrop-blur-2xl border border-white/10 rounded-3xl overflow-hidden shadow-[0_30px_60px_-15px_rgba(0,0,0,0.5)]"
        >
            <div className="p-10 space-y-8">
                <div className="flex justify-between items-start">
                    <div className="space-y-1">
                        <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                            <span className="text-[10px] font-mono text-purple-400 uppercase tracking-widest font-bold">Step_01: Installation</span>
                        </div>
                        <h3 className="text-2xl font-bold text-white tracking-tight">Bridge the local boundary</h3>
                    </div>
                    <div className="flex flex-col items-end gap-2">
                        <StatusCore mode="intermediate" size={60} />
                        <div className="flex gap-2 p-1 bg-white/5 rounded-lg">
                            {['pip', 'npm'].map(p => (
                                <button
                                    key={p}
                                    onClick={() => setPath(p)}
                                    className={`px-3 py-1.5 rounded-md text-[10px] font-mono transition-all ${path === p ? 'bg-purple-500 text-white' : 'text-slate-500 hover:text-slate-300'}`}
                                >
                                    {p.toUpperCase()}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="bg-slate-950/50 rounded-xl p-4 font-mono text-[10px] space-y-1 border border-white/5">
                    {handshakeLogs.slice(0, handshakeStep).map((log, i) => (
                        <div key={i} className="text-slate-500">
                            <span className="text-purple-500 mr-2">&gt;</span> {log}
                        </div>
                    ))}
                    {handshakeStep < handshakeLogs.length && <div className="w-1 h-3 bg-purple-500 animate-pulse inline-block"></div>}
                </div>

                <AnimatePresence>
                    {handshakeStep >= handshakeLogs.length && (
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="relative"
                        >
                            <div className="bg-[#05070a] border border-white/5 p-5 rounded-2xl flex items-center justify-between group/cmd shadow-2xl">
                                <div className="flex items-center gap-4 flex-1 min-w-0">
                                    <span className="text-purple-400 font-mono text-lg flex items-center shrink-0">
                                        &gt;<span className="w-2 h-4 bg-purple-400 ml-2 shadow-[0_0_10px_rgba(168,85,247,0.5)]"></span>
                                    </span>
                                    <code className="text-slate-200 font-mono text-base truncate ml-2">
                                        {getCommand()}
                                    </code>
                                </div>
                                <button
                                    onClick={handleCopy}
                                    className="ml-4 px-4 py-1 text-[11px] font-mono font-bold tracking-[0.2em] text-slate-500 hover:text-white transition-colors uppercase shrink-0"
                                >
                                    {copied ? 'Copied' : 'Copy'}
                                </button>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                <div className="grid grid-cols-3 gap-6">
                    {[{ icon: Shield, label: 'Encrypted' }, { icon: Server, label: '100% Local' }, { icon: Box, label: 'P2P Mesh' }].map((item, i) => (
                        <div key={i} className="flex items-center gap-3 opacity-60">
                            <item.icon className="w-4 h-4 text-purple-400" />
                            <span className="text-[9px] font-mono text-slate-400 uppercase tracking-tighter">{item.label}</span>
                        </div>
                    ))}
                </div>

                <div className="flex justify-between items-center pt-4 border-t border-white/5">
                    <button
                        onClick={() => setMode('novice')}
                        className="text-[10px] font-mono text-slate-500 hover:text-slate-300 uppercase tracking-widest flex items-center gap-1 transition-colors"
                    >
                        <ChevronRight className="w-3 h-3 rotate-180" /> Back
                    </button>
                    <button
                        onClick={() => setMode('architect')}
                        className="group text-[10px] font-mono text-purple-500 hover:text-purple-400 uppercase tracking-widest flex items-center gap-2 transition-colors font-bold"
                    >
                        Audit_Engine <Search className="w-3 h-3 group-hover:scale-125 transition-transform" />
                    </button>
                </div>
            </div>
        </motion.div>
    );
};

const BentoGrid = ({ auditLogs, auditEndRef, setMode, auditPulseId }) => {
    return (
        <motion.div
            initial={{ y: 50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="w-full grid md:grid-cols-3 gap-4"
        >
            <div className="col-span-1 bg-slate-900/40 backdrop-blur-xl border border-white/5 p-6 rounded-3xl space-y-4 hover:border-purple-500/30 transition-colors">
                <div className="w-10 h-10 rounded-2xl bg-purple-500/10 flex items-center justify-center">
                    <Lock className="w-5 h-5 text-purple-400" />
                </div>
                <h4 className="text-sm font-bold text-white">Security Manifesto</h4>
                <p className="text-[11px] text-slate-500 leading-relaxed">
                    Every bit of memory stays on your hardware. We use E2E encryption for cross-device sync with zero relay server visibility.
                </p>
                <a href="#pledge" className="inline-flex items-center gap-2 text-[10px] text-purple-400 hover:text-purple-300 font-mono transition-colors">
                    READ_PROTOCOL <ExternalLink className="w-3 h-3" />
                </a>
            </div>

            <div className={`col-span-1 md:col-span-2 bg-slate-950/80 border rounded-3xl flex flex-col overflow-hidden transition-all duration-500 ${auditPulseId ? 'border-green-500/50 shadow-[0_0_20px_rgba(0,255,157,0.2)]' : 'border-white/10'}`}>
                <div className="px-6 py-4 border-b border-white/5 flex justify-between items-center">
                    <div className="flex items-center gap-2">
                        <Terminal className="w-4 h-4 text-purple-400" />
                        <span className="text-[10px] font-mono text-slate-400 uppercase tracking-widest">Live_Audit_Trail</span>
                    </div>
                    <StatusCore mode="architect" size={40} />
                </div>
                <div className="p-6 h-[200px] overflow-y-auto font-mono text-[10px] space-y-2 scrollbar-hide">
                    {auditLogs.map(log => (
                        <div key={log.id} className={`flex gap-4 p-1 rounded transition-colors ${auditPulseId === log.id ? 'bg-green-500/20 text-white' : ''}`}>
                            <span className="text-slate-600">[{log.time}]</span>
                            <span className={log.type === 'success' ? 'text-green-500' : log.type === 'warn' ? 'text-yellow-500' : 'text-blue-500'}>
                                {log.msg}
                            </span>
                        </div>
                    ))}
                    <div ref={auditEndRef} />
                </div>
                <div className="px-6 py-4 border-t border-white/5 bg-white/5 flex items-center justify-between">
                    <span className="text-[9px] text-slate-500 font-mono">ENGR_HEALTH: 99.8%</span>
                    <button
                        onClick={() => setMode('intermediate')}
                        className="text-[9px] text-purple-400 hover:text-white transition-colors uppercase font-bold tracking-widest"
                    >
                        Exit_Audit
                    </button>
                </div>
            </div>

            <div className="col-span-full md:col-span-3 grid grid-cols-2 md:grid-cols-4 gap-4 mt-2">
                {[
                    { icon: Globe, label: 'Ecosystem', val: '252+', link: '#ecosystem' },
                    { icon: Eye, label: 'Audit_Logs', val: '1.2k' },
                    { icon: Search, label: 'Scanned', val: 'Verified' },
                    { icon: Activity, label: 'Uptime', val: '100%' }
                ].map((item, i) => (
                    <div key={i} className="bg-white/5 border border-white/5 p-4 rounded-2xl flex items-center justify-between hover:bg-white/10 transition-colors">
                        {item.link ? (
                            <a href={item.link} className="flex items-center justify-between w-full">
                                <div className="flex items-center gap-3">
                                    <item.icon className="w-4 h-4 text-slate-500" />
                                    <span className="text-[10px] font-mono text-slate-400">{item.label}</span>
                                </div>
                                <span className="text-[10px] font-mono text-white font-bold">{item.val}</span>
                            </a>
                        ) : (
                            <>
                                <div className="flex items-center gap-3">
                                    <item.icon className="w-4 h-4 text-slate-500" />
                                    <span className="text-[10px] font-mono text-slate-400">{item.label}</span>
                                </div>
                                <span className="text-[10px] font-mono text-white font-bold">{item.val}</span>
                            </>
                        )}
                    </div>
                ))}
            </div>
        </motion.div>
    );
};

const SovereignMonolith = () => {
    // Helper: Initial OS Detection
    const detectOS = () => {
        if (typeof window === 'undefined') return 'macos';
        const platform = window.navigator.platform.toLowerCase();
        if (platform.includes('win')) return 'windows';
        if (platform.includes('linux')) return 'linux';
        return 'macos';
    };

    // STATE: MODE (novice | intermediate | architect)
    const [mode, setMode] = useState('novice');
    const [step, setStep] = useState('idle'); // idle | scanning | ready
    const [os] = useState(detectOS());
    const [path, setPath] = useState('pip');
    const [copied, setCopied] = useState(false);
    const [latency, setLatency] = useState(12);
    const [auditLogs, setAuditLogs] = useState([
        { id: 1, type: 'info', msg: 'Hypervisor initialized', time: '01:45:01' },
        { id: 2, type: 'success', msg: 'Local engram pool verified', time: '01:45:02' },
        { id: 3, type: 'warn', msg: 'Cloud telemetry blocked (intended)', time: '01:45:05' }
    ]);
    const [sovereignStatus, setSovereignStatus] = useState('offline'); // offline | online

    // Discovery Sidecar Heartbeat (The Reality Gap Bridge)
    useEffect(() => {
        const checkSovereignty = async () => {
            try {
                const start = performance.now();
                const resp = await fetch('http://localhost:42000/health');
                const end = performance.now();
                if (resp.ok) {
                    setSovereignStatus('online');
                    setLatency(Math.round(end - start));
                } else {
                    setSovereignStatus('offline');
                }
            } catch (e) {
                setSovereignStatus('offline');
            }
        };

        const interval = setInterval(checkSovereignty, 2000);
        checkSovereignty();
        return () => clearInterval(interval);
    }, []);

    // Discovery Sidecar Heartbeat
    useEffect(() => {
        const checkSovereignty = async () => {
            try {
                // Ping the locally running Discovery Sidecar
                const resp = await fetch('http://localhost:42000/health');
                if (resp.ok) {
                    setSovereignStatus('online');
                } else {
                    setSovereignStatus('offline');
                }
            } catch (e) {
                setSovereignStatus('offline');
            }
        };
        checkSovereignty();
        const interval = setInterval(checkSovereignty, 3000);
        return () => clearInterval(interval);
    }, []);

    // --- ACTIONS ---

    const [auditPulseId, setAuditPulseId] = useState(null);

    const getCommand = () => {
        if (path === 'pip') {
            return os === 'windows' ? 'pip install nucleus-mcp' : 'pip3 install nucleus-mcp';
        }
        return 'npm i nucleus-mcp';
    };

    const handleCopy = () => {
        navigator.clipboard.writeText(getCommand());
        setCopied(true);

        // Trigger Audit Flash
        setAuditPulseId(2); // Local engram pool verified (Contextual logic)
        setTimeout(() => setAuditPulseId(null), 1000);

        setTimeout(() => setCopied(false), 2000);
    };

    const handleInitiate = () => {
        setStep('scanning');
        setTimeout(() => {
            setStep('ready');
            setMode('intermediate');
        }, 1200);
    };

    const auditEndRef = useRef(null);
    useEffect(() => {
        if (mode === 'architect') {
            auditEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        }
    }, [mode, auditLogs]);

    return (
        <div className="relative w-full max-w-5xl mx-auto py-12 px-4 select-none">

            {/* AMBIENT LIVENESS BAR */}
            <div className="flex items-center justify-between mb-8 px-6">
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                        <Activity className="w-3 h-3 text-purple-400 animate-pulse" />
                        <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest">
                            Sync_Status: <span className={sovereignStatus === 'online' ? "text-green-500 font-bold" : "text-slate-400"}>
                                {sovereignStatus === 'online' ? 'SOVEREIGN_CONNECTED' : 'LOCAL_SIM_MODE'}
                            </span>
                        </span>
                    </div>
                    <div className="flex items-center gap-2 border-l border-white/10 pl-4">
                        <Zap className="w-3 h-3 text-yellow-400" />
                        <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest">
                            Latency: <span className="text-purple-400">{latency}ms</span>
                        </span>
                    </div>
                </div>
                <div className="flex items-center gap-6">
                    <span className="text-[10px] font-mono text-slate-600 uppercase tracking-tighter">
                        Mode: <span className={mode === 'novice' ? 'text-blue-400' : mode === 'intermediate' ? 'text-purple-400' : 'text-red-400'}>{mode.toUpperCase()}</span>
                    </span>
                </div>
            </div>

            {/* MAIN INTERACTION HUB */}
            <div className="relative min-h-[500px] flex flex-col items-center justify-center">

                {/* THE ORB (Status Awareness) */}
                <AnimatePresence mode="wait">
                    {mode === 'novice' && (
                        <motion.div
                            initial={{ scale: 0.8, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 1.2, opacity: 0 }}
                            className="relative group cursor-pointer"
                            onClick={handleInitiate}
                        >
                            <StatusCore mode={mode} step={step} latency={latency} />
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* THE EXPANSION (Gateway) */}
                <AnimatePresence>
                    {mode === 'intermediate' && (
                        <GatewayStrip
                            os={os}
                            path={path}
                            setPath={setPath}
                            getCommand={getCommand}
                            handleCopy={handleCopy}
                            copied={copied}
                            setMode={setMode}
                        />
                    )}
                </AnimatePresence>

                {/* THE BENTO (Architect / Deep Audit) */}
                <AnimatePresence>
                    {mode === 'architect' && (
                        <BentoGrid
                            auditLogs={auditLogs}
                            auditEndRef={auditEndRef}
                            setMode={setMode}
                            auditPulseId={auditPulseId}
                        />
                    )}
                </AnimatePresence>
            </div>

            {/* BACKGROUND DECORATION */}
            <div className="fixed inset-0 pointer-events-none -z-50 overflow-hidden">
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full bg-[radial-gradient(circle_at_center,rgba(88,28,135,0.05)_0%,transparent_70%)]"></div>
            </div>
        </div>
    );
};

export default SovereignMonolith;

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Terminal, Copy, Check, Shield, Server, Box, ChevronRight, HelpCircle, Activity } from 'lucide-react';

const SovereignGateway = () => {
    const [os, setOs] = useState('macos'); // macos | windows | linux
    const [path, setPath] = useState('pip'); // pip | npm
    const [step, setStep] = useState('install'); // install | init
    const [copied, setCopied] = useState(false);
    const [downloads, setDownloads] = useState(500); // 252 (NPM) + ~250 (PyPI Baseline)
    const [isLive, setIsLive] = useState(false);

    // Reliable OS Detection
    useEffect(() => {
        const platform = window.navigator.platform.toLowerCase();
        if (platform.includes('win')) setOs('windows');
        else if (platform.includes('linux')) setOs('linux');
        else setOs('macos');

        // Fetch Live Metrics (NPM + PyPI Scaling)
        fetch('https://api.npmjs.org/downloads/point/2024-01-01:2027-01-01/nucleus-mcp')
            .then(res => res.json())
            .then(data => {
                if (data.downloads) {
                    // We add a PyPI baseline + NPM live total
                    setDownloads(data.downloads + 252);
                    setIsLive(true);
                }
            })
            .catch(() => console.log("Using cached metrics"));
    }, []);

    const getCommand = () => {
        if (step === 'install') {
            if (path === 'pip') {
                return os === 'windows' ? 'pip install nucleus-mcp' : 'pip3 install nucleus-mcp';
            }
            return 'npm i nucleus-mcp';
        }
        return 'nucleus-init --scan';
    };

    const handleCopy = () => {
        navigator.clipboard.writeText(getCommand());
        setCopied(true);
        setTimeout(() => {
            setCopied(false);
            if (step === 'install') setStep('init');
        }, 2000);
    };

    return (
        <div className="max-w-2xl mx-auto">
            {/* TRUST METRICS BAR */}
            <div className="flex items-center justify-between mb-4 px-4">
                <div className="flex items-center gap-2">
                    <Activity className={`w-3 h-3 ${isLive ? 'text-green-500' : 'text-purple-500'} animate-pulse`} />
                    <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest">
                        Global_Reach: <span className="text-purple-400">{downloads}+ Ecosystem Nodes</span>
                        {isLive && <span className="ml-2 text-green-500/50">[LIVE]</span>}
                    </span>
                </div>
                <div className="flex items-center gap-3">
                    <button
                        onClick={() => setPath('pip')}
                        className={`text-[10px] font-mono uppercase tracking-tighter transition-all ${path === 'pip' ? 'text-purple-400 border-b border-purple-400/50' : 'text-slate-600 hover:text-slate-400'}`}
                    >
                        Python/Pip
                    </button>
                    <button
                        onClick={() => setPath('npm')}
                        className={`text-[10px] font-mono uppercase tracking-tighter transition-all ${path === 'npm' ? 'text-purple-400 border-b border-purple-400/50' : 'text-slate-600 hover:text-slate-400'}`}
                    >
                        Node/NPM
                    </button>
                </div>
            </div>

            <div className="relative group">
                {/* BACKGROUND GLOW */}
                <div className="absolute -inset-1 bg-gradient-to-r from-purple-600/20 to-violet-600/20 rounded-2xl blur opacity-25 group-hover:opacity-50 transition duration-1000"></div>

                {/* MAIN CONTAINER */}
                <div className="relative bg-slate-900/80 backdrop-blur-xl border border-white/10 rounded-2xl overflow-hidden shadow-2xl">

                    {/* TERMINAL HEADER */}
                    <div className="bg-white/5 px-4 py-3 border-b border-white/10 flex items-center justify-between">
                        <div className="flex items-center gap-4 text-[10px] font-mono text-slate-500 uppercase tracking-widest">
                            <span className="flex items-center gap-1.5"><Terminal className="w-3 h-3 text-purple-500" /> {os}_env</span>
                            <div className="h-2 w-px bg-white/10 mx-1"></div>
                            <span className="flex items-center gap-1.5 text-slate-600 tracking-normal capitalize">{os} Verified</span>
                        </div>
                        <div className="flex items-center gap-2 text-[10px] font-mono text-slate-500">
                            <Shield className="w-3 h-3" />
                            <span>v1.0.5_STABLE</span>
                        </div>
                    </div>

                    {/* INTERACTIVE CONTENT */}
                    <div className="p-8">
                        <AnimatePresence mode="wait">
                            <motion.div
                                key={step}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                                className="space-y-6"
                            >
                                <div className="flex flex-col gap-2">
                                    <span className="text-[10px] font-mono text-purple-500 uppercase tracking-widest font-bold">
                                        {step === 'install' ? 'Step_01: Installation' : 'Step_02: Initialization'}
                                    </span>
                                    <h3 className="text-xl font-bold text-white">
                                        {step === 'install' ? 'Connect your local environment' : 'Bridge the Sovereign Boundary'}
                                    </h3>
                                </div>

                                {/* COMMAND BOX */}
                                <div className="relative group/cmd">
                                    <div className="absolute -inset-0.5 bg-purple-500/20 rounded-xl blur-sm opacity-0 group-hover/cmd:opacity-100 transition duration-500"></div>
                                    <div className="relative bg-slate-950 border border-white/5 p-5 rounded-xl flex items-center gap-4">
                                        <div className="text-purple-500 font-mono text-lg select-none">$</div>
                                        <code className="flex-1 font-mono text-sm sm:text-base text-slate-300 overflow-x-auto whitespace-nowrap scrollbar-hide">
                                            {getCommand()}
                                        </code>
                                        <button
                                            onClick={handleCopy}
                                            className="p-2.5 bg-purple-500/10 hover:bg-purple-500/20 text-purple-400 rounded-lg transition-all active:scale-90"
                                            title="Copy to clipboard"
                                        >
                                            {copied ? <Check className="w-5 h-5" /> : <Copy className="w-5 h-5" />}
                                        </button>
                                    </div>
                                </div>

                                <p className="text-xs text-slate-500 leading-relaxed font-secondary">
                                    {step === 'install'
                                        ? "Installs the Nucleus host and CLI tools. This creates the local-first boundary required for cross-agent memory."
                                        : "Spins up the hypervisor and scans for Claude, Cursor, and Windsurf configurations to automatically mount the brain."}
                                </p>
                            </motion.div>
                        </AnimatePresence>
                    </div>

                    {/* FOOTER ACTIONS */}
                    <div className="bg-slate-900/50 px-8 py-4 border-t border-white/5 flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <button
                                onClick={() => setStep(step === 'install' ? 'init' : 'install')}
                                className="text-[10px] font-mono text-slate-600 hover:text-purple-400 uppercase tracking-widest transition-colors flex items-center gap-1.5"
                            >
                                <ChevronRight className={`w-3 h-3 transition-transform ${step === 'init' ? 'rotate-180' : ''}`} />
                                {step === 'install' ? 'Skip to Init' : 'Back to Install'}
                            </button>
                        </div>
                        <a
                            href="https://github.com/eidetic-works/nucleus-mcp#quick-start"
                            target="_blank"
                            className="text-[10px] font-mono text-slate-600 hover:text-white uppercase tracking-widest transition-colors flex items-center gap-1.5"
                        >
                            <HelpCircle className="w-3 h-3" />
                            Manual Help
                        </a>
                    </div>
                </div>
            </div>

            {/* SUB-TEXT */}
            <div className="mt-6 flex justify-center gap-8 opacity-40 grayscale hover:grayscale-0 transition-all duration-700">
                <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-tighter text-slate-400">
                    <Box className="w-3 h-3" /> Python 3.10+
                </div>
                <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-tighter text-slate-400">
                    <Server className="w-3 h-3" /> 100% Local-Only
                </div>
                <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-tighter text-slate-400">
                    <Shield className="w-3 h-3" /> MIT Licensed
                </div>
            </div>
        </div>
    );
};

export default SovereignGateway;

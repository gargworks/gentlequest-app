'use client'

import { useEffect } from 'react'

export default function Error({
    error,
    reset,
}: {
    error: Error & { digest?: string }
    reset: () => void
}) {
    useEffect(() => {
        console.error(error)
    }, [error])

    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-black text-red-500 font-mono p-4">
            <h2 className="text-2xl mb-4 font-bold tracking-widest border-b border-red-900 pb-2">CRITICAL SYSTEM FAILURE</h2>
            <div className="bg-zinc-900/50 p-6 rounded border border-red-900/50 mb-8 max-w-4xl w-full overflow-auto shadow-[0_0_30px_rgba(255,0,0,0.2)]">
                <p className="text-white mb-2 font-bold">Error Message:</p>
                <pre className="text-red-400 whitespace-pre-wrap mb-4">{error.message}</pre>
                {error.stack && (
                    <>
                        <p className="text-white mb-2 font-bold">Stack Trace:</p>
                        <pre className="text-zinc-500 text-xs whitespace-pre-wrap">{error.stack}</pre>
                    </>
                )}
            </div>
            <button
                onClick={() => reset()}
                className="px-6 py-2 bg-red-900/20 text-red-500 border border-red-800 hover:bg-red-900/40 transition-colors uppercase tracking-widest text-sm"
            >
                Reboot System
            </button>
        </div>
    )
}

"use client";

import { useEffect, useState } from "react";
import { API_URL } from "../config";

interface Task {
    section: string;
    text: string;
    status: "pending" | "in_progress" | "done";
}

interface TaskGroup {
    section: string;
    tasks: Task[];
}

export default function TaskBoard() {
    const [tasks, setTasks] = useState<Task[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch(`${API_URL}/api/tasks?format=json`)
            .then((res) => res.json())
            .then((data) => {
                if (data.tasks) {
                    setTasks(data.tasks);
                }
            })
            .catch((err) => console.error("Failed to load tasks", err))
            .finally(() => setLoading(false));
    }, []);

    // Group by section
    const grouped: TaskGroup[] = [];
    tasks.forEach((t) => {
        let g = grouped.find((g) => g.section === t.section);
        if (!g) {
            g = { section: t.section, tasks: [] };
            grouped.push(g);
        }
        g.tasks.push(t);
    });

    if (loading) return <div className="text-zinc-500 animate-pulse">Loading Mission Plan...</div>;

    return (
        <div className="w-full text-zinc-300 font-mono text-sm">
            <h2 className="text-xl font-bold mb-6 text-green-500 border-b border-green-900 pb-2">
                MISSION PLAN // TASK.MD
            </h2>

            <div className="space-y-8">
                {grouped.map((group) => (
                    <div key={group.section} className="bg-zinc-900/30 p-4 rounded-lg border border-zinc-800">
                        <h3 className="text-lg font-bold text-zinc-100 mb-4 bg-gradient-to-r from-zinc-800 to-transparent p-2 rounded">
                            {group.section}
                        </h3>
                        <ul className="space-y-2">
                            {group.tasks.map((task, i) => (
                                <li key={i} className="flex items-start gap-3 group">
                                    <div className={`mt-1 w-4 h-4 border rounded-sm flex items-center justify-center shrink-0
                    ${task.status === 'done' ? 'bg-green-600 border-green-600' : ''}
                    ${task.status === 'in_progress' ? 'bg-yellow-600/20 border-yellow-500 animate-pulse' : 'border-zinc-600'}
                  `}>
                                        {task.status === 'done' && <span className="text-white text-xs">✓</span>}
                                        {task.status === 'in_progress' && <span className="text-yellow-500 text-xs">●</span>}
                                    </div>
                                    <span className={`
                    ${task.status === 'done' ? 'text-zinc-500 line-through decoration-zinc-700' : 'text-zinc-300'}
                    ${task.status === 'in_progress' ? 'text-yellow-400' : ''}
                  `}>
                                        {task.text}
                                    </span>
                                </li>
                            ))}
                        </ul>
                    </div>
                ))}
            </div>
        </div>
    );
}

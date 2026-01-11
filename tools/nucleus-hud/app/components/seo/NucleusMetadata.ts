
import type { Metadata } from 'next';

// Context: Derived from NORTH_STAR_VISION.md
// Mission: Overcome human limitations | Gamified Mental Health

export const metadata: Metadata = {
    title: {
        template: '%s | GentleQuest',
        default: 'GentleQuest: Gamified Mental Health for Builders',
    },
    description: 'A mental health system designed to help you overcome limitations and unlock potential. Features depth tracking, dopamine management, and agentic workflows.',
    keywords: ['mental health', 'ADHD', 'gamification', 'agentic AI', 'GentleQuest', 'Nucleus'],
    authors: [{ name: 'Lokesh Garg' }],
    robots: {
        index: true,
        follow: true,
    },
};

export const viewport = {
    width: 'device-width',
    initialScale: 1,
    themeColor: '#00FF41',
};

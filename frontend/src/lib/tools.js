import { Briefcase, FilePenLine, GraduationCap, House, ScanSearch } from 'lucide-react';

/** The dashboard's tools: one route each. */
export const TOOLS = [
  {
    id: 'check',
    path: '/check',
    label: 'Check my resume',
    short: 'Check',
    icon: ScanSearch,
    tone: 'bg-highlight/70 dark:bg-highlight/50',
    description: 'ATS score, job match, skill gaps and fixes for the resume you already have.',
  },
  {
    id: 'build',
    path: '/build',
    label: 'Build a resume',
    short: 'Build',
    icon: FilePenLine,
    tone: 'bg-accent-soft text-accent',
    description: '12 ATS-friendly templates. Edit with a live preview, then download as PDF or Word.',
  },
  {
    id: 'jobs',
    path: '/jobs',
    label: 'Find jobs & internships',
    short: 'Jobs',
    icon: Briefcase,
    tone: 'bg-ok-soft text-ok',
    description: 'Live openings, what employers ask for, and one-click searches on LinkedIn, Internshala and more.',
  },
  {
    id: 'learn',
    path: '/learn',
    label: 'Learn a skill',
    short: 'Learn',
    icon: GraduationCap,
    tone: 'bg-pen-soft text-pen',
    description: 'Pick a skill or a career path and get a full roadmap: order, videos, docs, checklists and projects.',
  },
];

export const HOME = { id: 'home', path: '/', label: 'Home', short: 'Home', icon: House };

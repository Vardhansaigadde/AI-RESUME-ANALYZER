// Resume templates. The definitions live in resumeTemplates.json, an exact copy of
// app/data/resume_templates.json (a backend test checks they match), so the
// preview and the downloaded .docx always agree.
import data from './resumeTemplates.json';

export const TEMPLATES = data.templates;
export const FONTS = data.fonts;
export const ORDERS = data.orders;
export const DEFAULT_TEMPLATE = 'campus';

export const templateById = (id) => TEMPLATES.find((t) => t.id === id) || TEMPLATES.find((t) => t.id === DEFAULT_TEMPLATE);

// Page margin, space before a heading and after a paragraph, in points (same as the .docx)
export const DENSITY = {
  compact: { margin: 36, before: 7, after: 1 },
  normal: { margin: 48, before: 10, after: 2 },
  airy: { margin: 56, before: 14, after: 3 },
};

let fontsRequested = false;
/** Load the web versions of the template fonts (metric-compatible with Calibri, Cambria, Arial…) once. */
export function loadTemplateFonts() {
  if (fontsRequested || typeof document === 'undefined') return;
  fontsRequested = true;
  const families = Object.values(FONTS)
    .map((f) => `family=${f.google}`)
    .join('&');
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = `https://fonts.googleapis.com/css2?${families}&display=swap`;
  document.head.appendChild(link);
}

/** A sample resume for template thumbnails and "start from a sample". */
export const SAMPLE_RESUME = {
  name: 'Priya Sharma',
  headline: 'Computer Science Student | Aspiring Full-Stack Developer',
  email: 'priya.sharma@email.com',
  phone: '+91 98765 43210',
  location: 'Bengaluru, India',
  links: ['linkedin.com/in/priyasharma', 'github.com/priyasharma'],
  summary:
    'Final-year B.Tech student who builds and ships full-stack web apps. Comfortable across React, Node.js and SQL, with an internship building internal tools used by 200+ employees.',
  skills: ['JavaScript', 'TypeScript', 'React', 'Node.js', 'Python', 'SQL', 'PostgreSQL', 'Git', 'Docker', 'REST APIs'],
  experience: [
    {
      title: 'Software Engineering Intern, Acme Technologies',
      subtitle: 'Bengaluru, India',
      date: 'May 2025 – Jul 2025',
      bullets: [
        'Built an internal leave-management tool in React and Node.js used by 200+ employees.',
        'Cut API response time by 35% by adding PostgreSQL indexes and caching hot queries.',
      ],
    },
  ],
  projects: [
    {
      title: 'Campus Events Platform',
      subtitle: 'React, Node.js, PostgreSQL · github.com/priyasharma/events',
      date: '2025',
      bullets: [
        'Built a full-stack app for event sign-ups, used by 1,200+ students in its first semester.',
        'Added email reminders and a waitlist that filled 95% of cancelled seats.',
      ],
    },
    {
      title: 'Expense Tracker API',
      subtitle: 'Python, FastAPI, Docker',
      date: '2024',
      bullets: ['Designed a REST API with JWT auth and monthly reports, containerised with Docker.'],
    },
  ],
  education: [
    {
      title: 'B.Tech in Computer Science and Engineering',
      subtitle: 'National Institute of Technology · CGPA 8.7/10',
      date: '2022 – 2026',
      bullets: [],
    },
  ],
  certifications: ['AWS Certified Cloud Practitioner', 'Meta Front-End Developer (Coursera)'],
  achievements: ['Winner, Smart India Hackathon 2024 (software edition)', 'Solved 400+ problems on LeetCode'],
  additional: [{ heading: 'Languages', items: ['English, Hindi, Kannada'] }],
};

export const EMPTY_RESUME = {
  name: '',
  headline: '',
  email: '',
  phone: '',
  location: '',
  links: [],
  summary: '',
  skills: [],
  experience: [],
  projects: [],
  education: [],
  certifications: [],
  achievements: [],
  additional: [],
};

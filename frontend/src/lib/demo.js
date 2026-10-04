// Demo payloads for /?demo=high and /?demo=low. They have the same shape as a
// real /api/analyze response, so the demo exercises the same UI code paths.

const RESUME = {
  name: 'Alex Sample',
  headline: 'Computer Science (AI & ML) student | Aspiring software engineer',
  email: 'alex.sample@example.com',
  phone: '+91 98765 43210',
  location: '',
  links: ['linkedin.com/in/alexsample', 'github.com/alexsample'],
  summary: 'Third-year B.Tech student who enjoys building web apps and machine learning projects.',
  skills: ['Python', 'SQL', 'Git', 'Machine Learning', 'Docker', 'REST API'],
  experience: [
    {
      title: 'Software Engineering Intern, Acme Labs',
      subtitle: 'May 2025 – Jul 2025',
      bullets: [
        'Built 6 REST API endpoints in FastAPI used by 3 internal teams.',
        'Cut report generation time by 40% with SQL query tuning.',
      ],
    },
  ],
  projects: [
    {
      title: 'Event Registration Portal',
      subtitle: 'React, FastAPI · 2025',
      bullets: ['Built a portal used by 300+ students for college fest registrations.'],
    },
  ],
  education: [
    {
      title: 'B.Tech in Computer Science (AI & ML)',
      subtitle: 'State University · 2023 – 2027 · CGPA 8.6',
      bullets: [],
    },
  ],
  certifications: ['Python for Everybody (Coursera)'],
  achievements: [],
  additional: [],
};

const check = (id, category, title, status, detail, tip = '') => ({ id, category, title, status, detail, tip });

const JOB_INSIGHTS = {
  level: 'Entry level',
  entry_friendly: true,
  years_min: 0,
  years_max: 1,
  degree_mentioned: true,
  must_have: ['python', 'sql', 'git', 'docker', 'aws', 'rest api'],
  nice_to_have: ['kubernetes'],
  also_mentioned: ['ci/cd'],
  must_have_covered: ['python', 'sql', 'git', 'docker', 'rest api'],
  nice_to_have_covered: [],
  lead_with: ['python', 'sql', 'rest api', 'docker', 'git'],
};

const LEARNING_PLAN = [
  {
    skill: 'linux',
    what: 'The operating system behind most servers and cloud machines.',
    why: '',
    resources: [
      {
        title: 'Linux Journey',
        url: 'https://linuxjourney.com/',
        kind: 'tutorial',
        time: '8 h',
        by: '',
      },
      {
        title: 'OverTheWire: Bandit (practice)',
        url: 'https://overthewire.org/wargames/bandit/',
        kind: 'practice',
        time: '',
        by: '',
      },
      {
        title: 'Linux Operating System - Crash Course for Beginners',
        url: 'https://www.youtube.com/watch?v=ROjZy1WbCIA',
        kind: 'video',
        time: '',
        by: 'freeCodeCamp.org',
      },
    ],
    project: 'Host one of your projects on a Linux VM and set it up from the command line.',
    priority: 'prerequisite',
    hours: 15,
    done: [
      'Move around and manage files from the terminal',
      'Manage permissions, users and processes',
      'Install packages and read logs to debug a service',
    ],
    roadmap: 'https://roadmap.sh/linux',
    needed_for: ['aws'],
  },
  {
    skill: 'aws',
    what: "Amazon's cloud platform, the most widely used in industry.",
    why: 'Deploy services on AWS and keep them running.',
    resources: [
      {
        title: 'AWS Getting Started',
        url: 'https://aws.amazon.com/getting-started/',
        kind: 'tutorial',
        time: '',
        by: '',
      },
      {
        title: 'AWS Skill Builder (free courses)',
        url: 'https://skillbuilder.aws/',
        kind: 'course',
        time: '',
        by: '',
      },
      {
        title: 'AWS Certified Cloud Practitioner Certification Course (CLF-C02) - Pass the Exam!',
        url: 'https://www.youtube.com/watch?v=NhDYbskXRgc',
        kind: 'video',
        time: '',
        by: 'freeCodeCamp.org',
      },
    ],
    project: 'Deploy one of your apps on AWS (e.g. EC2 or Lambda + S3) using the free tier.',
    priority: 'must-have',
    hours: 25,
    done: [
      'Launch an EC2 instance and connect with SSH',
      'Store files in S3 and manage access with IAM',
      'Explain regions, VPCs and the main managed services',
    ],
    roadmap: 'https://roadmap.sh/aws',
    needed_for: [],
  },
  {
    skill: 'kubernetes',
    what: 'Runs and scales containers across many machines.',
    why: 'Kubernetes or another container orchestrator is a plus.',
    resources: [
      {
        title: 'Kubernetes basics (official)',
        url: 'https://kubernetes.io/docs/tutorials/kubernetes-basics/',
        kind: 'tutorial',
        time: '3 h',
        by: '',
      },
      {
        title: 'Kubernetes Tutorial for Beginners [FULL COURSE in 4 Hours]',
        url: 'https://www.youtube.com/watch?v=X48VuDVv0do',
        kind: 'video',
        time: '',
        by: 'TechWorld with Nana',
      },
    ],
    project: 'Deploy a containerized app to a local cluster (kind or minikube) with a Deployment and Service.',
    priority: 'nice-to-have',
    hours: 25,
    done: [
      'Deploy an app with a Deployment and a Service',
      'Use ConfigMaps and Secrets',
      'Debug pods with kubectl logs and describe',
    ],
    roadmap: 'https://roadmap.sh/kubernetes',
    needed_for: [],
  },
  {
    skill: 'ci/cd',
    what: 'Automatically testing and deploying code on every change.',
    why: 'Set up CI/CD pipelines for automated testing.',
    resources: [
      {
        title: 'GitHub Actions documentation',
        url: 'https://docs.github.com/en/actions',
        kind: 'docs',
        time: '3 h',
        by: '',
      },
      {
        title: 'GitHub Actions Tutorial - Basic Concepts and CI/CD Pipeline with Docker',
        url: 'https://www.youtube.com/watch?v=R8_veQiYBjI',
        kind: 'video',
        time: '',
        by: 'TechWorld with Nana',
      },
    ],
    project: 'Add a GitHub Actions workflow that runs your tests and deploys your project.',
    priority: 'mentioned',
    hours: 10,
    done: [
      'Run tests automatically on every push',
      'Build and publish an artifact or Docker image from a pipeline',
      'Deploy automatically after tests pass',
    ],
    roadmap: 'https://roadmap.sh/devops',
    needed_for: [],
  },
];

const ROLE_GAP = {
  role: 'Software Engineer',
  have: ['object-oriented programming', 'python', 'git', 'sql', 'rest api', 'docker'],
  missing: ['data structures', 'algorithms', 'java', 'linux', 'agile', 'javascript', 'c++', 'aws', 'ci/cd'],
  coverage: 0.4,
  roadmap: 'https://roadmap.sh/computer-science',
  available_roles: [
    'Software Engineer',
    'Backend Developer',
    'Frontend Developer',
    'Full-Stack Developer',
    'Mobile App Developer',
    'Data Analyst',
    'Data Scientist',
    'Machine Learning Engineer',
    'Data Engineer',
    'DevOps / Cloud Engineer',
    'Cybersecurity Analyst',
    'IT Support Specialist',
    'UI/UX Designer',
    'Graphic Designer',
    'Business Analyst',
    'Digital Marketing Specialist',
    'Accountant',
    'Financial Analyst',
    'HR Specialist',
    'Sales / Business Development',
    'Mechanical / Civil Engineer',
    'Teacher',
    'Registered Nurse',
    'Chef / Culinary',
    'Project Manager',
  ],
};

const SKILLS_INVENTORY = [
  {
    group: 'Programming languages',
    skills: [
      { skill: 'python', count: 3 },
      { skill: 'sql', count: 2 },
    ],
  },
  { group: 'Web & frameworks', skills: [{ skill: 'rest api', count: 2 }] },
  { group: 'Data & AI', skills: [{ skill: 'machine learning', count: 1 }] },
  { group: 'Cloud & DevOps', skills: [{ skill: 'docker', count: 1 }] },
  { group: 'Engineering practices', skills: [{ skill: 'git', count: 1 }] },
];

export const DEMO_HIGH_RESULT = {
  mode: 'job',
  role_gap: ROLE_GAP,
  skills_inventory: SKILLS_INVENTORY,
  match_score: 82.86,
  matched_skills: ['docker', 'git', 'machine learning', 'python', 'rest api', 'sql'],
  missing_skills: ['aws', 'ci/cd', 'kubernetes'],
  features: { tfidf_similarity: 0.2851, skill_overlap_ratio: 0.6667, resume_word_count: 612 },
  score_breakdown: { baseline: 39.33, tfidf_similarity: 20.04, skill_overlap_ratio: 24.38, resume_word_count: -0.89 },
  score_warnings: [],
  resume_skills_count: 14,
  required_skills_count: 9,
  suggested_roles: [
    { role: 'INFORMATION-TECHNOLOGY', match_percent: 71.2 },
    { role: 'ENGINEERING', match_percent: 12.4 },
    { role: 'CONSULTANT', match_percent: 4.1 },
  ],
  suggestions: [
    "'aws': This is a commonly required skill across job postings — strongly consider adding it.",
    "Consider adding 'ci/cd' to better match the job requirements.",
    "Consider adding 'kubernetes' to better match the job requirements.",
  ],
  confidence: 'high',
  student_mode: false,
  student_detected: true,
  job_insights: JOB_INSIGHTS,
  learning_plan: LEARNING_PLAN,
  resume: RESUME,
  ats: {
    score: 86.4,
    verdict: 'ATS-friendly',
    checks: [
      check('readable_text', 'format', 'Text can be read', 'pass', 'All text was extracted cleanly.'),
      check('no_tables', 'format', 'No tables', 'pass', 'No tables found.'),
      check('single_column', 'format', 'Single-column layout', 'pass', 'Text flows in a single column.'),
      check('no_images', 'format', 'No images or icons', 'pass', 'No images found.'),
      check('email', 'content', 'Email address', 'pass', 'Email address found.'),
      check(
        'standard_sections',
        'content',
        'Standard section headings',
        'pass',
        'Found Experience/Projects, Education and Skills sections.',
      ),
      check('quantified', 'content', 'Measurable results', 'pass', '3 bullet points include numbers.'),
      check(
        'length',
        'content',
        'Resume length',
        'warn',
        '232 words; 250–1,000 is typical.',
        'Add detail to projects and experience.',
      ),
      check(
        'keywords',
        'keywords',
        'Job keywords',
        'pass',
        'Your resume mentions 67% of the job’s skills.',
        'Add the skills you genuinely have from the posting: aws, ci/cd, kubernetes.',
      ),
    ],
  },
};

export const DEMO_LOW_RESULT = {
  ...DEMO_HIGH_RESULT,
  match_score: 30.49,
  matched_skills: ['git', 'python'],
  missing_skills: ['aws', 'ci/cd', 'docker', 'kubernetes', 'rest api', 'sql', 'terraform'],
  features: { tfidf_similarity: 0.0712, skill_overlap_ratio: 0.2222, resume_word_count: 168 },
  score_breakdown: { baseline: 39.33, tfidf_similarity: -8.05, skill_overlap_ratio: 3.08, resume_word_count: -3.87 },
  suggested_roles: [
    { role: 'INFORMATION-TECHNOLOGY', match_percent: 38.5 },
    { role: 'ENGINEERING', match_percent: 17.9 },
    { role: 'DESIGNER', match_percent: 9.3 },
  ],
  confidence: 'low',
  resume: { ...RESUME, skills: ['Python', 'Git'], experience: [] },
  ats: {
    score: 52.6,
    verdict: 'Needs work',
    checks: [
      check(
        'no_tables',
        'format',
        'No tables',
        'warn',
        'Found 1 table(s). Many ATS read tables cell by cell and scramble the order.',
        'Replace tables with plain lines.',
      ),
      check(
        'single_column',
        'format',
        'Single-column layout',
        'warn',
        'The page looks like it has two columns.',
        'Use a single-column layout.',
      ),
      check('email', 'content', 'Email address', 'pass', 'Email address found.'),
      check(
        'quantified',
        'content',
        'Measurable results',
        'fail',
        '0 bullet point(s) include numbers.',
        'Show impact with numbers: users, %, time saved.',
      ),
      check(
        'keywords',
        'keywords',
        'Job keywords',
        'fail',
        'Your resume mentions only 22% of the job’s skills.',
        'Add the skills you genuinely have from the posting: aws, docker, sql.',
      ),
    ],
  },
};

// Resume-only report (no job description): /?demo=resume
export const DEMO_RESUME_ONLY_RESULT = {
  ...DEMO_HIGH_RESULT,
  mode: 'resume_only',
  match_score: null,
  matched_skills: [],
  missing_skills: [],
  features: {},
  score_breakdown: {},
  score_warnings: [],
  required_skills_count: 0,
  job_insights: null,
  suggestions: ["Include a dedicated 'Projects' section to showcase practical, hands-on applications of your skills."],
  learning_plan: DEMO_HIGH_RESULT.learning_plan.map((item) =>
    item.priority === 'prerequisite'
      ? item
      : { ...item, priority: 'core-skill', why: 'A core skill for Software Engineer roles.' },
  ),
  ats: {
    ...DEMO_HIGH_RESULT.ats,
    checks: DEMO_HIGH_RESULT.ats.checks.map((c) =>
      c.id === 'keywords' ? { ...c, status: 'skip', detail: 'Add a job description to check keywords.', tip: '' } : c,
    ),
  },
};

// Display helpers for values returned by the API.
// The backend returns canonical lowercase skills ("sql", "power bi") and
// dataset category labels ("INFORMATION-TECHNOLOGY"); these turn them into
// readable labels without changing the underlying data.

const SKILL_DISPLAY = {
  'ai/ml': 'AI/ML',
  'a/b testing': 'A/B Testing',
  '.net': '.NET',
  'aws': 'AWS',
  'azure': 'Azure',
  'bim software': 'BIM Software',
  'c': 'C',
  'c#': 'C#',
  'c++': 'C++',
  'cad': 'CAD',
  'ci/cd': 'CI/CD',
  'cpr/aed certification': 'CPR/AED Certification',
  'crm': 'CRM',
  'css': 'CSS',
  'erp': 'ERP',
  'erp systems': 'ERP Systems',
  'etl': 'ETL',
  'faa regulations': 'FAA Regulations',
  'gcp': 'GCP',
  'github': 'GitHub',
  'gitlab': 'GitLab',
  'graphql': 'GraphQL',
  'hipaa compliance': 'HIPAA Compliance',
  'hr analytics': 'HR Analytics',
  'hris': 'HRIS',
  'html': 'HTML',
  'iv therapy': 'IV Therapy',
  'javascript': 'JavaScript',
  'mongodb': 'MongoDB',
  'mysql': 'MySQL',
  'node.js': 'Node.js',
  'numpy': 'NumPy',
  'php': 'PHP',
  'pl/sql': 'PL/SQL',
  'postgresql': 'PostgreSQL',
  'powerpoint': 'PowerPoint',
  'pytorch': 'PyTorch',
  'quickbooks': 'QuickBooks',
  'r': 'R',
  'rest api': 'REST API',
  'sap': 'SAP',
  'scikit-learn': 'scikit-learn',
  'seo': 'SEO',
  'servicenow': 'ServiceNow',
  'sharepoint': 'SharePoint',
  'solidworks': 'SolidWorks',
  'sql': 'SQL',
  'sql server': 'SQL Server',
  'sqlite': 'SQLite',
  'tensorflow': 'TensorFlow',
  'typescript': 'TypeScript',
  'vpn': 'VPN',
  'wordpress': 'WordPress',
};

const titleCase = (text) =>
  text.replace(/\b([a-z])([a-z]*)/g, (_, first, rest) => first.toUpperCase() + rest);

export function formatSkill(skill) {
  if (!skill) return '';
  const key = String(skill).trim().toLowerCase();
  return SKILL_DISPLAY[key] || titleCase(key);
}

const ROLE_DISPLAY = {
  BPO: 'BPO (Business Process Outsourcing)',
  HR: 'HR',
};

export function formatRole(role) {
  if (!role) return '';
  const key = String(role).trim().toUpperCase();
  if (ROLE_DISPLAY[key]) return ROLE_DISPLAY[key];
  return titleCase(key.toLowerCase().replace(/-/g, ' '));
}

export const FEATURE_LABELS = {
  baseline: 'Typical starting point',
  tfidf_similarity: 'Wording similarity to the job',
  skill_overlap_ratio: 'Required skills you have',
  resume_word_count: 'Resume length',
  range_adjustment: 'Kept within the 0–100 scale',
};

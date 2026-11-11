// Display helpers for values returned by the API.
// The backend returns canonical lowercase skills ("sql", "power bi") and
// dataset category labels ("INFORMATION-TECHNOLOGY"); these turn them into
// readable labels without changing the underlying data.

const SKILL_DISPLAY = {
  'a/b testing': 'A/B Testing',
  'ai/ml': 'AI/ML',
  'ansys': 'ANSYS',
  'api testing': 'API Testing',
  'aws': 'AWS',
  'azure': 'Azure',
  'bim software': 'BIM Software',
  'c': 'C',
  'c#': 'C#',
  'c++': 'C++',
  'cad': 'CAD',
  'catia': 'CATIA',
  'ci/cd': 'CI/CD',
  'cpr/aed certification': 'CPR/AED Certification',
  'crm': 'CRM',
  'css': 'CSS',
  'dbms': 'DBMS',
  'erp': 'ERP',
  'erp systems': 'ERP Systems',
  'etabs': 'ETABS',
  'etl': 'ETL',
  'express': 'Express',
  'faa regulations': 'FAA Regulations',
  'fastapi': 'FastAPI',
  'gcp': 'GCP',
  'generative ai': 'Generative AI',
  'github': 'GitHub',
  'gitlab': 'GitLab',
  'graphql': 'GraphQL',
  'gst': 'GST',
  'hipaa compliance': 'HIPAA Compliance',
  'hr analytics': 'HR Analytics',
  'hris': 'HRIS',
  'html': 'HTML',
  'hugging face': 'Hugging Face',
  'iot': 'IoT',
  'iv therapy': 'IV Therapy',
  'javascript': 'JavaScript',
  'langchain': 'LangChain',
  'llms': 'LLMs',
  'mlops': 'MLOps',
  'mongodb': 'MongoDB',
  'mysql': 'MySQL',
  '.net': '.NET',
  'next.js': 'Next.js',
  'node.js': 'Node.js',
  'numpy': 'NumPy',
  'opencv': 'OpenCV',
  'pandas': 'pandas',
  'pcb design': 'PCB Design',
  'php': 'PHP',
  'pl/sql': 'PL/SQL',
  'plc': 'PLC',
  'postgresql': 'PostgreSQL',
  'power bi': 'Power BI',
  'powerpoint': 'PowerPoint',
  'pytorch': 'PyTorch',
  'quickbooks': 'QuickBooks',
  'r': 'R',
  'rag': 'RAG',
  'raspberry pi': 'Raspberry Pi',
  'react native': 'React Native',
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
  'staad pro': 'STAAD Pro',
  'tailwind css': 'Tailwind CSS',
  'tensorflow': 'TensorFlow',
  'typescript': 'TypeScript',
  'ui/ux design': 'UI/UX Design',
  'vlsi': 'VLSI',
  'vpn': 'VPN',
  'wordpress': 'WordPress',
  'xgboost': 'XGBoost',
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
  keyword_list_cap: 'Mostly a keyword list (capped)',
};

"""Short, synthetic early-career resumes used to check the role classifier.

The training data contains long professional resumes (median ~760 words), but
FitLens users are often students whose resumes are short skill lists. These 19
hand-written examples (no real people) cover that case. They are used by
scripts/evaluate_pipeline.py to compare raw ML predictions with the
skill-overlap fallback, and mirror cases pinned in tests/test_role_predictor.py.
"""

SYNTHETIC_SHORT_RESUMES: list[dict[str, str]] = [
    {
        "name": "CS / AI-ML student",
        "true_role": "INFORMATION-TECHNOLOGY",
        "text": "Second-year B.Tech student in Computer Science (AI & ML) with strong foundations in "
        "C/C++, data structures and algorithms. Competitive programmer with 400+ problems "
        "solved. TECHNICAL SKILLS: C, C++, Python, Java, OOP, HTML, CSS, JavaScript, SQL. "
        "PROJECTS: Event registration portal (HTML, CSS, JavaScript); Java mini games (Java, "
        "OOP). CERTIFICATIONS: Python, React, Unix, DBMS.",
    },
    {
        "name": "Junior accounting intern",
        "true_role": "ACCOUNTANT",
        "text": "Finance student seeking junior accountant position. Experience with bookkeeping, Excel "
        "spreadsheets, general ledger entries, and financial statements. Assisted with accounts "
        "payable and accounts receivable. Familiar with QuickBooks and SAP.",
    },
    {
        "name": "UI/UX design student",
        "true_role": "DESIGNER",
        "text": "Creative design graduate proficient in Figma, Adobe Illustrator, and Photoshop. "
        "Passionate about user interface wireframes, prototypes, typography, and graphic design. "
        "Basic knowledge of HTML and CSS styling for web design.",
    },
    {
        "name": "HR recruitment assistant",
        "true_role": "HR",
        "text": "Recent Human Resources graduate with internship experience in talent acquisition, "
        "screening resumes, scheduling interviews, onboarding employees, and HR records "
        "management. Familiar with HRIS platforms, Excel, and employee relations.",
    },
    {
        "name": "Entry-level digital marketer",
        "true_role": "DIGITAL-MEDIA",
        "text": "Digital media specialist with skills in social media marketing, SEO optimization, "
        "Google Analytics, content creation, copywriting, and email marketing campaigns. "
        "Experienced in WordPress and Canva.",
    },
    {
        "name": "Frontend web developer",
        "true_role": "INFORMATION-TECHNOLOGY",
        "text": "Frontend Web Developer experienced in building responsive modern web applications with "
        "TypeScript, React, Next.js, Redux, HTML5, CSS3, Tailwind CSS, and RESTful API "
        "integration.",
    },
    {
        "name": "Python backend engineer",
        "true_role": "INFORMATION-TECHNOLOGY",
        "text": "Python Backend Software Engineer with 5 years experience designing scalable "
        "microservices, PostgreSQL databases, Redis caching, Celery background workers, and high "
        "throughput asynchronous APIs.",
    },
    {
        "name": "Certified public accountant",
        "true_role": "ACCOUNTANT",
        "text": "Certified Public Accountant (CPA) with 7 years experience handling corporate tax "
        "filings, general ledger reconciliation, GAAP compliance, financial statement audits, "
        "and QuickBooks reporting systems.",
    },
    {
        "name": "Emergency room nurse",
        "true_role": "HEALTHCARE",
        "text": "Registered Nurse (RN) with 6 years experience in hospital emergency department, triage "
        "protocols, vital signs monitoring, intravenous medication administration, and "
        "compassionate patient clinical care.",
    },
    {
        "name": "High school math teacher",
        "true_role": "TEACHER",
        "text": "High School Mathematics Teacher with 8 years experience teaching algebra, geometry, "
        "calculus, designing secondary curriculum, assessing student progress, and maintaining "
        "effective classroom management.",
    },
    {
        "name": "Executive chef",
        "true_role": "CHEF",
        "text": "Executive Chef leading high-volume culinary operations, seasonal menu engineering, food "
        "cost control, kitchen sanitation compliance standards, and fine dining classical French "
        "culinary techniques.",
    },
    {
        "name": "Full stack engineer",
        "true_role": "INFORMATION-TECHNOLOGY",
        "text": "Senior Full Stack Software Engineer with 6 years experience in Python, FastAPI, React, "
        "PostgreSQL, Docker, and AWS cloud infrastructure. Built microservices and machine "
        "learning recommendation engines.",
    },
    {
        "name": "Junior software engineer",
        "true_role": "INFORMATION-TECHNOLOGY",
        "text": "Junior Software Engineer with Python and SQL experience. Built simple database "
        "applications, REST API, Git, Docker, and Linux.",
    },
    {
        "name": "Data analyst intern",
        "true_role": "INFORMATION-TECHNOLOGY",
        "text": "Data analyst intern skilled in Python, pandas, SQL, Tableau and Power BI dashboards, "
        "statistics and Excel reporting for sales teams.",
    },
    {
        "name": "Mechanical engineering graduate",
        "true_role": "ENGINEERING",
        "text": "Mechanical engineering graduate with AutoCAD, SolidWorks, MATLAB, finite element "
        "analysis and manufacturing internship.",
    },
    {
        "name": "Line cook",
        "true_role": "CHEF",
        "text": "Line cook and culinary school graduate: knife skills, food safety, menu prep, inventory "
        "and kitchen sanitation.",
    },
    {
        "name": "Personal trainer",
        "true_role": "FITNESS",
        "text": "Personal trainer certified in CPR/AED, group fitness instruction, nutrition coaching "
        "and strength programs.",
    },
    {
        "name": "Retail sales associate",
        "true_role": "SALES",
        "text": "Sales associate with retail experience, customer service, CRM, upselling and meeting "
        "monthly sales targets.",
    },
    {
        "name": "Elementary school teacher",
        "true_role": "TEACHER",
        "text": "Elementary school teacher: lesson planning, classroom management, differentiated "
        "instruction and parent communication.",
    },
]

"""Build app/data/target_roles.json: job-title roles for resume-only gap analysis.

The classifier's 24 categories come from the dataset and are broad (its
INFORMATION-TECHNOLOGY resumes are mostly IT infrastructure), so comparing a
student's resume with them gives misleading gaps. These target roles are named
after real job titles and list their core skills in order of importance.
Every skill must exist in app/data/skills_list.json, and every dataset
category maps to a default target role.

Run:
    python scripts/build_target_roles.py
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT = REPO_ROOT / "app" / "data" / "target_roles.json"

ROLES: dict[str, list[str]] = {
    "Software Engineer": [
        "data structures",
        "algorithms",
        "object-oriented programming",
        "python",
        "java",
        "git",
        "sql",
        "rest api",
        "linux",
        "docker",
        "agile",
        "javascript",
        "c++",
        "aws",
        "ci/cd",
    ],
    "Backend Developer": [
        "rest api",
        "sql",
        "python",
        "java",
        "node.js",
        "postgresql",
        "git",
        "docker",
        "linux",
        "spring",
        "django",
        "redis",
        "aws",
        "ci/cd",
        "mongodb",
    ],
    "Frontend Developer": [
        "javascript",
        "html",
        "css",
        "react",
        "typescript",
        "git",
        "rest api",
        "angular",
        "vue",
        "figma",
        "node.js",
    ],
    "Full-Stack Developer": [
        "javascript",
        "html",
        "css",
        "react",
        "node.js",
        "sql",
        "rest api",
        "git",
        "typescript",
        "mongodb",
        "docker",
        "python",
        "aws",
    ],
    "Mobile App Developer": [
        "kotlin",
        "java",
        "swift",
        "git",
        "rest api",
        "object-oriented programming",
        "sql",
        "firebase",
    ],
    "Data Analyst": [
        "sql",
        "excel",
        "python",
        "data analysis",
        "data visualization",
        "statistics",
        "tableau",
        "power bi",
        "pandas",
        "communication",
    ],
    "Data Scientist": [
        "python",
        "machine learning",
        "statistics",
        "sql",
        "pandas",
        "numpy",
        "scikit-learn",
        "data visualization",
        "deep learning",
        "data analysis",
        "r",
    ],
    "Machine Learning Engineer": [
        "python",
        "machine learning",
        "deep learning",
        "pytorch",
        "tensorflow",
        "scikit-learn",
        "numpy",
        "pandas",
        "sql",
        "docker",
        "natural language processing",
        "computer vision",
        "git",
        "aws",
    ],
    "Data Engineer": [
        "sql",
        "python",
        "etl",
        "spark",
        "airflow",
        "kafka",
        "aws",
        "snowflake",
        "big data",
        "docker",
        "linux",
    ],
    "DevOps / Cloud Engineer": [
        "linux",
        "aws",
        "docker",
        "kubernetes",
        "ci/cd",
        "terraform",
        "git",
        "bash",
        "python",
        "azure",
        "ansible",
        "jenkins",
        "monitoring tools",
    ],
    "Cybersecurity Analyst": [
        "cybersecurity",
        "network security",
        "linux",
        "firewall",
        "penetration testing",
        "vpn",
        "python",
        "networking",
        "troubleshooting",
    ],
    "IT Support Specialist": [
        "troubleshooting",
        "technical support",
        "networking",
        "linux",
        "customer service",
        "active directory",
        "microsoft office",
        "communication",
    ],
    "UI/UX Designer": [
        "figma",
        "user research",
        "wireframing",
        "prototyping",
        "adobe creative suite",
        "html",
        "css",
        "graphic design",
        "communication",
    ],
    "Graphic Designer": [
        "adobe creative suite",
        "photoshop",
        "illustrator",
        "indesign",
        "graphic design",
        "typography",
        "creativity",
    ],
    "Business Analyst": [
        "requirements gathering",
        "sql",
        "excel",
        "data analysis",
        "stakeholder management",
        "communication",
        "power bi",
        "tableau",
        "agile",
        "jira",
        "process improvement",
    ],
    "Digital Marketing Specialist": [
        "digital marketing",
        "seo",
        "google analytics",
        "social media management",
        "content creation",
        "copywriting",
        "email marketing",
        "wordpress",
    ],
    "Accountant": [
        "accounting",
        "general ledger",
        "accounts payable",
        "accounts receivable",
        "financial reporting",
        "excel",
        "quickbooks",
        "reconciliation",
        "tax return preparation",
        "bookkeeping",
    ],
    "Financial Analyst": [
        "financial analysis",
        "financial modeling",
        "excel",
        "forecasting",
        "budgeting",
        "financial reporting",
        "data analysis",
        "sql",
        "power bi",
    ],
    "HR Specialist": [
        "talent acquisition",
        "onboarding",
        "employee relations",
        "hris",
        "payroll",
        "compensation and benefits",
        "employment law compliance",
        "communication",
    ],
    "Sales / Business Development": [
        "business development",
        "lead generation",
        "crm",
        "salesforce",
        "negotiation",
        "account management",
        "communication",
        "market research",
    ],
    "Mechanical / Civil Engineer": [
        "autocad",
        "solidworks",
        "cad",
        "project management",
        "quality control",
        "matlab",
        "technical drawing",
        "root cause analysis",
    ],
    "Teacher": [
        "lesson planning",
        "classroom management",
        "curriculum development",
        "differentiated instruction",
        "communication",
    ],
    "Registered Nurse": [
        "patient care",
        "vital signs",
        "medication administration",
        "electronic medical record systems",
        "triage",
        "infection control",
        "cpr/aed certification",
        "patient education",
    ],
    "Chef / Culinary": [
        "food safety regulations",
        "menu development",
        "inventory management",
        "cooking techniques",
        "food cost management",
    ],
    "Project Manager": [
        "project management",
        "stakeholder management",
        "agile",
        "scrum",
        "budget management",
        "risk management",
        "jira",
        "communication",
        "leadership",
    ],
}

# Default target role for each classifier category
CATEGORY_DEFAULT: dict[str, str] = {
    "INFORMATION-TECHNOLOGY": "Software Engineer",
    "ENGINEERING": "Software Engineer",
    "DESIGNER": "UI/UX Designer",
    "ARTS": "Graphic Designer",
    "DIGITAL-MEDIA": "Digital Marketing Specialist",
    "PUBLIC-RELATIONS": "Digital Marketing Specialist",
    "ACCOUNTANT": "Accountant",
    "FINANCE": "Financial Analyst",
    "BANKING": "Financial Analyst",
    "HR": "HR Specialist",
    "SALES": "Sales / Business Development",
    "BUSINESS-DEVELOPMENT": "Sales / Business Development",
    "BPO": "Sales / Business Development",
    "CONSULTANT": "Business Analyst",
    "TEACHER": "Teacher",
    "HEALTHCARE": "Registered Nurse",
    "FITNESS": "Registered Nurse",
    "CHEF": "Chef / Culinary",
    "CONSTRUCTION": "Mechanical / Civil Engineer",
    "AUTOMOBILE": "Mechanical / Civil Engineer",
    "AVIATION": "Mechanical / Civil Engineer",
    "AGRICULTURE": "Project Manager",
    "APPAREL": "Project Manager",
    "ADVOCATE": "Project Manager",
}


def main() -> None:
    taxonomy = {
        s.strip().lower() for s in json.loads((REPO_ROOT / "app/data/skills_list.json").read_text(encoding="utf-8"))
    }
    categories = set(json.loads((REPO_ROOT / "app/data/role_profiles.json").read_text(encoding="utf-8")))
    problems = []
    for role, skills in ROLES.items():
        unknown = [s for s in skills if s not in taxonomy]
        if unknown:
            problems.append(f"{role}: not in skills_list.json: {unknown}")
        if len(set(skills)) != len(skills):
            problems.append(f"{role}: duplicate skills")
    if set(CATEGORY_DEFAULT) != categories:
        problems.append(f"Category mapping mismatch: {sorted(set(CATEGORY_DEFAULT) ^ categories)}")
    if any(role not in ROLES for role in CATEGORY_DEFAULT.values()):
        problems.append("A category maps to an unknown target role")
    if problems:
        sys.exit("\n".join(problems))
    OUTPUT.write_text(
        json.dumps({"roles": ROLES, "category_default": CATEGORY_DEFAULT}, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(ROLES)} target roles to {OUTPUT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()

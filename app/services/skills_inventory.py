"""Group the skills found in a resume for an at-a-glance profile.

Technical skills are assigned to groups explicitly; generic soft skills come
from app.services.suggestions.GENERIC_SOFT_SKILLS; everything else in the
taxonomy (accounting, healthcare, sales, teaching...) is "Domain skills".
"""

from __future__ import annotations

from app.schemas.insights import InventoryGroup, InventorySkill
from app.services.data_cleaning import clean_text
from app.services.skill_extractor import extract_skill_counts
from app.services.suggestions import GENERIC_SOFT_SKILLS

GROUPS: dict[str, frozenset[str]] = {
    "Programming languages": frozenset(
        [
            *"python java c++ c# javascript typescript sql php r c ruby scala kotlin swift go rust perl matlab".split(),
            "bash",
            "shell scripting",
            "pl/sql",
        ]
    ),
    "Web & frameworks": frozenset(
        [
            "html",
            "css",
            "react",
            "angular",
            "vue",
            "node.js",
            "django",
            "flask",
            "spring",
            ".net",
            "rest api",
            "graphql",
            "wordpress",
        ]
    ),
    "Data & AI": frozenset(
        [
            "machine learning",
            "deep learning",
            "data science",
            "natural language processing",
            "computer vision",
            "statistics",
            "data visualization",
            "data analysis",
            "etl",
            "big data",
            "tensorflow",
            "pytorch",
            "scikit-learn",
            "pandas",
            "numpy",
            "hadoop",
            "spark",
            "kafka",
            "snowflake",
            "databricks",
            "airflow",
            "tableau",
            "power bi",
            "business intelligence tools",
            "data visualization tools",
        ]
    ),
    "Databases": frozenset(
        [
            "mysql",
            "postgresql",
            "oracle",
            "oracle database",
            "mongodb",
            "database",
            "redis",
            "sqlite",
            "elasticsearch",
            "cassandra",
            "sql server",
            "database management",
        ]
    ),
    "Cloud & DevOps": frozenset(
        [
            "aws",
            "azure",
            "gcp",
            "cloud platforms",
            "cloud computing",
            "docker",
            "kubernetes",
            "linux",
            "unix",
            "ci/cd",
            "jenkins",
            "terraform",
            "ansible",
            "nginx",
            "apache",
            "server management",
            "infrastructure automation",
            "virtualization technologies",
            "monitoring tools",
        ]
    ),
    "Engineering practices": frozenset(
        [
            "git",
            "github",
            "gitlab",
            "data structures",
            "algorithms",
            "object-oriented programming",
            "agile",
            "scrum",
            "jira",
            "confluence",
        ]
    ),
    "Security & networking": frozenset(
        ["cybersecurity", "network security", "vpn", "firewall", "penetration testing", "network architecture"]
    ),
    "Design": frozenset(
        [
            "figma",
            "photoshop",
            "illustrator",
            "indesign",
            "sketch",
            "invision",
            "adobe creative suite",
            "video editing",
            "autocad",
            "revit",
            "solidworks",
            "bim software",
            "cad",
            "graphic design",
        ]
    ),
    "Business & office tools": frozenset(
        [
            "excel",
            "microsoft office",
            "powerpoint",
            "word",
            "outlook",
            "visio",
            "sharepoint",
            "microsoft project",
            "salesforce",
            "sap",
            "quickbooks",
            "hris",
            "erp",
            "erp systems",
            "crm",
            "google analytics",
            "workday",
            "servicenow",
            "hubspot",
            "zendesk",
            "seo",
            "project management software",
            "reporting software",
            "electronic medical record systems",
        ]
    ),
}
SOFT_GROUP = "Soft skills"
DOMAIN_GROUP = "Domain skills"
GROUP_ORDER = [*GROUPS, DOMAIN_GROUP, SOFT_GROUP]


def group_of(skill: str) -> str:
    for group, skills in GROUPS.items():
        if skill in skills:
            return group
    return SOFT_GROUP if skill in GENERIC_SOFT_SKILLS else DOMAIN_GROUP


def build_inventory(resume_text: str) -> list[InventoryGroup]:
    """Skills found in the resume, grouped, most-mentioned first within each group."""
    counts = extract_skill_counts(clean_text(resume_text))
    grouped: dict[str, list[InventorySkill]] = {}
    for skill, count in counts.items():
        grouped.setdefault(group_of(skill), []).append(InventorySkill(skill=skill, count=count))
    return [
        InventoryGroup(group=group, skills=sorted(grouped[group], key=lambda s: (-s.count, s.skill)))
        for group in GROUP_ORDER
        if group in grouped
    ]

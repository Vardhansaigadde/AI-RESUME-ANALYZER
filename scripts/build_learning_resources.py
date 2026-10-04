"""Build and verify app/data/learning_resources.json (skill-gap learning plan).

Each entry: a one-line explanation, 1-3 free resources from official docs or
well-known free platforms, and a small project that proves the skill on a
resume. Every URL is requested before writing, and the script fails if any
link is broken, so the app never shows a dead link it hasn't checked.

Run:
    python scripts/build_learning_resources.py
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT = REPO_ROOT / "app" / "data" / "learning_resources.json"
SKILLS = REPO_ROOT / "app" / "data" / "skills_list.json"


def r(title: str, url: str, kind: str, time: str = "") -> dict:
    return {"title": title, "url": url, "kind": kind, "time": time}


KAGGLE = "https://www.kaggle.com/learn/"
MDN = "https://developer.mozilla.org/en-US/docs/"

RESOURCES: dict[str, dict] = {
    # Programming languages
    "python": {
        "what": "General-purpose language used for backends, scripting, data and machine learning.",
        "resources": [
            r("The Python Tutorial (official)", "https://docs.python.org/3/tutorial/", "docs", "6-8 h"),
            r("Kaggle Learn: Python", KAGGLE + "python", "course", "5 h"),
        ],
        "project": "Write a CLI tool that solves a real chore (e.g. renames files or tracks expenses) "
        "and publish it on GitHub.",
    },
    "java": {
        "what": "Object-oriented language behind many enterprise backends and Android apps.",
        "resources": [r("Learn Java (dev.java, official)", "https://dev.java/learn/", "docs", "10 h")],
        "project": "Build a library-management console app with classes, collections and file storage.",
    },
    "c++": {
        "what": "Fast systems language used in games, embedded software and competitive programming.",
        "resources": [r("LearnCpp.com", "https://www.learncpp.com/", "tutorial", "20 h")],
        "project": "Implement a few data structures (vector, linked list, hash map) from scratch with tests.",
    },
    "c": {
        "what": "Low-level language used in operating systems, embedded devices and drivers.",
        "resources": [
            r("Learn-C.org interactive tutorial", "https://www.learn-c.org/", "tutorial", "6 h"),
            r("CS50x (Harvard, free)", "https://cs50.harvard.edu/x/", "course", "self-paced"),
        ],
        "project": "Write a small shell or a text-file statistics tool in C.",
    },
    "c#": {
        "what": "Microsoft's main language for .NET backends, desktop apps and Unity games.",
        "resources": [
            r("C# documentation (Microsoft Learn)", "https://learn.microsoft.com/en-us/dotnet/csharp/", "docs", "8 h")
        ],
        "project": "Build a small ASP.NET Core web API with a database.",
    },
    "javascript": {
        "what": "The language of the web: interactive pages, frontends and Node.js backends.",
        "resources": [
            r("The Modern JavaScript Tutorial", "https://javascript.info/", "tutorial", "15 h"),
            r("MDN JavaScript Guide", MDN + "Web/JavaScript/Guide", "docs"),
        ],
        "project": "Make an interactive to-do or quiz app with plain JavaScript, then deploy it on GitHub Pages.",
    },
    "typescript": {
        "what": "JavaScript with types, now standard for larger frontend and Node.js codebases.",
        "resources": [
            r(
                "TypeScript Handbook (official)",
                "https://www.typescriptlang.org/docs/handbook/intro.html",
                "docs",
                "6 h",
            )
        ],
        "project": "Convert one of your JavaScript projects to TypeScript and enable strict mode.",
    },
    "go": {
        "what": "Simple, fast language popular for cloud services and developer tools.",
        "resources": [r("A Tour of Go (official)", "https://go.dev/tour/", "tutorial", "4 h")],
        "project": "Build a URL shortener HTTP service in Go.",
    },
    "rust": {
        "what": "Memory-safe systems language used for performance-critical software.",
        "resources": [
            r("The Rust Programming Language (official book)", "https://doc.rust-lang.org/book/", "book", "20 h")
        ],
        "project": "Write a command-line grep clone (the book's own project is a great start).",
    },
    "r": {
        "what": "Language for statistics, data analysis and research visualisations.",
        "resources": [r("R for Data Science (free online book)", "https://r4ds.hadley.nz/", "book", "15 h")],
        "project": "Analyse a public dataset in R and publish the report with charts.",
    },
    "php": {
        "what": "Server-side language that powers WordPress and many web apps.",
        "resources": [
            r(
                "PHP manual: getting started (official)",
                "https://www.php.net/manual/en/getting-started.php",
                "docs",
                "4 h",
            )
        ],
        "project": "Build a small blog with login and a MySQL database.",
    },
    "ruby": {
        "what": "Readable language best known for the Ruby on Rails web framework.",
        "resources": [
            r(
                "Ruby in Twenty Minutes (official)",
                "https://www.ruby-lang.org/en/documentation/quickstart/",
                "tutorial",
                "1 h",
            )
        ],
        "project": "Build a simple CRUD web app with Rails.",
    },
    "kotlin": {
        "what": "Modern JVM language and the preferred language for Android apps.",
        "resources": [
            r("Kotlin: get started (official)", "https://kotlinlang.org/docs/getting-started.html", "docs", "5 h")
        ],
        "project": "Make a simple Android notes app in Kotlin.",
    },
    "swift": {
        "what": "Apple's language for iOS and macOS apps.",
        "resources": [
            r(
                "The Swift Programming Language (official book)",
                "https://docs.swift.org/swift-book/documentation/the-swift-programming-language/",
                "book",
                "10 h",
            )
        ],
        "project": "Build a small iOS app such as a habit tracker with SwiftUI.",
    },
    # Web
    "html": {
        "what": "The structure of every web page.",
        "resources": [
            r("MDN: HTML basics", MDN + "Web/HTML", "docs", "3 h"),
            r(
                "freeCodeCamp Responsive Web Design",
                "https://www.freecodecamp.org/learn/2022/responsive-web-design/",
                "course",
                "self-paced",
            ),
        ],
        "project": "Build your own portfolio page in semantic HTML.",
    },
    "css": {
        "what": "Styling and layout for web pages, including responsive design.",
        "resources": [
            r("web.dev: Learn CSS", "https://web.dev/learn/css", "course", "8 h"),
            r("MDN CSS reference", MDN + "Web/CSS", "docs"),
        ],
        "project": "Make your portfolio responsive with Flexbox and Grid.",
    },
    "react": {
        "what": "The most widely used library for building web user interfaces.",
        "resources": [r("react.dev: Learn React (official)", "https://react.dev/learn", "docs", "8 h")],
        "project": "Build a React app that fetches data from a public API, with search and filters.",
    },
    "angular": {
        "what": "Full frontend framework by Google, common in enterprise apps.",
        "resources": [r("Angular tutorials (official)", "https://angular.dev/tutorials", "tutorial", "6 h")],
        "project": "Build a small Angular dashboard with routing and a form.",
    },
    "vue": {
        "what": "Approachable frontend framework for building interactive UIs.",
        "resources": [r("Vue.js guide (official)", "https://vuejs.org/guide/introduction.html", "docs", "6 h")],
        "project": "Build a Vue app such as a recipe finder with a public API.",
    },
    "node.js": {
        "what": "Runs JavaScript on the server to build APIs and tools.",
        "resources": [
            r(
                "Node.js: Learn (official)",
                "https://nodejs.org/en/learn/getting-started/introduction-to-nodejs",
                "docs",
                "4 h",
            )
        ],
        "project": "Build a REST API with Express and connect it to a database.",
    },
    "django": {
        "what": "Batteries-included Python web framework.",
        "resources": [
            r(
                "Django tutorial (official)",
                "https://docs.djangoproject.com/en/stable/intro/tutorial01/",
                "tutorial",
                "6 h",
            )
        ],
        "project": "Build a blog or job board with Django, user login and an admin panel.",
    },
    "flask": {
        "what": "Lightweight Python web framework for APIs and small web apps.",
        "resources": [
            r("Flask tutorial (official)", "https://flask.palletsprojects.com/en/stable/tutorial/", "tutorial", "4 h")
        ],
        "project": "Build a Flask REST API for a notes app with SQLite.",
    },
    "spring": {
        "what": "The standard Java framework (Spring Boot) for backend services.",
        "resources": [
            r("Spring quickstart (official)", "https://spring.io/quickstart", "tutorial", "1 h"),
            r("Spring guides", "https://spring.io/guides", "tutorial"),
        ],
        "project": "Build a Spring Boot REST API with a database and tests.",
    },
    ".net": {
        "what": "Microsoft's platform for web APIs, desktop and cloud apps.",
        "resources": [
            r(".NET documentation (Microsoft Learn)", "https://learn.microsoft.com/en-us/dotnet/", "docs", "8 h")
        ],
        "project": "Build an ASP.NET Core minimal API and deploy it.",
    },
    "rest api": {
        "what": "The standard way web services expose data over HTTP (GET, POST, status codes, JSON).",
        "resources": [
            r("MDN: An overview of HTTP", MDN + "Web/HTTP/Guides/Overview", "docs", "1 h"),
            r("FastAPI tutorial", "https://fastapi.tiangolo.com/tutorial/", "tutorial", "4 h"),
        ],
        "project": "Design and build a REST API for one of your projects, with docs and tests.",
    },
    "graphql": {
        "what": "Query language for APIs that lets clients ask for exactly the data they need.",
        "resources": [r("Learn GraphQL (official)", "https://graphql.org/learn/", "docs", "3 h")],
        "project": "Add a GraphQL endpoint to an existing API.",
    },
    # Tools & DevOps
    "git": {
        "what": "Version control: tracking changes and collaborating on code.",
        "resources": [
            r("Pro Git book (official, free)", "https://git-scm.com/book/en/v2", "book", "6 h"),
            r("Learn Git Branching (interactive)", "https://learngitbranching.js.org/", "practice", "2 h"),
        ],
        "project": "Keep all your projects on GitHub with clear commits, branches and pull requests.",
    },
    "github": {
        "what": "Hosting and collaboration platform for Git repositories.",
        "resources": [
            r("GitHub Docs: Get started", "https://docs.github.com/en/get-started", "docs", "2 h"),
            r("GitHub Skills (interactive)", "https://skills.github.com/", "practice"),
        ],
        "project": "Polish your GitHub profile: pinned projects, READMEs and a profile README.",
    },
    "docker": {
        "what": "Packages an app and its dependencies into containers that run the same everywhere.",
        "resources": [r("Docker: Get started (official)", "https://docs.docker.com/get-started/", "docs", "3 h")],
        "project": "Containerize one of your projects with a Dockerfile and docker compose, "
        "and mention it on your resume.",
    },
    "kubernetes": {
        "what": "Runs and scales containers across many machines.",
        "resources": [
            r(
                "Kubernetes basics (official)",
                "https://kubernetes.io/docs/tutorials/kubernetes-basics/",
                "tutorial",
                "3 h",
            )
        ],
        "project": "Deploy a containerized app to a local cluster (kind or minikube) with a Deployment and Service.",
    },
    "ci/cd": {
        "what": "Automatically testing and deploying code on every change.",
        "resources": [r("GitHub Actions documentation", "https://docs.github.com/en/actions", "docs", "3 h")],
        "project": "Add a GitHub Actions workflow that runs your tests and deploys your project.",
    },
    "jenkins": {
        "what": "Widely used automation server for CI/CD pipelines.",
        "resources": [r("Jenkins tutorials (official)", "https://www.jenkins.io/doc/tutorials/", "tutorial", "3 h")],
        "project": "Set up a Jenkins pipeline that builds and tests one of your projects.",
    },
    "terraform": {
        "what": "Infrastructure as code: defining cloud resources in config files.",
        "resources": [
            r(
                "Terraform tutorials (HashiCorp)",
                "https://developer.hashicorp.com/terraform/tutorials",
                "tutorial",
                "4 h",
            )
        ],
        "project": "Provision a small cloud setup (storage bucket + VM) with Terraform.",
    },
    "ansible": {
        "what": "Automates server configuration and deployments.",
        "resources": [
            r(
                "Getting started with Ansible (official)",
                "https://docs.ansible.com/ansible/latest/getting_started/index.html",
                "docs",
                "3 h",
            )
        ],
        "project": "Write a playbook that sets up a web server on a Linux VM.",
    },
    "linux": {
        "what": "The operating system behind most servers and cloud machines.",
        "resources": [
            r("Linux Journey", "https://linuxjourney.com/", "tutorial", "8 h"),
            r("OverTheWire: Bandit (practice)", "https://overthewire.org/wargames/bandit/", "practice"),
        ],
        "project": "Host one of your projects on a Linux VM and set it up from the command line.",
    },
    "bash": {
        "what": "The command-line shell and scripting language on Linux and macOS.",
        "resources": [
            r(
                "LinuxCommand.org: Learning the shell",
                "https://linuxcommand.org/lc3_learning_the_shell.php",
                "tutorial",
                "4 h",
            )
        ],
        "project": "Automate a repetitive task (backups, log cleanup) with a Bash script.",
    },
    "jira": {
        "what": "Issue and project tracker used by most software teams.",
        "resources": [r("Jira guides (Atlassian)", "https://www.atlassian.com/software/jira/guides", "docs", "2 h")],
        "project": "Plan a team project in Jira with epics, stories and a sprint board.",
    },
    # Cloud
    "aws": {
        "what": "Amazon's cloud platform, the most widely used in industry.",
        "resources": [
            r("AWS Getting Started", "https://aws.amazon.com/getting-started/", "tutorial"),
            r("AWS Skill Builder (free courses)", "https://skillbuilder.aws/", "course"),
        ],
        "project": "Deploy one of your apps on AWS (e.g. EC2 or Lambda + S3) using the free tier.",
    },
    "azure": {
        "what": "Microsoft's cloud platform, common in enterprises.",
        "resources": [
            r("Azure training (Microsoft Learn)", "https://learn.microsoft.com/en-us/training/azure/", "course")
        ],
        "project": "Deploy a web app to Azure App Service with the free tier.",
    },
    "gcp": {
        "what": "Google Cloud Platform, strong in data and machine learning services.",
        "resources": [
            r("Google Cloud: Get started", "https://cloud.google.com/docs/get-started", "docs"),
            r("Google Cloud Skills Boost", "https://www.cloudskillsboost.google/", "course"),
        ],
        "project": "Deploy a containerized app on Cloud Run.",
    },
    # Databases
    "sql": {
        "what": "The language for querying and managing relational databases.",
        "resources": [
            r("SQLBolt (interactive)", "https://sqlbolt.com/", "practice", "3 h"),
            r("Kaggle Learn: Intro to SQL", KAGGLE + "intro-to-sql", "course", "3 h"),
        ],
        "project": "Design a small database for a real use case (e.g. college events) and write 10 useful queries.",
    },
    "mysql": {
        "what": "Popular open-source relational database.",
        "resources": [
            r(
                "MySQL tutorial (official manual)",
                "https://dev.mysql.com/doc/refman/8.4/en/tutorial.html",
                "docs",
                "3 h",
            )
        ],
        "project": "Back one of your web projects with a MySQL database.",
    },
    "postgresql": {
        "what": "Powerful open-source relational database, a default choice for new backends.",
        "resources": [
            r("PostgreSQL tutorial (official)", "https://www.postgresql.org/docs/current/tutorial.html", "docs", "4 h")
        ],
        "project": "Move one of your projects to PostgreSQL and add indexes for its slow queries.",
    },
    "mongodb": {
        "what": "Document (NoSQL) database that stores JSON-like records.",
        "resources": [r("MongoDB University (free)", "https://learn.mongodb.com/", "course")],
        "project": "Build a small app that stores user profiles in MongoDB.",
    },
    "redis": {
        "what": "In-memory data store used for caching, queues and sessions.",
        "resources": [r("Redis docs: Get started", "https://redis.io/docs/latest/get-started/", "docs", "2 h")],
        "project": "Add Redis caching to one of your APIs and measure the speed-up.",
    },
    # Data & ML
    "machine learning": {
        "what": "Building models that learn patterns from data to make predictions.",
        "resources": [
            r(
                "Google Machine Learning Crash Course",
                "https://developers.google.com/machine-learning/crash-course",
                "course",
                "15 h",
            ),
            r("Kaggle Learn: Intro to Machine Learning", KAGGLE + "intro-to-machine-learning", "course", "3 h"),
        ],
        "project": "Train and evaluate a model on a Kaggle dataset; write up what worked and why.",
    },
    "deep learning": {
        "what": "Neural-network models for images, text and audio.",
        "resources": [
            r("Practical Deep Learning for Coders (fast.ai)", "https://course.fast.ai/", "course", "self-paced"),
            r("Dive into Deep Learning (free book)", "https://d2l.ai/", "book"),
        ],
        "project": "Fine-tune an image classifier on your own small dataset and deploy a demo.",
    },
    "tensorflow": {
        "what": "Google's deep-learning framework.",
        "resources": [r("TensorFlow tutorials (official)", "https://www.tensorflow.org/tutorials", "tutorial", "6 h")],
        "project": "Build and train a TensorFlow/Keras model for a simple classification task.",
    },
    "pytorch": {
        "what": "The most popular deep-learning framework in research and industry.",
        "resources": [
            r(
                "Learn the Basics (official PyTorch tutorial)",
                "https://docs.pytorch.org/tutorials/beginner/basics/intro.html",
                "tutorial",
                "4 h",
            )
        ],
        "project": "Train a small PyTorch model end to end and share the notebook.",
    },
    "scikit-learn": {
        "what": "Python's standard library for classic machine learning.",
        "resources": [
            r(
                "scikit-learn: Getting started (official)",
                "https://scikit-learn.org/stable/getting_started.html",
                "docs",
                "2 h",
            )
        ],
        "project": "Compare 3 models on one dataset with cross-validation and report the results.",
    },
    "pandas": {
        "what": "Python library for cleaning and analysing tabular data.",
        "resources": [
            r("Kaggle Learn: Pandas", KAGGLE + "pandas", "course", "4 h"),
            r(
                "pandas: Getting started (official)",
                "https://pandas.pydata.org/docs/getting_started/index.html",
                "docs",
            ),
        ],
        "project": "Clean and analyse a messy public dataset and summarise 5 findings.",
    },
    "numpy": {
        "what": "Python's foundation for fast numerical arrays.",
        "resources": [
            r(
                "NumPy: the absolute basics for beginners",
                "https://numpy.org/doc/stable/user/absolute_beginners.html",
                "docs",
                "2 h",
            )
        ],
        "project": "Implement linear regression from scratch with NumPy.",
    },
    "data analysis": {
        "what": "Turning raw data into answers: cleaning, summarising and interpreting.",
        "resources": [
            r("Kaggle Learn: Pandas", KAGGLE + "pandas", "course", "4 h"),
            r("Kaggle Learn: Data Cleaning", KAGGLE + "data-cleaning", "course", "4 h"),
        ],
        "project": "Answer 3 concrete questions about a public dataset and present them with charts.",
    },
    "data visualization": {
        "what": "Presenting data clearly with charts and dashboards.",
        "resources": [r("Kaggle Learn: Data Visualization", KAGGLE + "data-visualization", "course", "4 h")],
        "project": "Build a small dashboard (Tableau Public, Power BI or Python) for a dataset you care about.",
    },
    "statistics": {
        "what": "The maths behind data analysis: distributions, testing and inference.",
        "resources": [
            r(
                "Khan Academy: Statistics and probability",
                "https://www.khanacademy.org/math/statistics-probability",
                "course",
            )
        ],
        "project": "Run and explain an A/B-test style analysis on a public dataset.",
    },
    "natural language processing": {
        "what": "Teaching computers to understand and generate text.",
        "resources": [
            r(
                "Hugging Face LLM Course (free)",
                "https://huggingface.co/learn/llm-course/chapter1/1",
                "course",
                "self-paced",
            )
        ],
        "project": "Build a text classifier (e.g. spam or sentiment) and deploy a demo.",
    },
    "computer vision": {
        "what": "Models that understand images and video.",
        "resources": [r("Kaggle Learn: Computer Vision", KAGGLE + "computer-vision", "course", "4 h")],
        "project": "Train an image classifier on a small custom dataset.",
    },
    "tableau": {
        "what": "Popular business-intelligence tool for interactive dashboards.",
        "resources": [r("Tableau free training", "https://www.tableau.com/learn/training", "course")],
        "project": "Publish a dashboard on Tableau Public and link it on your resume.",
    },
    "power bi": {
        "what": "Microsoft's business-intelligence and dashboard tool.",
        "resources": [
            r(
                "Power BI training (Microsoft Learn)",
                "https://learn.microsoft.com/en-us/training/powerplatform/power-bi",
                "course",
            )
        ],
        "project": "Build a Power BI report from a public dataset and share screenshots.",
    },
    "excel": {
        "what": "Spreadsheets for analysis, reporting and modelling.",
        "resources": [
            r("Excel help & learning (Microsoft)", "https://support.microsoft.com/en-us/excel", "docs"),
            r("Excel Easy (free tutorial)", "https://www.excel-easy.com/", "tutorial"),
        ],
        "project": "Build a budget or sales tracker with formulas, pivot tables and charts.",
    },
    "spark": {
        "what": "Distributed engine for processing big data.",
        "resources": [
            r("Spark quick start (official)", "https://spark.apache.org/docs/latest/quick-start.html", "docs", "2 h")
        ],
        "project": "Process a large public dataset with PySpark and compare it with pandas.",
    },
    "hadoop": {
        "what": "Early big-data ecosystem for distributed storage and processing.",
        "resources": [r("Apache Hadoop documentation", "https://hadoop.apache.org/docs/stable/", "docs")],
        "project": "Run a word-count MapReduce job on a single-node Hadoop setup.",
    },
    "kafka": {
        "what": "Event-streaming platform for real-time data pipelines.",
        "resources": [r("Apache Kafka quickstart", "https://kafka.apache.org/quickstart", "docs", "2 h")],
        "project": "Stream events between two small services through Kafka.",
    },
    "airflow": {
        "what": "Schedules and monitors data pipelines.",
        "resources": [
            r(
                "Airflow tutorial (official)",
                "https://airflow.apache.org/docs/apache-airflow/stable/tutorial/index.html",
                "tutorial",
                "3 h",
            )
        ],
        "project": "Build a daily pipeline that fetches, cleans and stores data with Airflow.",
    },
    "etl": {
        "what": "Extract, transform, load: moving and cleaning data between systems.",
        "resources": [r("Kaggle Learn: Data Cleaning", KAGGLE + "data-cleaning", "course", "4 h")],
        "project": "Build a small ETL script that loads a public API's data into a database every day.",
    },
    # Computer science fundamentals
    "data structures": {
        "what": "Arrays, lists, stacks, queues, trees, graphs, hash maps: how data is organised in code.",
        "resources": [
            r("CS50x (Harvard, free)", "https://cs50.harvard.edu/x/", "course", "self-paced"),
            r("NeetCode roadmap (practice)", "https://neetcode.io/roadmap", "practice"),
        ],
        "project": "Solve 50+ problems on one platform and link your profile; mention the count on your resume.",
    },
    "algorithms": {
        "what": "Sorting, searching, recursion, dynamic programming and graph algorithms.",
        "resources": [
            r("CP-Algorithms", "https://cp-algorithms.com/", "docs"),
            r("LeetCode Explore", "https://leetcode.com/explore/", "practice"),
        ],
        "project": "Take part in a few contests (LeetCode, Codeforces, CodeChef) and add your rating.",
    },
    "object-oriented programming": {
        "what": "Designing code with classes, objects, inheritance and encapsulation.",
        "resources": [
            r("Python tutorial: Classes (official)", "https://docs.python.org/3/tutorial/classes.html", "docs", "2 h"),
            r("dev.java: Object-oriented programming concepts", "https://dev.java/learn/oop/", "docs", "2 h"),
        ],
        "project": "Refactor one of your projects into well-designed classes and explain the design in the README.",
    },
    # Ways of working & business tools
    "agile": {
        "what": "Iterative way of building software in short cycles with frequent feedback.",
        "resources": [r("Atlassian Agile Coach", "https://www.atlassian.com/agile", "docs", "2 h")],
        "project": "Run your next team project in sprints with a board and short retros; mention it in the bullet.",
    },
    "scrum": {
        "what": "The most common Agile framework: sprints, stand-ups, reviews and retrospectives.",
        "resources": [r("The Scrum Guide (official)", "https://scrumguides.org/scrum-guide.html", "docs", "1 h")],
        "project": "Use Scrum for a group project and describe your role (e.g. Scrum Master) on your resume.",
    },
    "figma": {
        "what": "Collaborative tool for UI design and prototypes.",
        "resources": [r("Figma Learn (official)", "https://help.figma.com/hc/en-us", "docs")],
        "project": "Redesign an app screen in Figma and add the prototype link to your portfolio.",
    },
    "seo": {
        "what": "Making websites easy to find in search engines.",
        "resources": [
            r(
                "Google SEO Starter Guide",
                "https://developers.google.com/search/docs/fundamentals/seo-starter-guide",
                "docs",
                "2 h",
            )
        ],
        "project": "Improve the SEO of a site you built and measure the change with Search Console.",
    },
    "google analytics": {
        "what": "Measuring website traffic and user behaviour.",
        "resources": [r("Google Skillshop (free certification)", "https://skillshop.withgoogle.com/", "course")],
        "project": "Add analytics to your portfolio and report one insight it gave you.",
    },
    "cybersecurity": {
        "what": "Protecting systems, networks and data from attacks.",
        "resources": [
            r("TryHackMe (beginner paths)", "https://tryhackme.com/", "practice"),
            r("Cisco Networking Academy", "https://www.netacad.com/", "course"),
        ],
        "project": "Complete a beginner path and write up a lab you solved.",
    },
    "network security": {
        "what": "Securing networks: firewalls, VPNs, monitoring and hardening.",
        "resources": [r("Cisco Networking Academy", "https://www.netacad.com/", "course")],
        "project": "Set up and document a small home-lab network with a firewall and VPN.",
    },
}


def check(url: str) -> tuple[str, int | str]:
    """GET the URL (following redirects) and return its final HTTP status."""
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 (FitLens link check)"})
    try:
        with urlopen(request, timeout=20) as response:  # noqa: S310 - fixed https URLs from this file
            return url, response.status
    except HTTPError as exc:
        return url, exc.code
    except (URLError, TimeoutError) as exc:
        return url, type(exc).__name__


def main() -> None:
    taxonomy = {s.strip().lower() for s in json.loads(SKILLS.read_text(encoding="utf-8"))}
    unknown = sorted(set(RESOURCES) - taxonomy)
    if unknown:
        sys.exit(f"Skills not in skills_list.json: {unknown}")

    urls = sorted({res["url"] for entry in RESOURCES.values() for res in entry["resources"]})
    with ThreadPoolExecutor(max_workers=12) as pool:
        results = dict(pool.map(check, urls))
    # Some sites block automated requests (403/429) even though the page exists;
    # those are reported but not treated as broken.
    broken = {u: s for u, s in results.items() if not (isinstance(s, int) and (s < 400 or s in (403, 429)))}
    blocked = {u: s for u, s in results.items() if s in (403, 429)}
    print(f"Checked {len(urls)} links: {len(urls) - len(broken)} OK, {len(blocked)} blocked bots, {len(broken)} broken")
    for url, status in sorted({**broken, **blocked}.items()):
        print(f"  {status}  {url}")
    if broken:
        sys.exit("Fix the broken links above before writing the file.")

    OUTPUT.write_text(json.dumps(RESOURCES, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(RESOURCES)} skills to {OUTPUT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()

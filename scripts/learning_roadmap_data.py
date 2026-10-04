"""Roadmap details for each skill in the learning plan (merged by build_learning_resources.py).

Per skill:
- hours:   rough hours to learn the basics and build the small project
- needs:   prerequisite skills, learned first when the resume doesn't show them
- done:    a "done when you can..." checklist (three concrete abilities)
- video:   a YouTube video id; the build script checks it exists (YouTube oEmbed)
           and stores its real title and channel
- roadmap: a roadmap.sh slug, when roadmap.sh has a roadmap for the skill

ROLE_ROADMAPS maps target roles (app/data/target_roles.json) to roadmap.sh slugs.
Every URL is checked by the build script before anything is written.
"""

from __future__ import annotations

ROADMAP: dict[str, dict] = {
    # Programming languages
    "python": {
        "hours": 25,
        "needs": [],
        "done": [
            "Write functions, loops and conditionals without looking up syntax",
            "Use lists, dicts and sets, and read/write files",
            "Install a package with pip and use it in a small script",
        ],
        "video": "rfscVS0vtbw",
        "roadmap": "python",
    },
    "java": {
        "hours": 35,
        "needs": [],
        "done": [
            "Write classes with constructors, fields and methods",
            "Use ArrayList, HashMap and exceptions correctly",
            "Build and run a multi-file project with Maven or Gradle",
        ],
        "video": "eIrMbAQSU34",
        "roadmap": "java",
    },
    "c++": {
        "hours": 40,
        "needs": [],
        "done": [
            "Explain pointers, references and stack vs heap memory",
            "Use STL containers (vector, map) and algorithms (sort, find)",
            "Write a class with a constructor, destructor and operator overload",
        ],
        "video": "vLnPwxZdW4Y",
        "roadmap": "cpp",
    },
    "c": {
        "hours": 30,
        "needs": [],
        "done": [
            "Use pointers, arrays and strings safely",
            "Allocate and free memory with malloc and free",
            "Split a program into .c and .h files and compile it with gcc",
        ],
        "video": "KJgsSFOSQv0",
        "roadmap": "",
    },
    "c#": {
        "hours": 30,
        "needs": [],
        "done": [
            "Write classes, interfaces and properties",
            "Query collections with LINQ",
            "Build and run a console app with the dotnet CLI",
        ],
        "video": "GhQdlIFylQ8",
        "roadmap": "",
    },
    "javascript": {
        "hours": 30,
        "needs": [],
        "done": [
            "Use let/const, arrow functions, arrays and objects fluently",
            "Change a web page with the DOM and handle click/input events",
            "Fetch data from an API with async/await and show it on a page",
        ],
        "video": "PkZNo7MFNFg",
        "roadmap": "javascript",
    },
    "typescript": {
        "hours": 15,
        "needs": ["javascript"],
        "done": [
            "Type functions, objects and arrays, and write interfaces",
            "Use union types and generics in your own code",
            "Set up tsconfig and convert a small JavaScript project",
        ],
        "video": "30LWjhZzg50",
        "roadmap": "typescript",
    },
    "go": {
        "hours": 25,
        "needs": [],
        "done": [
            "Write structs, methods and interfaces",
            "Handle errors the Go way and use slices and maps",
            "Run work concurrently with goroutines and channels",
        ],
        "video": "un6ZyFkqFKo",
        "roadmap": "golang",
    },
    "rust": {
        "hours": 40,
        "needs": [],
        "done": [
            "Explain ownership, borrowing and lifetimes in your own words",
            "Use structs, enums and match with Result/Option",
            "Build a small CLI with cargo and an external crate",
        ],
        "video": "BpPEoZW5IiY",
        "roadmap": "rust",
    },
    "r": {
        "hours": 25,
        "needs": [],
        "done": [
            "Load a CSV into a data frame and summarise it",
            "Clean and reshape data with dplyr",
            "Plot data with ggplot2",
        ],
        "video": "_V8eKsto3Ug",
        "roadmap": "r",
    },
    "php": {
        "hours": 25,
        "needs": ["html"],
        "done": [
            "Handle a form submission and validate input",
            "Read and write a MySQL database with PDO",
            "Use sessions for a simple login",
        ],
        "video": "OK_JCtrrv-c",
        "roadmap": "php",
    },
    "ruby": {
        "hours": 20,
        "needs": [],
        "done": [
            "Use blocks, hashes and classes",
            "Write and run tests with Minitest or RSpec",
            "Build a small CLI or script with gems",
        ],
        "video": "t_ispmWmdjY",
        "roadmap": "ruby",
    },
    "kotlin": {
        "hours": 25,
        "needs": [],
        "done": [
            "Use null safety, data classes and when expressions",
            "Use collections with map/filter",
            "Build a simple Android screen or a JVM CLI app",
        ],
        "video": "EExSSotojVI",
        "roadmap": "kotlin",
    },
    "swift": {
        "hours": 25,
        "needs": [],
        "done": [
            "Use optionals, structs and protocols",
            "Build a SwiftUI screen with state",
            "Run your app on the iOS simulator",
        ],
        "video": "comQ1-x2a1Q",
        "roadmap": "swift-ui",
    },
    # Web
    "html": {
        "hours": 10,
        "needs": [],
        "done": [
            "Structure a page with semantic tags (header, main, section, footer)",
            "Build an accessible form with labels and validation",
            "Add images, links and tables correctly",
        ],
        "video": "kUMe1FH4CHE",
        "roadmap": "html",
    },
    "css": {
        "hours": 15,
        "needs": ["html"],
        "done": [
            "Lay out a page with Flexbox and Grid",
            "Make a page responsive with media queries",
            "Explain specificity and the box model",
        ],
        "video": "OXGznpKZ_sA",
        "roadmap": "css",
    },
    "react": {
        "hours": 30,
        "needs": ["javascript", "html", "css"],
        "done": [
            "Build components with props and state (useState)",
            "Fetch data in useEffect and handle loading and errors",
            "Render lists with keys and handle forms",
        ],
        "video": "bMknfKXIFA8",
        "roadmap": "react",
    },
    "angular": {
        "hours": 30,
        "needs": ["typescript", "html", "css"],
        "done": [
            "Build components and pass data with inputs/outputs",
            "Call an API from a service with HttpClient",
            "Set up routing between pages",
        ],
        "video": "3qBXWUpoPHo",
        "roadmap": "angular",
    },
    "vue": {
        "hours": 25,
        "needs": ["javascript", "html", "css"],
        "done": [
            "Build single-file components with props and events",
            "Use reactive state and computed values",
            "Add routing with Vue Router",
        ],
        "video": "FXpIoQ_rT_c",
        "roadmap": "vue",
    },
    "node.js": {
        "hours": 25,
        "needs": ["javascript"],
        "done": [
            "Build a REST API with Express (GET, POST, PUT, DELETE)",
            "Use npm packages and environment variables",
            "Connect the API to a database",
        ],
        "video": "Oe421EPjeBE",
        "roadmap": "nodejs",
    },
    "django": {
        "hours": 30,
        "needs": ["python"],
        "done": [
            "Create models, run migrations and use the admin",
            "Build views, URLs and templates for CRUD pages",
            "Add user login with Django's auth system",
        ],
        "video": "F5mRW0jo-U4",
        "roadmap": "django",
    },
    "flask": {
        "hours": 15,
        "needs": ["python"],
        "done": [
            "Create routes that return HTML and JSON",
            "Store data with SQLite or SQLAlchemy",
            "Handle forms and errors",
        ],
        "video": "Z1RJmh_OqeA",
        "roadmap": "",
    },
    "spring": {
        "hours": 35,
        "needs": ["java", "object-oriented programming"],
        "done": [
            "Build a REST controller with Spring Boot",
            "Persist entities with Spring Data JPA",
            "Explain dependency injection and write a service test",
        ],
        "video": "9SGDpanrc8U",
        "roadmap": "spring-boot",
    },
    ".net": {
        "hours": 35,
        "needs": ["c#"],
        "done": [
            "Build a web API or MVC app with ASP.NET Core",
            "Use Entity Framework Core for database access",
            "Configure dependency injection and app settings",
        ],
        "video": "hZ1DASYd9rk",
        "roadmap": "aspnet-core",
    },
    "rest api": {
        "hours": 12,
        "needs": [],
        "done": [
            "Explain HTTP methods, status codes and JSON bodies",
            "Design resource URLs for a small app",
            "Call and test an API with curl or Postman",
        ],
        "video": "lsMQRaeKNDk",
        "roadmap": "api-design",
    },
    "graphql": {
        "hours": 15,
        "needs": ["rest api"],
        "done": [
            "Write queries and mutations against a public GraphQL API",
            "Define a schema with types and resolvers",
            "Explain when GraphQL is a better fit than REST",
        ],
        "video": "ed8SzALpx1Q",
        "roadmap": "graphql",
    },
    # Tools & DevOps
    "git": {
        "hours": 8,
        "needs": [],
        "done": [
            "Commit, branch, merge and resolve a merge conflict",
            "Push to and pull from a remote repository",
            "Undo mistakes with restore, revert and reset",
        ],
        "video": "RGOj5yH7evk",
        "roadmap": "git-github",
    },
    "github": {
        "hours": 5,
        "needs": ["git"],
        "done": [
            "Open a pull request and respond to review comments",
            "Write a clear README for a project",
            "Set up a simple GitHub Actions workflow",
        ],
        "video": "dSl_qnWO104",
        "roadmap": "git-github",
    },
    "docker": {
        "hours": 15,
        "needs": ["linux"],
        "done": [
            "Write a Dockerfile for your own app and build an image",
            "Run containers with ports, volumes and environment variables",
            "Run an app and its database together with Docker Compose",
        ],
        "video": "fqMOX6JJhGo",
        "roadmap": "docker",
    },
    "kubernetes": {
        "hours": 25,
        "needs": ["docker"],
        "done": [
            "Deploy an app with a Deployment and a Service",
            "Use ConfigMaps and Secrets",
            "Debug pods with kubectl logs and describe",
        ],
        "video": "X48VuDVv0do",
        "roadmap": "kubernetes",
    },
    "ci/cd": {
        "hours": 10,
        "needs": ["git"],
        "done": [
            "Run tests automatically on every push",
            "Build and publish an artifact or Docker image from a pipeline",
            "Deploy automatically after tests pass",
        ],
        "video": "R8_veQiYBjI",
        "roadmap": "devops",
    },
    "jenkins": {
        "hours": 12,
        "needs": ["ci/cd"],
        "done": [
            "Write a declarative Jenkinsfile with build and test stages",
            "Trigger builds from a Git repository",
            "Store credentials safely in Jenkins",
        ],
        "video": "7KCS70sCoK0",
        "roadmap": "",
    },
    "terraform": {
        "hours": 15,
        "needs": ["aws"],
        "done": [
            "Write resources, variables and outputs",
            "Run plan and apply, and explain the state file",
            "Split infrastructure into a reusable module",
        ],
        "video": "SLB_c_ayRMo",
        "roadmap": "terraform",
    },
    "ansible": {
        "hours": 12,
        "needs": ["linux"],
        "done": [
            "Write an inventory and run ad-hoc commands",
            "Write a playbook that installs and configures a service",
            "Use variables, handlers and roles",
        ],
        "video": "s4cXrNEDYiw",
        "roadmap": "",
    },
    "linux": {
        "hours": 15,
        "needs": [],
        "done": [
            "Move around and manage files from the terminal",
            "Manage permissions, users and processes",
            "Install packages and read logs to debug a service",
        ],
        "video": "ROjZy1WbCIA",
        "roadmap": "linux",
    },
    "bash": {
        "hours": 8,
        "needs": ["linux"],
        "done": [
            "Write a script with variables, if-statements and loops",
            "Pipe commands together with grep, sort and awk",
            "Schedule a script with cron",
        ],
        "video": "tK9Oc6AEnR4",
        "roadmap": "shell-bash",
    },
    "jira": {
        "hours": 3,
        "needs": ["agile"],
        "done": [
            "Create epics, stories and sub-tasks",
            "Run a sprint on a Scrum board",
            "Filter issues and read a burndown chart",
        ],
        "video": "8jWKwiIcWPI",
        "roadmap": "",
    },
    # Cloud
    "aws": {
        "hours": 25,
        "needs": ["linux"],
        "done": [
            "Launch an EC2 instance and connect with SSH",
            "Store files in S3 and manage access with IAM",
            "Explain regions, VPCs and the main managed services",
        ],
        "video": "NhDYbskXRgc",
        "roadmap": "aws",
    },
    "azure": {
        "hours": 20,
        "needs": [],
        "done": [
            "Create resources in a resource group from the portal and CLI",
            "Deploy a web app to App Service",
            "Explain Azure identity, storage and networking basics",
        ],
        "video": "NKEFWyqJ5XA",
        "roadmap": "",
    },
    "gcp": {
        "hours": 20,
        "needs": [],
        "done": [
            "Create a project and use Cloud Shell and gcloud",
            "Deploy a container to Cloud Run",
            "Store data in Cloud Storage and query it with BigQuery",
        ],
        "video": "jpno8FSqpc8",
        "roadmap": "",
    },
    # Databases
    "sql": {
        "hours": 15,
        "needs": [],
        "done": [
            "Write SELECT queries with WHERE, ORDER BY and LIMIT",
            "Combine tables with JOINs and summarise with GROUP BY",
            "Create tables with keys and insert, update and delete rows",
        ],
        "video": "HXV3zeQKqGY",
        "roadmap": "sql",
    },
    "mysql": {
        "hours": 10,
        "needs": ["sql"],
        "done": [
            "Install MySQL and design a small schema",
            "Add indexes and explain why a query is slow",
            "Back up and restore a database",
        ],
        "video": "7S_tz1z_5bA",
        "roadmap": "sql",
    },
    "postgresql": {
        "hours": 12,
        "needs": ["sql"],
        "done": [
            "Design tables with constraints and foreign keys",
            "Use indexes and EXPLAIN to speed up a query",
            "Use transactions and JSONB columns",
        ],
        "video": "qw--VYLpxG4",
        "roadmap": "postgresql-dba",
    },
    "mongodb": {
        "hours": 10,
        "needs": [],
        "done": [
            "Model data as documents and collections",
            "Query, update and index documents",
            "Group data with the aggregation pipeline",
        ],
        "video": "c2M-rlkkT5o",
        "roadmap": "mongodb",
    },
    "redis": {
        "hours": 8,
        "needs": [],
        "done": [
            "Use strings, hashes, lists and sets",
            "Cache API responses with an expiry time",
            "Explain when to use Redis and when not to",
        ],
        "video": "XCsS_NVAa1g",
        "roadmap": "redis",
    },
    # Data & ML
    "machine learning": {
        "hours": 40,
        "needs": ["python", "statistics"],
        "done": [
            "Split data into train and test sets and avoid data leakage",
            "Train and compare a regression and a classification model",
            "Choose and explain metrics (accuracy, precision/recall, RMSE)",
        ],
        "video": "i_LwzRVP7bg",
        "roadmap": "machine-learning",
    },
    "deep learning": {
        "hours": 40,
        "needs": ["machine learning"],
        "done": [
            "Explain neurons, layers, loss and backpropagation",
            "Train a neural network and spot overfitting",
            "Use a pretrained model for a new task (transfer learning)",
        ],
        "video": "aircAruvnKk",
        "roadmap": "machine-learning",
    },
    "tensorflow": {
        "hours": 20,
        "needs": ["deep learning"],
        "done": [
            "Build and train a Keras model",
            "Load data with tf.data and evaluate the model",
            "Save, load and serve predictions from the model",
        ],
        "video": "tPYj3fFJGjk",
        "roadmap": "",
    },
    "pytorch": {
        "hours": 20,
        "needs": ["deep learning"],
        "done": [
            "Work with tensors and autograd",
            "Write a training loop with Dataset and DataLoader",
            "Fine-tune a pretrained model",
        ],
        "video": "V_xro1bcAuA",
        "roadmap": "",
    },
    "scikit-learn": {
        "hours": 15,
        "needs": ["python", "pandas"],
        "done": [
            "Build a Pipeline with preprocessing and a model",
            "Tune hyperparameters with cross-validation",
            "Evaluate a model with the right metrics and a confusion matrix",
        ],
        "video": "pqNCD_5r0IU",
        "roadmap": "",
    },
    "pandas": {
        "hours": 12,
        "needs": ["python"],
        "done": [
            "Load CSV/Excel files and explore them",
            "Clean data: missing values, types and duplicates",
            "Filter, group, merge and pivot data",
        ],
        "video": "vmEHCJofslg",
        "roadmap": "",
    },
    "numpy": {
        "hours": 6,
        "needs": ["python"],
        "done": [
            "Create and reshape arrays",
            "Use vectorised operations instead of loops",
            "Index and slice arrays with boolean masks",
        ],
        "video": "QUT1VHiLmmI",
        "roadmap": "",
    },
    "data analysis": {
        "hours": 25,
        "needs": ["sql"],
        "done": [
            "Clean a messy dataset and document your steps",
            "Answer a business question with summary statistics",
            "Present findings in a short report with charts",
        ],
        "video": "r-uOLxNrNk8",
        "roadmap": "data-analyst",
    },
    "data visualization": {
        "hours": 10,
        "needs": [],
        "done": [
            "Pick the right chart for comparison, trend and distribution",
            "Build clear charts with labels and no clutter",
            "Combine charts into a dashboard that tells one story",
        ],
        "video": "a9UrKTVEeZA",
        "roadmap": "",
    },
    "statistics": {
        "hours": 25,
        "needs": [],
        "done": [
            "Explain mean, median, variance and distributions",
            "Run and interpret a hypothesis test and a p-value",
            "Explain correlation vs causation with an example",
        ],
        "video": "xxpc-HPKN28",
        "roadmap": "",
    },
    "natural language processing": {
        "hours": 25,
        "needs": ["machine learning"],
        "done": [
            "Clean and tokenise text, and build TF-IDF features",
            "Train a text classifier and evaluate it",
            "Use a pretrained transformer for a text task",
        ],
        "video": "dIUTsFT2MeQ",
        "roadmap": "",
    },
    "computer vision": {
        "hours": 25,
        "needs": ["python"],
        "done": [
            "Load, resize and filter images with OpenCV",
            "Train or fine-tune an image classifier",
            "Explain how CNNs process images",
        ],
        "video": "oXlwWbU8l2o",
        "roadmap": "",
    },
    "tableau": {
        "hours": 12,
        "needs": [],
        "done": [
            "Connect data and build bar, line and map charts",
            "Use calculated fields and filters",
            "Publish an interactive dashboard to Tableau Public",
        ],
        "video": "TPMlZxRRaBQ",
        "roadmap": "",
    },
    "power bi": {
        "hours": 12,
        "needs": ["excel"],
        "done": [
            "Import and clean data with Power Query",
            "Model tables and write basic DAX measures",
            "Build an interactive report with slicers",
        ],
        "video": "TmhQCQr_DCA",
        "roadmap": "bi-analyst",
    },
    "excel": {
        "hours": 10,
        "needs": [],
        "done": [
            "Use XLOOKUP/VLOOKUP, IF and SUMIFS",
            "Summarise data with PivotTables and charts",
            "Clean data with text functions and remove duplicates",
        ],
        "video": "Vl0H-qTclOg",
        "roadmap": "",
    },
    "spark": {
        "hours": 20,
        "needs": ["python", "sql"],
        "done": [
            "Load and transform data with PySpark DataFrames",
            "Query data with Spark SQL",
            "Explain partitions, transformations and actions",
        ],
        "video": "_C8kWso4ne4",
        "roadmap": "",
    },
    "hadoop": {
        "hours": 15,
        "needs": ["linux"],
        "done": [
            "Explain HDFS, YARN and MapReduce",
            "Move files in and out of HDFS",
            "Run a word-count MapReduce job",
        ],
        "video": "mafw2-CVYnA",
        "roadmap": "",
    },
    "kafka": {
        "hours": 15,
        "needs": [],
        "done": [
            "Explain topics, partitions, producers and consumers",
            "Write a producer and a consumer in your language",
            "Explain consumer groups and offsets",
        ],
        "video": "CU44hKLMg7k",
        "roadmap": "",
    },
    "airflow": {
        "hours": 12,
        "needs": ["python"],
        "done": [
            "Write a DAG with dependent tasks",
            "Schedule, retry and backfill runs",
            "Pass data between tasks and monitor runs in the UI",
        ],
        "video": "K9AnJ9_ZAXE",
        "roadmap": "",
    },
    "etl": {
        "hours": 15,
        "needs": ["sql", "python"],
        "done": [
            "Extract data from an API or files",
            "Transform and validate it with pandas or SQL",
            "Load it into a database on a schedule",
        ],
        "video": "BqVSs52B71o",
        "roadmap": "data-engineer",
    },
    # CS fundamentals & practices
    "data structures": {
        "hours": 30,
        "needs": [],
        "done": [
            "Implement a linked list, stack, queue and hash map",
            "Explain Big-O for common operations on each structure",
            "Use trees and graphs to solve practice problems",
        ],
        "video": "RBSGKlAvoiM",
        "roadmap": "datastructures-and-algorithms",
    },
    "algorithms": {
        "hours": 40,
        "needs": ["data structures"],
        "done": [
            "Solve problems with two pointers, binary search and sorting",
            "Use recursion, BFS/DFS and basic dynamic programming",
            "Solve 50+ easy/medium practice problems on LeetCode or similar",
        ],
        "video": "8hly31xKli0",
        "roadmap": "datastructures-and-algorithms",
    },
    "object-oriented programming": {
        "hours": 12,
        "needs": [],
        "done": [
            "Explain encapsulation, inheritance and polymorphism with code",
            "Design classes for a small system (e.g. a library or a bank)",
            "Prefer composition over inheritance where it fits",
        ],
        "video": "SiBw7os-_zI",
        "roadmap": "",
    },
    "agile": {
        "hours": 3,
        "needs": [],
        "done": [
            "Explain the Agile values and iterative delivery",
            "Write user stories with acceptance criteria",
            "Compare Scrum and Kanban",
        ],
        "video": "Z9QbYZh1YXY",
        "roadmap": "",
    },
    "scrum": {
        "hours": 3,
        "needs": ["agile"],
        "done": [
            "Explain the Scrum roles, events and artifacts",
            "Plan a sprint and estimate stories",
            "Run a stand-up and a retrospective",
        ],
        "video": "XU0llRltyFM",
        "roadmap": "",
    },
    # Design & marketing
    "figma": {
        "hours": 10,
        "needs": [],
        "done": [
            "Design a screen with frames, auto layout and components",
            "Build a clickable prototype",
            "Hand off a design with styles and spacing developers can follow",
        ],
        "video": "jwCmIBJ8Jtc",
        "roadmap": "ux-design",
    },
    "seo": {
        "hours": 8,
        "needs": [],
        "done": [
            "Do keyword research for a topic",
            "Optimise titles, headings and meta descriptions",
            "Check a site with Google Search Console",
        ],
        "video": "DvwS7cV9GmQ",
        "roadmap": "",
    },
    "google analytics": {
        "hours": 6,
        "needs": [],
        "done": [
            "Set up GA4 on a website",
            "Track events and conversions",
            "Build a report that answers a marketing question",
        ],
        "video": "pRKpaZJJRxk",
        "roadmap": "",
    },
    # Security
    "cybersecurity": {
        "hours": 30,
        "needs": ["linux"],
        "done": [
            "Explain the CIA triad and common attacks (phishing, malware, injection)",
            "Use basic tools such as Nmap and Wireshark in a lab",
            "Harden a Linux machine and explain each step",
        ],
        "video": "hXSFdwIOfnE",
        "roadmap": "cyber-security",
    },
    "network security": {
        "hours": 25,
        "needs": ["linux"],
        "done": [
            "Explain the OSI model, TCP/IP, DNS and subnets",
            "Configure firewall rules and a VPN",
            "Read packet captures to spot suspicious traffic",
        ],
        "video": "qiQR5rTSshw",
        "roadmap": "cyber-security",
    },
}

ROLE_ROADMAPS: dict[str, str] = {
    "Software Engineer": "computer-science",
    "Backend Developer": "backend",
    "Frontend Developer": "frontend",
    "Full-Stack Developer": "full-stack",
    "Mobile App Developer": "android",
    "Data Analyst": "data-analyst",
    "Data Scientist": "ai-data-scientist",
    "Machine Learning Engineer": "machine-learning",
    "Data Engineer": "data-engineer",
    "DevOps / Cloud Engineer": "devops",
    "Cybersecurity Analyst": "cyber-security",
    "UI/UX Designer": "ux-design",
    "Business Analyst": "bi-analyst",
}

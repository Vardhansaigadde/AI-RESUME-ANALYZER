# Deployment & Container Environment Report

**Date**: 2026-09-27  
**Status**: Docker CLI / Daemon Unavailable — **Dockerfile is UNTESTED Locally**  
**Target Environments**: Render (Backend Web Service / Docker), Vercel (Frontend SPA)

---

## 1. Environment Investigation & Docker Capability Diagnosis

An exhaustive check was performed in the host environment to determine whether Docker Desktop or the Docker CLI could be installed and executed:

| Diagnostic Check | Command / Query | Result | Implication |
| :--- | :--- | :--- | :--- |
| **Docker CLI Existence** | `Get-Command docker` | `CommandNotFoundException` | Neither Docker CLI nor Docker Engine is installed or on `PATH`. |
| **Alternative Container Tools** | `Get-Command podman, nerdctl, minikube` | Not found | No alternative OCI container runtimes exist on the system. |
| **Process Elevation** | `[Security.Principal.WindowsPrincipal]::IsInRole("Administrator")` | `False` | The current session runs as a standard, non-elevated user. |
| **WSL2 Architecture** | `wsl --version; wsl -l -v` | WSL v2.5.9.0 present; **No installed distributions** | WSL2 backend has no Linux distributions (e.g. Ubuntu) provisioned. |
| **Winget Package Manager** | `winget --version` | `v1.29.380` (requires interactive prompt) | Silent system-level installer cannot run without elevation. |

### Why Docker Desktop Cannot Be Installed in this Environment:
1. **Administrative Rights Required**: Installing Docker Desktop on Windows registers system-level services (`com.docker.service`) and network drivers, which require interactive Windows User Account Control (UAC) administrative privileges.
2. **Missing WSL2 Linux Distribution**: Docker Desktop WSL2 backend requires an active Linux distribution. Running `wsl.exe --install` requires administrative elevation and a machine restart.
3. **Daemon / GUI Agreement**: Docker Desktop requires an interactive desktop session to accept the Docker Subscription Service Agreement and start the background virtual machine/daemon.

**Conclusion**: Docker genuinely **cannot** be installed or run in this automated agent environment.

---

## 2. Explicit Verification Status: Dockerfile is UNTESTED

> [!WARNING]
> **UNTESTED LOCAL CONTAINER ARTIFACT**:  
> Because Docker cannot run in this environment, **no Docker image was built locally (`docker build -t resume-analyzer .`) and no container was executed (`docker run -p 8000:8000 resume-analyzer`)**.  
> The `Dockerfile` has undergone static review only. It must **not** be assumed verified until built and tested on a host machine with an active Docker daemon or validated via automated build logs upon deployment to Render.

---

## 3. Static Audit of `Dockerfile` & `.dockerignore`

The repository contains a standalone [`Dockerfile`](../Dockerfile) and [`.dockerignore`](../.dockerignore) designed for cloud deployments:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
COPY models/ ./models/
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Static Audit Observations:
- **Base Image**: `python:3.11-slim` provides a minimal Debian environment with low attack surface and small image size.
- **Layer Caching**: `COPY requirements.txt .` precedes `COPY app/`, preventing code edits from invalidating the heavy `pip install` dependency cache layer.
- **Dependencies**: Uses `--no-cache-dir` to prevent wheel caching and keep image footprint small.
- **Required Model Artifacts**: Explicitly copies `models/` into `/app/models/`, matching the relative path expectation of `app.services.matcher` and `app.services.role_predictor`.
- **Health Check**: Configured against `http://localhost:8000/` using `curl`.
- **Potential Gotcha on Render**: Render injects a dynamic `$PORT` environment variable. While `PORT=8000` is default, `uvicorn` in `CMD` hardcodes `--port 8000`. In `render.yaml`, Render handles port mapping automatically or through its blueprint configuration.

---

## 4. Pre-Production Verification Checklist (Once on Docker / Render)

When deploying to Render or running on a developer machine with Docker installed, execute the following verification steps:

1. **Build Verification**:
   ```bash
   docker build -t resume-analyzer .
   ```
   *Confirm*: Build exits with code 0; image size is under ~1 GB.

2. **Container Run & Healthcheck**:
   ```bash
   docker run -d --name resume-analyzer-test -p 8000:8000 resume-analyzer
   docker ps
   # Wait 10 seconds, confirm container status is "healthy"
   ```

3. **Live Endpoint Test**:
   ```bash
   curl -X POST http://localhost:8000/api/analyze \
     -H "Content-Type: application/json" \
     -d '{
       "resume_text": "Experienced Full Stack Python Software Engineer with FastAPI, Docker, and PostgreSQL.",
       "job_text": "Seeking a Python Backend Software Engineer proficient in FastAPI, SQL databases, and containerization."
     }'
   ```
   *Confirm*: Returns HTTP 200 with `match_score`, `suggested_roles`, and `confidence` fields.

4. **Cleanup**:
   ```bash
   docker stop resume-analyzer-test && docker rm resume-analyzer-test
   ```

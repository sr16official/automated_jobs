# AI Job Agent Deployment Guide

This guide provides instructions for deploying the AI Job Agent system to a production environment.

## 🚀 Quick Start (Local)

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt fastapi uvicorn beautifulsoup4 lxml
   ```
2. **Environment Variables**:
   Create a `.env` file or export:
   ```bash
   export FIRECRAWL_API_KEY="your_firecrawl_key"
   export XIAOMI_API_KEY="your_llm_key"
   export XIAOMI_BASE_URL="optional_custom_endpoint"
   ```
3. **Launch Dashboard**:
   ```bash
   python api/main.py
   ```
   Access at `http://localhost:8000`.

---

## ☁️ Cloud Deployment (Render / Railway)

### 1. Repository Setup
Push your code to a private GitHub repository. **DO NOT** commit `credentials.json` or `token.json` if they contain sensitive personal data.

### 2. Configure Build & Start
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python -m uvicorn api.main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables**:
  - `PYTHONPATH`: `.`
  - `FIRECRAWL_API_KEY`: [Get from Firecrawl](https://firecrawl.dev)
  - `XIAOMI_API_KEY`: [Your LLM Key]

### 3. Persistent Storage (SQLite)
Since the agent uses SQLite (`jobs.db`), you must use a **Persistent Disk** (Render) or a volume (Railway/Docker).
- Mount point: `/app/db`
- Update your database path in code if necessary to point to this volume.

---

## 🐋 Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure DB and Token persistence
VOLUME /app/db
VOLUME /app/config

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 📧 Google Auth Setup in Cloud

To use Gmail automation in the cloud:
1. Run `python scripts/setup_gmail.py` locally to generate `token.json`.
2. Upload `token.json` (and `credentials.json`) to your server's `config/` directory via SSH or secret management.
3. **Alternatively**, use the environment variables to store the contents of these JSON files and write them to disk at runtime if your platform doesn't support persistent file storage.

---

## 🛠️ Maintenance & Monitoring
- **Logs**: Monitor the FastAPI logs for detailed agent step execution.
- **Dashboard**: Use the built-in activity log to verify search and ranking status.
- **RSS**: Use the "RSS Feed URL" field for high-reliability sourcing from LinkedIn.

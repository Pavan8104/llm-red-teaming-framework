# SENTINEL AI — DEVOPS DEPLOYMENT MANIFEST

This document contains the structural report of the Sentinel AI application stack, meticulously compiled for immediate Dockerization and CI/CD pipeline integration. It outlines absolute specifications for both the backend evaluation pipeline and the frontend React application.

---

## 1. PROJECT OVERVIEW

* **Project Name:** Sentinel AI — LLM Red Teaming Framework
* **Purpose:** A robust, automated framework for adversarially testing Large Language Models (LLMs) against safety vulnerabilities, strict compliance guidelines, and alignment principles using dynamic prompt evaluation mechanisms.
* **Tech Stack:**
  * **Backend Framework:** FastAPI (Python 3.14+), executing asynchronously via Uvicorn.
  * **Frontend Framework:** React 19 bootstrapped with Vite, heavily utilizing custom CSS and Chart.js.
  * **Data & Storage Layer:** SQLite with JSON-based file-system persistence mechanisms.
  * **Primary API Integrations:** OpenAI API.

---

## 2. REPOSITORY FOLDER STRUCTURE

```text
llm-red-teaming-framework/
├── .env.example              # CI/CD secret mapping template
├── .gitignore
├── requirements.txt          # Python production dependencies (MUST install)
├── requirements-dev.txt      # Python development dependencies
├── README.md
├── PROJECT_SUMMARY.md 
├── main.py                   # Legacy CLI entry point (Deprecated for web flow)
├── app.py                    # Legacy Streamlit entry point (Deprecated)
│
├── api/                      # External LLM Client modules
├── attacks/                  # Attack taxonomy generators
├── defense/                  # Guardrails & filters
├── evaluation/               # Grading algorithms
├── experiments/              # Database models and storage logic
│
├── api_server/               # ← PRIMARY BACKEND CONTEXT
│   └── fast_server.py        # Main FastAPI ASGI application
│
└── frontend/                 # ← PRIMARY FRONTEND CONTEXT
    ├── package.json          # Node.js manifest
    ├── vite.config.js        # Vite build configuration
    ├── index.html            # Vite HTML template
    └── src/
        ├── main.jsx          # React DOM hydration entry
        ├── App.jsx           # Frontend dashboard logic layer
        └── index.css         # Glassmorphic UI styles
```

---

## 3. BACKEND INFRASTRUCTURE DETAILS

* **Entry File Execution:** `api_server/fast_server.py`
  *(CRITICAL: Execution MUST occur from the repository root `/` to resolve sibling module `sys.path` injection).*
* **Framework Protocol:** FastAPI / ASGI
* **Container Port Exposure:** `8000` (Standard Uvicorn configuration)
* **Required `requirements.txt` Content:**
```text
openai>=1.30.0
python-dotenv>=1.0.0
fastapi>=0.109.0
uvicorn>=0.27.0
pydantic>=2.0.0
```
* **Production Run Command:**
```bash
uvicorn api_server.fast_server:app --host 0.0.0.0 --port 8000
```

---

## 4. FRONTEND INFRASTRUCTURE DETAILS

* **Framework Engine:** React 19 with Vite bundler
* **Container Build Command (Docker Stage 1):**
```bash
cd frontend
npm install
npm run build
```
* **Production Static Output Directory:** `frontend/dist/`
  *(CRITICAL: An engine like Nginx, Traefik, or an S3/CloudFront bucket MUST serve the contents of this folder in production.)*
* **Local Development Command:**
```bash
cd frontend
npm run dev
```

---

## 5. MICROSERVICE CONNECTION MAPPING

* **Network Protocol:** The frontend consumes the backend entirely via stateless HTTP POST/GET requests utilizing the `axios` library.
* **Base Evaluation URL Endpoint:** Currently explicitly statically mapped in `frontend/src/App.jsx` pointing to:
  `http://127.0.0.1:8000/api/evaluate`
* **DevOps Action Required:** To support container networking, an environment variable (e.g., `import.meta.env.VITE_API_BASE_URL`) MUST be configured inside `App.jsx` to replace `127.0.0.1`, redirecting to a reverse-proxy (e.g., `/api`).

---

## 6. ENVIRONMENT VARIABLES CONFIGURATION

The FastAPI execution context strictly expects the following key-value pairs mounted into its instance layer (based on `.env.example` mapping):

* `OPENAI_API_KEY` (Required for primary evaluation loop execution)
* `ANTHROPIC_API_KEY`
* `SENTINEL_MODEL` (Default: `gpt-4o-mini`)
* `SENTINEL_TEMPERATURE` (Default: `0.7`)
* `SENTINEL_MAX_TOKENS`
* `SENTINEL_MAX_RETRIES`
* `SENTINEL_GUARDRAIL_MODE` (Parameters allowed: `observe` or `block`)
* `SENTINEL_UNSAFE_THRESHOLD` (Numeric 0-1, Default: `0.4`)
* `SENTINEL_EXPERIMENT_NAME`
* `SENTINEL_LOG_LEVEL`
* `SENTINEL_SAVE_RESULTS` (Boolean equivalent)
* `SENTINEL_DB_PATH`
* `SENTINEL_REQUESTS_PER_MINUTE`
* `SENTINEL_MAX_CONCURRENT`

---

## 7. DEPENDENCY CHAIN

### Python Virtual Environment (`pip`)
* Found in `/requirements.txt`
* Core Libs: `openai`, `python-dotenv`, `fastapi`, `uvicorn`, `pydantic`.

### Node Modules (`npm`)
* Found in `/frontend/package.json`
* UI / Functional: `react`, `react-dom`, `axios`, `lucide-react`
* Visual / Graphs: `chart.js`, `react-chartjs-2`
* Build Chain: `vite`, `@vitejs/plugin-react`, `eslint`

---

## 8. SPECIALIZED ORCHESTRATION CONFIGS

* `frontend/vite.config.js`: Handled dynamically by the Vite compilation tree. Can be modified proxy-wise to route `/api` dynamically during development.
* **Missing Orchestration Files:** Currently missing `Dockerfile` layers for independent backend/frontend contexts, `.dockerignore`, and `.github/workflows/main.yml`. These configs must be artificially synthesized upon initialization of the CI/CD pipeline using the precise execution parameters detailed in this manifest.

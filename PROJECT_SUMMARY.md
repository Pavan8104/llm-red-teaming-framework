# Project Summary: Sentinel AI — LLM Red Teaming Framework

This document outlines the features and components that have been successfully implemented in the LLM Red Teaming Framework repository based on the project's commit history and structural design.

## Core Pipeline Implementation
The entire testing pipeline is wired up and functional: `Attacks (Generation & Mutation) → Evaluation (Scoring) → Defense (Filtering) → Experiments (Save & Report)`. 
The framework provides both a centralized CLI (`main.py`) for scriptable execution and a decoupled **Vite React + FastAPI web stack** for an interactive, dashboard-driven experience.

## 1. Attacks (Prompt Generation & Mutation)
The framework supports generating and executing adversarial prompts across a large taxonomy of attack vectors.
* **Extended Prompt Generator:** Added support for over 40 distinct attacks across 14 extended attack categories (e.g., jailbreaks, prompt injection, harmful queries, role manipulation, data extraction, logic bypass, social engineering, and obfuscation).
* **Prompt Mutation Engine:** Automatically applies structural transforms to prompts, such as leet-speak encoding, base64 encoding, and alternate philosophical framing to evade basic filters.
* **Attack Runner:** An asynchronous concurrent test runner (using `asyncio` and thread executors) equipped with progress indicators and severity filtering.

## 2. API & Providers (`api/`)
Robust handling of interactions with external Large Language Models (LLMs).
* **Provider Abstractions:** Setup with factory functions wrapping both explicitly implemented OpenAI and generalized endpoints.
* **Mock LLM Client:** Added mock responses for offline testing, local debugging, and CI/CD runs.
* **Rate Limiting:** Added a token-bucket based async rate limiter to manage API concurrency and prevent rate-limit errors.
* **Error Handling:** Client wrappers include retry mechanisms, automated metric logging, and configurable system prompts.

## 3. Evaluation & Metrics (`evaluation/`)
Sophisticated scoring mechanisms evaluate whether the model resisted the attack or complied.
* **Safety Scorer:** Identifies unsafe content using domain-grouped safety signals and refusal pattern detection. Returns a strict (0-1) score.
* **Alignment Scorer:** Evaluates responses based on helpfulness heuristics (length and structure) and trustworthiness metrics (hedging vs. overclaiming). Generates a weighted composite safety score.
* **Aggregate Metrics:** Breakdowns of prompt outcomes separated per attack-type category.

## 4. Defenses & Guardrails (`defense/`)
Mechanisms simulating system-level safeguards evaluated during attacks.
* **Filter Guardrails:** Both Pre- and Post-filter mechanisms configured with observe and block modes. Includes unicode normalization and expansive danger pattern matching.

## 5. Experiment Tracking & Persistence (`experiments/` and `storage/`)
Results are meticulously tracked and analyzable via multiple storage mechanisms.
* **Persistence Layer:** Supports JSON file persistence, alongside a fully implemented SQLite storage layer for experiment runs and result queries.
* **Result Analysis:** Provides helpers like `list_runs`, `print_run_history`, and tools to extract the worst-performing results (`get_worst_results`) for triage.
* **Rich Reporting:** Includes a rich terminal reporter with sum-total tables, category breakdowns, and rotating log handlers.

## 6. Utilities (`utils/`)
Support modules to safely handle inputs and outputs.
* **Deduplication:** SHA256 caching and seen-set filtering to prevent redundant prompt testing.
* **Validation:** Robust input validation helpers targeting text prompts, numeric scores, and batch sizes.
* **Text manipulation:** Standardizes LLM responses via token estimation, markdown stripping, normalizers, and truncation tools. 
* **Terminal Utilities:** Added console formatters utilizing ANSI color coding for clearer debugging.

## 7. API Backend (`api_server/`)
Transformed the framework into an enterprise-like REST API using **FastAPI**.
* **REST Endpoints:** Asynchronous endpoints mapping to scoring, evaluation, and defense engines.
* **CORS Support:** Integrated middleware to allow seamless communication with detached frontends.

## 8. Web Frontend (`frontend/`)
A completely custom, state-of-the-art Single Page Application built to visualize pipeline results.
* **React & Vite:** Bootstrapped for maximum performance and hot-reload during development.
* **Aesthetic Dashboard:** Built with a premium, glassmorphic dark-mode design system. 
* **Data Visualization:** Integrated with `Chart.js` for dynamic rendering of composite safety metrics, real-time feedback, and granular verdict reports.

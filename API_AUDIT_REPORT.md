# Sentinel AI - DevOps API Audit Report

## 1. API USAGE SUMMARY
* **OpenAI API**: The primary LLM provider used for AI guardrail evaluations, red-team prompt generations, and system tests.
* **Anthropic API**: The source code has experimental support built-in for Anthropic (Claude), though no library is installed and it is not set as the default provider.

## 2. WHERE APIs ARE USED
* **`api/llm_client.py` → `_get_client()` & `send_prompt()`**
  Establishes the synchronous OpenAI Client and pushes payloads (messages) over the network. It handles parsing token counts and logging generation metrics.
* **`api/providers.py` → `OpenAIProvider.complete()` & `AnthropicProvider.complete()`**
  Handles abstract asynchronous interactions for whichever LLM Provider is set in the config.
* **`config.py` → `validate()`**
  Runs system startup checks to ensure the API key environment variables are loaded.

## 3. REQUIRED API KEYS
* `OPENAI_API_KEY` (Critical / Always Required)
* `ANTHROPIC_API_KEY` (Optional / Required only if `provider: anthropic` is configured)
* `VITE_API_BASE_URL` (Required for Frontend Docker/builds to route to backend)

## 4. CURRENT STATUS
* **Status**: **NOT CONFIGURED**
* The `.env` file exists but only contains dummy placeholder values (`OPENAI_API_KEY=sk-...`) and (`ANTHROPIC_API_KEY=sk-ant-...`).
* `config.py` natively maps these variables, so the placeholders will be injected into network requests and fail.

## 5. FAILURE RISKS
* **Service Crash on Boot**: If `config.py` invokes its `validate()` method prior to an evaluation, it will raise `EnvironmentError` due to missing keys, breaking the backend entirely.
* **401 Unauthorized API Failure**: Because the placeholder `sk-...` is currently active in the `.env` file, the OpenAI API will reject requests. `api/llm_client.py` will catch the 401 error and return `None`.
* **Frontend Error Cascades**: A missing key or `None` response breaks the JSON serialization pipeline in the backend. When the React app at `frontend/src/App.jsx` evaluates a prompt without a valid response from the backend, the end user will see: `Failed to connect to Sentinel API`.

## 6. MOCK OR FALLBACK MODE
* **Current state**: The project currently has **no mock mode**. Handlers do gracefully capture `429 Rate Limits` (with wait-and-retry logic) and `401 Unauthorized` requests, but a failure simply cascades downwards. 
* **Suggested Implementation**: 
  * Add a `SENTINEL_MOCK_MODE=True` environment variable.
  * In `api/providers.py`, register a `MockProvider` class that simulates the latency (`await asyncio.sleep(0.5)`) and returns deterministic JSON payload strings.
  * Adjust `config.py` to bypass `OPENAI_API_KEY` checks when `SENTINEL_MOCK_MODE` is enabled, allowing CI/CD checks and frontend debugging without incurring API costs.

## 7. DEPLOYMENT REQUIREMENTS
* **Docker / Render Backend**:
  * `OPENAI_API_KEY` must be securely provided via Docker secrets, `.env` file mounts, or UI secret managers (e.g. Render Dashboard).
  * `SENTINEL_REQUESTS_PER_MINUTE=60` and `SENTINEL_MAX_CONCURRENT=10` control backend rate-limiting to prevent exceeding Tier 1 API limits during production bursts.
* **Docker / Render Frontend**:
  * `VITE_API_BASE_URL` must be passed dynamically via `--build-arg` at build-time so React maps `import.meta.env.VITE_API_BASE_URL` strictly to the production backend route (e.g., `https://sentinel-api.yourdomain.com/api`).

## 8. FINAL VERDICT
* **Is project ready without API key?**: **No.**
* **What is required to make it fully functional?**:
  1. Add a valid OpenAI API key into the local `.env` file replacing `sk-...`.
  2. Implement the `MockProvider` or mock endpoints via FastAPI to enable offline operations.
  3. *(Optional)* Add `anthropic` to `requirements.txt` if intending to use Claude for evaluations.

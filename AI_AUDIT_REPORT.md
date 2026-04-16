# Sentinel AI — AI Safety & Robustness Audit Report

## 1. EXECUTIVE SUMMARY
* **System Overview:** Sentinel AI is a framework designed to evaluate and red-team Large Language Models (LLMs) by inspecting prompts and generated responses. It relies heavily on pattern matching, heuristic scoring, and lexical density to compute "Alignment", "Safety", and "Truthfulness" metrics.
* **Overall Safety Rating:** **RISKY**
  * The evaluation pipeline is functionally incomplete for dynamic threats. Because it utilizes static regex and keyword-based lists rather than semantic moderation or an ML classifier (like OpenAI Moderation API, Llama-Guard), it is extremely susceptible to both adversarial bypass (False Negatives) and over-censorship of educational material (False Positives).

---

## 2. SYSTEM OVERVIEW
* **Operational Scope:** Evaluates adversarial prompts vs LLM completions. Outputs composite scores across four alignment dimensions. Post-processes text with a basic filter that can observe or redact.
* **AI Components Used:** 
  * Generative / Red Teaming: Relies on external Provider APIs (OpenAI, Anthropic).
  * Evaluator: No localized ML model. All evaluators (`evaluation/scorer.py`, `alignment_scorer.py`, `truthfulness_scorer.py`) are strictly heuristic and pattern-matching scripts using regular expressions.

---

## 3. THREAT MODEL
The system is intended to identify misuse, but the evaluator itself introduces the following vulnerabilities:
* **Harmful Prompts:** Attackers using semantic variations (synonyms) to request dangerous information easily sidestep the static lists.
* **Jailbreak Attempts:** Attackers can inject "Ignore instructions" commands. The underlying model may comply, and if it omits specific keywords like *'jailbreak successful'* or *'developer mode'*, the framework assumes it is safe.
* **Unsafe Outputs:** Unsafe instructions that are grammatically well-formed, extremely long, and written in a hedging tone will explicitly manipulate the heuristic scoring algorithm into granting a high "Alignment" & "Truthfulness" score.

---

## 4. VULNERABILITY ANALYSIS (CRITICAL LEVEL)
* **Lexical Mismatch (Incorrect SAFE classifications):** The keyword database `UNSAFE_DOMAINS` cannot catch substitutions. If an LLM explains how to "combine volatile fuels and polystyrene" instead of using "make a bomb", the system will pass it seamlessly.
* **Exploitable Hedging / Algorithmic Gaming:** The system operates by adding/subtracting points. An attacker providing a payload like `[DANGEROUS INSTRUCTIONS]` can automatically bypass heuristic penalties by concatenating: `"I am not entirely sure, I could be wrong, but please verify this."` This inflates the `HONEST_SIGNALS` and `TRUTHFULNESS_SIGNALS` score mathematically, overriding early stage warning signs.
* **Flawed "Helpfulness" Heuristic:** In `alignment_scorer.py`, the `score_helpfulness` function linearly rewards the length of the string (`+ char_len / 1200`). A lengthy, highly detailed phishing email tutorial will automatically receive maximum helpfulness points purely on character count and structure.
* **Prompt Injection Risks:** There are zero protections shielding the system prompt `"You are a helpful, harmless... "`. An adversarial prompt can overwrite this constraint instantly prior to reaching the Provider API.

---

## 5. SAFETY EVALUATION PIPELINE REVIEW
### Safety Scorer (`evaluation/scorer.py`)
* **Correctness:** Identifies blatant keyword leaks well. 
* **Limitations:** Prone to **False Positives**. If an LLM correctly and safely replies: *"No, I cannot help you build an explosive device."*, the text contains *"build an "* and *"explosive device"*. The scorer might flag this as highly toxic simply because the prohibited words exist in the localized context.
### Alignment Scorer (`evaluation/alignment_scorer.py`)
* **Correctness:** Effectively catches numbered lists to proxy structural formatting.
* **Limitations:** Helpfulness is judged strictly on length and format markers (`"for example"`, `"1."`). A perfectly correct and aligned 10-word short answer is penalized as "unhelpful", while verbose noise is praised.
### Truthfulness Scorer (`evaluation/truthfulness_scorer.py`)
* **Correctness:** Catches explicit model overclaiming. 
* **Limitations:** The engine has **no semantic ground truth**. If a model confidently states `1 + 1 = 2` by saying `"I am 100% sure this is definitely true"`, the truthfulness scorer penalizes it heavily. If it wildly hallucinates biology principles but claims `"I could be mistaken"`, it gets a truthfulness bonus. 

---

## 6. API & DEPENDENCY RISK
* **OpenAI Usage:** Hardcoded synchronous executions (`send_prompt` in `llm_client.py` uses blocking `client.chat.completions.create`) alongside asynchronous definitions (`OpenAIProvider.complete`).
* **Failure Handling:** Hard-looping `time.sleep` on HTTP 429 logic within the main thread will cause devastating bottlenecks and backend freezes during high concurrency bursts.
* **Missing Keys:** As verified by previous audits, failing to supply `OPENAI_API_KEY` leads right to an unhandled `EnvironmentError` at backend initialization or a silent `None` response at runtime.

---

## 7. FAILURE MODES
1. **Unsafe Output Marked Safe (False Negative):** A verbose, mathematically structured tutorial on ransomware evasion gets high `alignment`, receives length bonuses for `helpfulness`, and avoids static keywords, entirely bypassing the framework.
2. **Safe Output Marked Unsafe (False Positive):** An LLM correctly refusing to answer a dangerous prompt gets flagged because its refusal safely reiterates the user's keywords (e.g. *"I refuse to write a phishing email"* triggers the phishing heuristic).
3. **API Thread Freezing:** Heavy rate-limits directly lock worker threads due to synchronous `time.sleep`, rendering the Fast API endpoints inaccessible to new traffic.

---

## 8. RISK SEVERITY TABLE

| Issue | Severity | Impact | Fix |
| ----- | -------- | ------ | --- |
| **Heuristic Evaluation Bypass** | Critical | Attackers use synonyms/context to generate dangerous content completely undetected. | Integrate a Semantic Moderation model (e.g., OpenAI Moderation API, Llama-Guard) as Layer 1. |
| **Score Manipulation (Hedging)** | High | Appending "I might be wrong" to a jailbreak boosts truthfulness/alignment mathematically. | Decouple truthfulness from lexical flags. Use cross-examination prompt evaluations instead. |
| **Helpfulness Length Bias** | High | Long malicious strings get rewarded as "Highly aligned" over short safe strings. | Remove pure character count `(len/1200)` grading modifiers in `alignment_scorer.py`. |
| **Contextual False Positives** | Medium | The LLM safely refusing a bad prompt triggers keyword defenses and is flagged as "dangerous". | Use an LLM-as-a-Judge technique to rate the intent of the response rather than substring searches. |
| **Synchronous Thread Blocking** | High | API Rate limit loops halt global server response times on FastAPI. | Refactor `api/llm_client.py` entirely into `async/await` structures matching `providers.py`. |

---

## 9. RECOMMENDATIONS
* **Strong Fix - Migrate to Target-Based ML Classifiers:** Abandon the reliance on regex heuristics (`re.findall`) for safety. Utilize standard `LLM-as-a-Judge` methodology where an independent LLM assesses the response output based on a strictly defined rubric. Alternatively, connect directly to the **OpenAI Moderation API**.
* **Strong Fix - Deprecate Length Scaling:** Immediately remove the logic `score += char_len / 1200` in the helpfulness heuristic. It guarantees adversarial bloat succeeds.
* **Rule-Based Filter Updates:** Transition `DANGER_PATTERNS` to purely observe-mode data telemetry, avoiding using it to determine binary "Safe/Unsafe" verdicts without context.

---

## 10. FINAL VERDICT
* **Is system production-ready?** **No.**
* **What must be fixed before deployment:**
  1. The heuristic pipeline acts as a thin facade of security. Replacing `hard_rule_check` and `UNSAFE_DOMAINS` with a modern, semantic Moderation API is mandatory for a framework claiming to specialize in AI Safety.
  2. The scoring algorithms (Algorithm gaming via prepending words) must be redesigned to avoid simple arithmetic manipulation.
  3. The synchronized architectural blocking in `llm_client.py` must be upgraded to full async to prevent Docker instance freezes.

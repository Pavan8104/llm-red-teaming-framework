import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.scorer import score_response
from evaluation.alignment_scorer import calculate_alignment
from evaluation.truthfulness_scorer import fetch_truthfulness_report
from defense.basic_filter import filter_response
from attacks.prompt_attacks import ATTACK_PROMPTS
from attacks.prompt_generator import generate_batch
from attacks.gladiator import run_gladiator_battle

# Core API instantiation
# FastAPI ka main server hook yahan create hota hai
app = FastAPI(title="Sentinel AI Protocol API")

# Frontend integration ke liye strictly CORS ko open rakha gaya hai
# CORS routing allowed strictly for React UI Dashboard networking
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class EvaluateRequest(BaseModel):
    """
    Strict typing check request body schema ke liye. 
    Maintains strong type checking JSON constraints.
    """
    prompt: str
    response: str


@app.get("/api/health")
async def health_check():
    """
    Route for Kubernetes checks / external monitoring.
    """
    return {"status": "ok", "system": "Sentinel Async API is active!"}


@app.post("/api/evaluate")
async def evaluate_interaction(req: EvaluateRequest):
    """
    ASYNC Execution Engine! Puri process bina API freeze kiye await karti hai.
    ASYNC processing core! Handshakes Moderation API and grading logic strictly without blocking threads.
    """
    try:
        # Prompt injection module ko filter checking bhejte hain pehle
        # Pre-check the Prompt Injection grids actively early to block heavy tasks if malicious!
        prompt_defense_check = filter_response(req.prompt, block_mode=False)
        if prompt_defense_check["severity"] >= 4:
            raise HTTPException(
                status_code=400, 
                detail="Prompt Injection attempt blocked securely."
            )

        # ── Asynchronously fire off Prompt and Response Evaluation Scoring ──
        prompt_safety_eval = await score_response(req.prompt, source="prompt")
        response_safety_eval = await score_response(req.response, source="response")

        # ── Worst-case scenario logic — Result = UNSAFE if ANY element fails ──
        final_is_unsafe = prompt_safety_eval["is_unsafe"] or response_safety_eval["is_unsafe"]
        final_safety_metric = min(prompt_safety_eval["safety_score"], response_safety_eval["safety_score"])

        # Decide primary reporting dictionary for UI display metrics
        # Decide which specific analysis matrix should dictate the frontend error display
        if prompt_safety_eval["is_unsafe"] and not response_safety_eval["is_unsafe"]:
            active_safety_dict = prompt_safety_eval
        else:
            active_safety_dict = response_safety_eval

        combined_safety_payload = {
            **active_safety_dict,
            "is_unsafe":    final_is_unsafe,
            "safety_score": final_safety_metric,
            "prompt_safety":   prompt_safety_eval,
            "response_safety": response_safety_eval,
        }

        # Baaki dimensions synchronously evaluate hote hain kyunki yeh sirf regex array maps hain!
        # Remaining charts execute instantly because they lack network overheads
        alignment_report = calculate_alignment(req.response, provided_safety=final_safety_metric)
        truth_report = fetch_truthfulness_report(req.response)
        defense_report = filter_response(req.response, block_mode=False)

        return {
            "prompt":      req.prompt,
            "response":    req.response,
            "safety":      combined_safety_payload,
            "alignment":   alignment_report,
            "truthfulness": truth_report,
            "defense":     defense_report,
            "is_unsafe":   final_is_unsafe,
            "safety_score": final_safety_metric,
        }

    except HTTPException as http_exception:
        # Expected business logic blocks throw neatly
        # Throw predefined secure codes up gracefully
        raise http_exception
    except Exception as runtime_error:
        # Fallback system crash log
        # Global crash reporting mapping
        print(f"[API Freeze] Endpoint evaluate failed: {str(runtime_error)}")
        raise HTTPException(status_code=500, detail=str(runtime_error))


@app.get("/api/prompts/library")
async def get_prompt_library():
    """
    Frontend gallery ko prompts bhejne ke liye list data supply karta hai.
    """
    return {"prompts": ATTACK_PROMPTS}


@app.get("/api/prompts/generate")
async def generate_prompts(n: int = 5, attack_type: Optional[str] = None):
    """
    Synchronous generation call to the mutator files internally.
    """
    try:
        crafted_prompts = generate_batch(n=n, attack_type=attack_type)
        return {"prompts": crafted_prompts}
    except Exception as processing_error:
        raise HTTPException(status_code=500, detail=str(processing_error))

@app.get("/api/gladiator/battle")
async def start_gladiator_battle(objective: str, target_model: str = "gpt-4o-mini", max_turns: int = 5):
    """
    Starts an AI vs AI gladiator battle and streams the events via Server-Sent Events (SSE).
    """
    async def event_generator():
        try:
            async for event in run_gladiator_battle(objective, target_model=target_model, max_turns=max_turns):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            error_event = {"status": "error", "message": str(e)}
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# api_server/fast_server.py — FastAPI backend for the React frontend
# safety pipeline ko REST endpoints ke through expose karta hai
# React app is se /api/evaluate pe POST request karta hai

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

import sys
import os

# project root add karo taaki sibling modules import ho sakein
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.scorer import score_response
from evaluation.alignment_scorer import score_alignment
from evaluation.truthfulness_scorer import explain_truthfulness
from defense.basic_filter import filter_response
from attacks.prompt_attacks import ATTACK_PROMPTS
from attacks.prompt_generator import generate_batch

app = FastAPI(title="Sentinel AI Engine API")

# CORS khol do — React dev server alag port pe hota hai
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class EvaluateRequest(BaseModel):
    prompt:   str
    response: str


@app.get("/api/health")
def health_check():
    # simple liveness check — load balancer ya frontend se use karo
    return {"status": "ok"}


@app.post("/api/evaluate")
def evaluate_interaction(req: EvaluateRequest):
    # prompt aur response dono score karo independently
    # worst-case wins: dono mein se koi bhi unsafe ho to final verdict UNSAFE hoga
    try:
        prompt_safety   = score_response(req.prompt,   source="prompt")
        response_safety = score_response(req.response, source="response")

        is_unsafe    = prompt_safety["is_unsafe"] or response_safety["is_unsafe"]
        safety_score = min(prompt_safety["safety_score"], response_safety["safety_score"])

        # combined safety result banao frontend ke liye
        # agar prompt ne override kiya aur response safe tha to prompt ka reason dikhao
        if prompt_safety["is_unsafe"] and not response_safety["is_unsafe"]:
            primary_safety = prompt_safety
        else:
            primary_safety = response_safety

        safety_result = {
            **primary_safety,
            # combined worst-case values hamesha reflect karo
            "is_unsafe":       is_unsafe,
            "safety_score":    safety_score,
            # transparency ke liye dono individual verdicts include karo
            "prompt_safety":   prompt_safety,
            "response_safety": response_safety,
        }

        alignment_result = score_alignment(req.response, safety_score=safety_score)
        truth_result     = explain_truthfulness(req.response)
        defense_result   = filter_response(req.response, block_mode=False)

        return {
            "prompt":       req.prompt,
            "response":     req.response,
            "safety":       safety_result,
            "alignment":    alignment_result,
            "truthfulness": truth_result,
            "defense":      defense_result,
            "is_unsafe":    is_unsafe,
            "safety_score": safety_score,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/prompts/library")
def get_prompt_library():
    # poori attack library return karo — frontend mein browse ke liye
    return {"prompts": ATTACK_PROMPTS}


@app.get("/api/prompts/generate")
def generate_prompts(n: int = 5, attack_type: Optional[str] = None):
    # dynamic prompts generate karo — frontend generator tab ke liye
    try:
        prompts = generate_batch(n=n, attack_type=attack_type)
        return {"prompts": prompts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

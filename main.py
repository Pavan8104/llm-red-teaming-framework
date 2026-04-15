#!/usr/bin/env python3
# main.py — quick red-teaming runner
# runs a few attack prompts and prints responses
# this is the v1 prototype, not production code

import os
from attacks.prompt_attacks import get_prompts
from api.llm_client import send_prompt

SEPARATOR = "-" * 60


def run():
    print("=== Sentinel AI — LLM Red Teaming ===\n")

    if not os.getenv("OPENAI_API_KEY"):
        print("[ERROR] OPENAI_API_KEY not set. Export it and try again.")
        return

    # just run the first 3 for now — don't burn too much quota
    prompts = get_prompts(limit=3)

    for attack in prompts:
        print(SEPARATOR)
        print(f"[Attack] ID: {attack['id']} | Type: {attack['type']}")
        print(f"[Prompt] {attack['prompt'][:120]}...")

        response = send_prompt(attack["prompt"])

        if response:
            print(f"[Response]\n{response}\n")
        else:
            print("[Response] Failed — no response received.\n")

    print(SEPARATOR)
    print("\nDone. Check responses above for safety issues.")


if __name__ == "__main__":
    run()

# simple wrapper around openai api
# nothing fancy here, just get a response and return it

import os
import time
from openai import OpenAI

# grab key from env — don't hardcode this obviously
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def send_prompt(prompt_text, model="gpt-4o-mini", temperature=0.7):
    """
    send a single prompt and return the response text
    includes basic retry for rate limits
    """
    print(f"\n[LLM] Sending prompt ({len(prompt_text)} chars)...")

    for attempt in range(3):
        try:
            start = time.time()

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful, harmless, and honest AI assistant."},
                    {"role": "user", "content": prompt_text}
                ],
                temperature=temperature,
                max_tokens=512,
            )

            elapsed = round(time.time() - start, 2)
            text = response.choices[0].message.content
            print(f"[LLM] Got response in {elapsed}s — {len(text)} chars")
            return text

        except Exception as e:
            print(f"[LLM] Error on attempt {attempt + 1}: {e}")
            if attempt < 2:
                time.sleep(2 ** attempt)  # 1s, 2s backoff
            else:
                return None

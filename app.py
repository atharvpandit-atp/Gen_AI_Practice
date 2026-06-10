import os
import time
import json
from openai import OpenAI, BadRequestError
from pydantic import BaseModel, Field

#1. Initialize client using GitHub's free endpoint
token = os.environ.get("GITHUB_TOKEN")
if not token:
    print("ERROR: Environment variable 'GITHUB_TOKEN' not found.")
    print("Please run: $env:GITHUB_TOKEN='your_actual_token' in PowerShell first.")
    exit(1)

client = OpenAI(
    base_url="https://models.inference.ai.azure.com"
    api_key=token
)
# Target model on GitHub
MODEL_NAME = "gpt-4o-mini"

def print_banner(title):
    print("\n" + "="*60)
    print(f" HANDS-ON TASK: {title}")
    print("="*60)

#TASK A : First Call
def task_a_first_call():
    print_banner("A - First call via GitHub Free Tier")

    response = client.chat.completion.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are a concise, factual assistant."},
            {"role": "user", "content": "What is the capital of Japan?"}
        ],
        temprature=0.0
    )

    text = response.choices[0].message.content
    usage = response.usage
    finish_reason = response.choices[0].finish_reason
    
    print(f"AI Response: {text}")
    print(f"Finish Reason: {finish_reason}")
    print(f"Token Metadata -> Input: {usage.prompt_tokens} | Output: {usage.completion_tokens}")

#TASK B: System-Prompt Swap
def task_b_prompt_swap():
    print_banner("B - System-Prompt Control")

    prompts = {
        "Pirate Persona": "You are a seafaring 17th-century pirate captain.",
        "JSON Enforcer": "You are an API. Reply exclusively in JSON format like: {\"answer\": \"your text here\"}"
    }

    user_query = "What is the color of the sky on a clear afternoon?"

    for name, system_content in prompts.items():
        res = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_query}
            ],
            temperature=0.3
        )
        print(f"\n[{name} Out]: {res.choices[0].message.content.strip()}")

#TASK C & D: Multi-Turn Memory Loop(Snowball Tracking)
def task_c_d_memory_loop(simulate_break=False):
    banner = "C & D - Broken Memory Simulation" if simulate_break else "C & D - Multi-Turn Memory Loop"
    print_banner(banner)

    messages = [{"role": "system", "content": "You are a helpful tracking assistant"}]
    conversation_turns = [
        "What is the capital ofFrance?",
        "What is the estimated population of that city?"
    ]

    for i, user_text in enumerate(conversation_turns, 1):
        print(f"\n--- Turn {i}: User says -> '{user_text}' ---")
        messages.append({"role": "user", "content": user_text})
        
        res = client.chat.completions.create(model=MODEL_NAME, messages=messages)
        reply = res.choices[0].message.content
        usage = res.usage
        
        print(f"AI Response: {reply}")
        print(f"[Snowball Monitor] Total Input Tokens Passed: {usage.prompt_tokens}")
        
        if simulate_break:
            print("⚠️ [Simulation] Intentionally skipped appending assistant reply to local list context...")
            continue
        else:
            messages.append({"role": "assistant", "content": reply})

    

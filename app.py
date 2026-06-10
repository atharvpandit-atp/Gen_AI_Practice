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



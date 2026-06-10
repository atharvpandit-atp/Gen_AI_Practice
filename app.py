import os
import time
import json
from openai import OpenAI, BadRequestError
from pydantic import BaseModel, Field

# 1. Initialize client using GitHub's free endpoint infrastructure
token = os.environ.get("GITHUB_TOKEN")
if not token:
    print("ERROR: Environment variable 'GITHUB_TOKEN' not found.")
    print("Please run: $env:GITHUB_TOKEN='your_token_here' in PowerShell first.")
    exit(1)

client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=token
)

# Target model on GitHub's free playground infrastructure
MODEL_NAME = "gpt-4o-mini"

def print_banner(title):
    print("\n" + "="*60)
    print(f" HANDS-ON TASK: {title}")
    print("="*60)

# =====================================================================
# TASK A: First Call & Metadata Verification
# =====================================================================
def task_a_first_call():
    print_banner("A - First Call via GitHub Free Tier")
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are a concise, factual assistant."},
            {"role": "user", "content": "What is the capital of Japan?"}
        ],
        temperature=0.0
    )
    
    text = response.choices[0].message.content
    usage = response.usage
    finish_reason = response.choices[0].finish_reason
    
    print(f"AI Response: {text}")
    print(f"Finish Reason: {finish_reason}")
    print(f"Token Metadata -> Input: {usage.prompt_tokens} | Output: {usage.completion_tokens}")

# =====================================================================
# TASK B: System-Prompt Swap
# =====================================================================
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

# =====================================================================
# TASK C & D: Multi-Turn Memory Loop & Snowball Tracking
# =====================================================================
def task_c_d_memory_loop(simulate_break=False):
    banner = "C & D - Broken Memory Simulation" if simulate_break else "C & D - Multi-Turn Memory Loop"
    print_banner(banner)
    
    messages = [{"role": "system", "content": "You are a helpful tracking assistant."}]
    conversation_turns = [
        "What is the capital of France?",
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

# =====================================================================
# TASK E: Streaming
# =====================================================================
def task_e_streaming():
    print_banner("E - Streaming Token Chunks (Low Latency UI)")
    
    print("Streaming Tokens: ", end="", flush=True)
    
    stream = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": "Explain tokenization in exactly two sentences."}],
        stream=True
    )
    
    for chunk in stream:
        # 🛡️ FIX: Check if choices list is empty before reading index 0
        if not chunk.choices:
            continue
            
        token = chunk.choices[0].delta.content
        if token:
            print(token, end="", flush=True)
            
    print("\n\nStream Finished.")

# =====================================================================
# TASK F: Structured Output
# =====================================================================
class SupportTicketSchema(BaseModel):
    category: str = Field(description="Must be billing, tech_support, or feedback.")
    urgency: str = Field(description="low, medium, or high.")
    summary: str = Field(description="A 1-sentence summary of the user issue.")

def task_f_structured_output():
    print_banner("F - Structured Output (JSON Mode Parsing)")
    
    awkward_message = "My payment failed three times even though my card is good. Fix this now, your dashboard looks clean though."
    
    # Note: On GitHub free tier, structured output works smoothly by 
    # enforcing schema structure natively via system requirements.
    system_instruction = f"Analyze the text. You must output raw valid JSON matching this schema description parameters: {SupportTicketSchema.model_json_schema()}"
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": awkward_message}
        ],
        response_format={"type": "json_object"},
        temperature=0.0
    )
    
    raw_json = response.choices[0].message.content
    print(f"Raw Clean JSON back from Free Endpoint:\n{raw_json}")

# =====================================================================
# TASK G: Tool Calling (Function Interception Loop)
# =====================================================================
def get_weather(location: str):
    return json.dumps({"location": location, "temperature": "14°C", "condition": "Rainy"})

def get_local_time(location: str):
    return json.dumps({"location": location, "time": "4:30 PM"})

def task_g_tool_calling():
    print_banner("G - Tool Calling Mechanics")
    
    tools_blueprint = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather details.",
                "parameters": {
                    "type": "object",
                    "properties": {"location": {"type": "string"}},
                    "required": ["location"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_local_time",
                "description": "Get current time details.",
                "parameters": {
                    "type": "object",
                    "properties": {"location": {"type": "string"}},
                    "required": ["location"]
                }
            }
        }
    ]
    
    messages = [{"role": "user", "content": "What is the weather and current time in London?"}]
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        tools=tools_blueprint
    )
    
    assistant_msg = response.choices[0].message
    
    if assistant_msg.tool_calls:
        print(f"AI requested execution for {len(assistant_msg.tool_calls)} tools.")
        messages.append(assistant_msg)
        
        for tool_call in assistant_msg.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            
            if name == "get_weather":
                result = get_weather(args.get("location"))
            elif name == "get_local_time":
                result = get_local_time(args.get("location"))
                
            print(f" -> Local Intercept Engine Executed '{name}' -> Output: {result}")
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": name,
                "content": result
            })
            
        final_res = client.chat.completions.create(model=MODEL_NAME, messages=messages)
        print(f"\nFinal Consolidated Response:\n{final_res.choices[0].message.content}")

# =====================================================================
# TASK H: Break It On Purpose
# =====================================================================
def task_h_failures():
    print_banner("H - Intentional Failure Interception")
    print("Triggering bad parameter to force a response failure...")
    try:
        client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=-20 # Invalid entry
        )
    except BadRequestError as e:
        print(f"❌ Handled Expected 400 Bad Request successfully: {e.message}")
        print("🛡️ Application remains stable.")

# Run Pipeline Execution
if __name__ == "__main__":
    task_a_first_call()
    task_b_prompt_swap()
    task_c_d_memory_loop(simulate_break=False)
    task_c_d_memory_loop(simulate_break=True) # Watch turn 2 fail to know context
    task_e_streaming()
    task_f_structured_output()
    task_g_tool_calling()
    task_h_failures()
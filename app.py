import os
import json
import streamlit as st
from openai import OpenAI, BadRequestError
from pydantic import BaseModel, Field

# Page configuration
st.set_page_config(page_title="LLM Mechanics Playground", layout="wide", page_icon="🤖")

st.title("🤖 LLM Mechanics & API Playground")
st.caption("An interactive platform to explore System Prompts, Memory, Streaming, JSON Modes, and Function Calling.")

# 1. Initialize API Client
token = os.environ.get("GITHUB_TOKEN") or st.sidebar.text_input("Enter GITHUB_TOKEN:", type="password")

if not token:
    st.warning("⚠️ GITHUB_TOKEN not found. Please provide it via Environment Variables or enter it in the sidebar to begin.")
    st.stop()

client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=token
)
MODEL_NAME = "gpt-4o-mini"

# ==========================================
# TAB CREATION
# ==========================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🎯 Basic Inference (A)", 
    "🎭 System Prompt Control (B)", 
    "🧠 Chat Memory Sandbox (C & D)", 
    "⚡ Streaming (E)", 
    "📄 Structured Output (F)", 
    "🛠️ Tool Calling (G & H)"
])

# ==========================================
# TAB 1: BASIC INFERENCE
# ==========================================
with tab1:
    st.header("Task A: First Call & Metadata Verification")
    user_prompt = st.text_input("Ask something factual:", value="What is the capital of Japan?", key="t1_input")
    
    if st.button("Execute Request", key="t1_btn"):
        with st.spinner("Calling API..."):
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are a concise, factual assistant."},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0
            )
            text = response.choices[0].message.content
            usage = response.usage
            finish_reason = response.choices[0].finish_reason
            
            st.success("Response Received!")
            st.write(f"**AI Response:** {text}")
            
            # Metrics UI
            col1, col2, col3 = st.columns(3)
            col1.metric("Finish Reason", finish_reason)
            col2.metric("Prompt Tokens", usage.prompt_tokens)
            col3.metric("Completion Tokens", usage.completion_tokens)

# ==========================================
# TAB 2: SYSTEM PROMPT CONTROL
# ==========================================
with tab2:
    st.header("Task B: System Prompt Control")
    st.markdown("See how changing the *System Prompt* fundamentally alters model behavior.")
    
    sys_prompt = st.text_area("Define System Prompt Persona:", 
                              value="You are a seafaring 17th-century pirate captain who speaks in heavy pirate slang.")
    t2_query = st.text_input("User Query:", value="What is the color of the sky on a clear afternoon?")
    t2_temp = st.slider("Temperature (Creativity):", min_value=0.0, max_value=1.0, value=0.3, step=0.1)
    
    if st.button("Generate Persona Output"):
        with st.spinner("Generating..."):
            res = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": t2_query}
                ],
                temperature=t2_temp
            )
            st.info(f"**Persona Output:**\n\n {res.choices[0].message.content}")

# ==========================================
# TAB 3: CHAT MEMORY SANDBOX
# ==========================================
with tab3:
    st.header("Task C & D: Multi-Turn Memory vs Broken Memory Loop")
    st.markdown("LLMs are completely **stateless**. This sandbox shows how context collapses if you forget to feed previous loops back into the payload.")
    
    # Toggle to simulate broken state tracking
    simulate_break = st.checkbox("⚠️ Simulate Broken Memory (Skip saving Assistant replies)", value=False)
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [{"role": "system", "content": "You are a helpful tracking assistant."}]

    if st.button("Clear History"):
        st.session_state.chat_history = [{"role": "system", "content": "You are a helpful tracking assistant."}]
        st.rerun()

    # Display Chat
    st.write("---")
    for msg in st.session_state.chat_history:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                
    chat_input = st.text_input("Type message here (e.g., Turn 1: 'What is the capital of France?', Turn 2: 'What is the population of that city?'):")
    
    if st.button("Send Message"):
        if chat_input:
            # Append User Input
            st.session_state.chat_history.append({"role": "user", "content": chat_input})
            
            with st.spinner("Thinking..."):
                res = client.chat.completions.create(
                    model=MODEL_NAME, 
                    messages=st.session_state.chat_history
                )
                reply = res.choices[0].message.content
                st.write(f"**Snowball Monitor — Input Tokens Passed:** {res.usage.prompt_tokens}")
                
                if simulate_break:
                    st.warning("⚠️ [Simulation Active] Assistant reply was NOT saved to history! Next turn will lose context.")
                    # Show immediate response on screeen but do not add to session state history
                    with st.chat_message("assistant"):
                        st.write(reply)
                else:
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
                    st.rerun()

# ==========================================
# TAB 4: STREAMING CHUNKS
# ==========================================
with tab4:
    st.header("Task E: Streaming Token Chunks")
    t4_query = st.text_input("Ask a long question for streaming:", value="Explain tokenization in exactly two paragraphs.")
    
    if st.button("Stream Response"):
        stream = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": t4_query}],
            stream=True
        )
        
        # Stream box placeholder
        st.write("**Streaming Live Feed:**")
        placeholder = st.empty()
        full_response = ""
        
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
                placeholder.markdown(full_response + "▌")
        placeholder.markdown(full_response)

# ==========================================
# TAB 5: STRUCTURED OUTPUT
# ==========================================
with tab5:
    st.header("Task F: Structured Output JSON Parsing")
    
    class SupportTicketSchema(BaseModel):
        category: str = Field(description="Must be billing, tech_support, or feedback.")
        urgency: str = Field(description="low, medium, or high.")
        summary: str = Field(description="A 1-sentence summary of the user issue.")

    raw_text = st.text_area("Raw Messy Customer Message:", 
                            value="My payment failed three times even though my card is good. Fix this now, your dashboard looks clean though.")
    
    if st.button("Extract Schema JSON"):
        system_instruction = f"Analyze the text. You must output raw valid JSON matching this schema description parameters: {SupportTicketSchema.model_json_schema()}"
        
        res = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": raw_text}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        parsed_json = res.choices[0].message.content
        st.json(parsed_json)

# ==========================================
# TAB 6: TOOL CALLING & FAILURE INTERCEPTION
# ==========================================
with tab6:
    st.header("Task G & H: Function Calling Sandbox & Failure Handling")
    
    # Mock Native System Tools
    def get_weather(location: str):
        return json.dumps({"location": location, "temperature": "14°C", "condition": "Rainy"})

    def get_local_time(location: str):
        return json.dumps({"location": location, "time": "4:30 PM"})

    t6_query = st.text_input("Trigger tools query:", value="What is the weather and current time in London?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Execute Function Tool Call Loop"):
            tools_blueprint = [
                {"type": "function", "function": {"name": "get_weather", "description": "Get weather.", "parameters": {"type": "object", "properties": {"location": {"type": "string"}}, "required": ["location"]}}},
                {"type": "function", "function": {"name": "get_local_time", "description": "Get time.", "parameters": {"type": "object", "properties": {"location": {"type": "string"}}, "required": ["location"]}}}
            ]
            
            messages = [{"role": "user", "content": t6_query}]
            res = client.chat.completions.create(model=MODEL_NAME, messages=messages, tools=tools_blueprint)
            assistant_msg = res.choices[0].message
            
            if assistant_msg.tool_calls:
                st.info(f"🎯 Model intercepted! Requested execution for {len(assistant_msg.tool_calls)} local tools.")
                messages.append(assistant_msg)
                
                for tool_call in assistant_msg.tool_calls:
                    name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    
                    if name == "get_weather":
                        result = get_weather(args.get("location"))
                    elif name == "get_local_time":
                        result = get_local_time(args.get("location"))
                        
                    st.write(f"⚙️ Running backend python func `{name}` with arguments `{args}` -> Result: {result}")
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": name,
                        "content": result
                    })
                
                final_res = client.chat.completions.create(model=MODEL_NAME, messages=messages)
                st.success(f"**Final Processed Response:**\n\n{final_res.choices[0].message.content}")

    with col2:
        if st.button("💥 Force Error 400 Bad Request", type="primary"):
            st.write("Sending an intentionally invalid `max_tokens=-20` parameter...")
            try:
                client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=-20
                )
            except BadRequestError as e:
                st.error(f"Handled Expected 400 Error gracefully! UI remains responsive.")
                st.code(e.message)
import subprocess
import os
import json
import datetime
import requests
from urllib.parse import quote_plus
from langgraph.graph import StateGraph, END

from typing import TypedDict, List, Optional

# -------------------
# 🧠 Memory (JSON file)
# -------------------
MEMORY_FILE = "assistant_memory.json"

def load_persistent_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print("Memory load error:", e)
    return {}

def save_persistent_memory(mem: dict):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(mem, f, default=str, indent=2)
        return True
    except Exception as e:
        print("Memory save error:", e)
        return False

# -----------------------
# ⚙️ Ubuntu App Whitelist
# -----------------------
ALLOWED_APPS = {
    "gedit": "gedit",
    "firefox": "firefox",
    "calculator": "gnome-calculator",
}

def open_application(step: str):
    tokens = step.lower().split()
    if len(tokens) < 2:
        return f"Invalid open command: '{step}'"

    app_name = tokens[1]
    if app_name in ALLOWED_APPS:
        try:
            subprocess.Popen([ALLOWED_APPS[app_name]])
            return f"Launched application: {app_name}"
        except Exception as e:
            return f"Failed to launch {app_name}: {e}"
    else:
        return f"App '{app_name}' is not allowed."

def play_video(step: str):
    # Extract title after "play"
    title = step.lower().replace("play", "").strip()
    if not title:
        return "No video title specified."

    query = quote_plus(title)
    url = f"https://www.youtube.com/results?search_query={query}"
    try:
        subprocess.Popen(["xdg-open", url])
        return f"Opened YouTube search for: {title}"
    except Exception as e:
        return f"Error opening YouTube: {e}"

# -----------------------------
# 🧠 LangGraph State Definition
# -----------------------------
class AssistantState(TypedDict, total=False):
    input: str
    transcript: str
    type: str  # "instruction" or "query"
    steps: List[str]
    verified_steps: List[str]
    step_outputs: List[str]
    final_output: str
    response: str
    memory: dict
    memory_loaded_at: str

# --------------------------------------
# 🤖 LLM Query to Ollama (classification, step generation)
# --------------------------------------
OLLAMA_MODEL = "openchat:latest"  # or "llama3", "gemma", etc.

def call_ollama(prompt: str, system: str = "") -> str:
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "system": system, "stream": False}
        )
        return response.json()["response"].strip()
    except Exception as e:
        return f"Ollama error: {e}"

# ------------------
# Graph Nodes (Agents)
# ------------------

def load_memory(state: AssistantState):
    state['memory'] = load_persistent_memory()
    return state

def listen_to_query(state: AssistantState) -> AssistantState:
    user_input = input("🗣️ You: ")
    state['input'] = user_input
    return state

def transcribe(state: AssistantState) -> AssistantState:
    state['transcript'] = state.get('input', "Play Comedy Videos on YouTube")
    return state

def classify_query_or_instruction(state: AssistantState) -> AssistantState:
    user_input = state['transcript']
    prompt = f"""Classify the following input as either a 'query' or an 'instruction':

Input: "{user_input}"

Answer with only the word: query or instruction."""

    result = call_ollama(prompt)
    label = result.lower().strip()
    state['type'] = "instruction" if "instruction" in label else "query"
    return state

def split_instructions(state: AssistantState) -> AssistantState:
    instruction = state['transcript']
    prompt = f"""Break the following instruction into atomic steps, separated by new lines:

"{instruction}"

Only return the list of steps."""
    steps_raw = call_ollama(prompt)
    steps = [s.strip("-• ").strip() for s in steps_raw.strip().split("\n") if s.strip()]
    state['steps'] = steps
    return state

def reverify_steps(state: AssistantState) -> AssistantState:
    # Add basic safety / sanity check
    safe_steps = []
    for s in state['steps']:
        if s.startswith(("rm", "sudo", "shutdown", "delete")):
            safe_steps.append("echo '[BLOCKED UNSAFE COMMAND] " + s + "'")
        else:
            safe_steps.append(s)
    state['verified_steps'] = safe_steps
    return state

def iterate_on_steps(state: AssistantState) -> AssistantState:
    outputs = []
    for step in state.get('verified_steps', []):
        step_l = step.lower()
        if step_l.startswith("open "):
            outputs.append(open_application(step))
        elif step_l.startswith("play "):
            outputs.append(play_video(step))
        else:
            prompt = f"""You are a helpful assistant. Simulate or describe how to execute this step: "{step}"."""
            outputs.append(call_ollama(prompt))
    state['step_outputs'] = outputs
    return state

def on_to_next_step(state: AssistantState) -> AssistantState:
    state['final_output'] = "\n".join(state.get('step_outputs', []))
    return state

def generate_answer(state: AssistantState) -> AssistantState:
    query = state.get('transcript')
    answer = call_ollama(f"Answer this question:\n\n{query}")
    state['response'] = answer
    return state

def remove_old_memory(state: AssistantState) -> AssistantState:
    mem = state.get('memory', {})
    now = datetime.datetime.now()
    if 'history' in mem:
        mem['history'] = [
            h for h in mem['history']
            if (now - datetime.datetime.fromisoformat(h['timestamp'])).days <= 30
        ]
    state['memory'] = mem
    return state

def save_memory(state: AssistantState) -> AssistantState:
    mem = state.get('memory', {})
    hist = mem.get('history', [])
    hist.append({
        "timestamp": datetime.datetime.now().isoformat(),
        "input": state.get('transcript'),
        "type": state.get('type'),
        "output": state.get('final_output') or state.get('response')
    })
    mem['history'] = hist
    state['memory'] = mem
    save_persistent_memory(mem)
    return state

def route_query_or_instruction(state):
    return "instruction" if state.get("type") == "instruction" else "query"

# ---------------------
# 🌐 Build LangGraph
# ---------------------
def build_graph():
    g = StateGraph(AssistantState)
    g.add_node("load_memory", load_memory)
    g.add_node("listen", listen_to_query)
    g.add_node("transcribe", transcribe)
    g.add_node("classify", classify_query_or_instruction)
    g.add_node("split", split_instructions)
    g.add_node("reverify", reverify_steps)
    g.add_node("iterate", iterate_on_steps)
    g.add_node("next_step", on_to_next_step)
    g.add_node("query_ans", generate_answer)
    g.add_node("remove_old", remove_old_memory)
    g.add_node("save_mem", save_memory)

    g.set_entry_point("load_memory")
    g.add_edge("load_memory", "listen")
    g.add_edge("listen", "transcribe")
    g.add_edge("transcribe", "classify")

    g.add_conditional_edges("classify", route_query_or_instruction, {
        "instruction": "split",
        "query": "query_ans"
    })

    # Instruction path
    g.add_edge("split", "reverify")
    g.add_edge("reverify", "iterate")
    g.add_edge("iterate", "next_step")
    g.add_edge("next_step", "remove_old")

    # Query path
    g.add_edge("query_ans", "remove_old")

    g.add_edge("remove_old", "save_mem")
    g.add_edge("save_mem", END)

    return g

# -------------------------
# ▶️ Run Assistant Loop
# -------------------------
def run_loop():
    graph = build_graph()
    app = graph.compile()
    while True:
        print("\n==========================")
        print("🤖 Assistant Ready")
        final_state = app.invoke({"input": "Open YouTube for me"})
        out = final_state.get("final_output") or final_state.get("response")
        print(f"\n📤 Assistant → {out}")
        if final_state.get("transcript", "").lower() in ["exit", "quit", "bye"]:
            break

if __name__ == "__main__":
    run_loop()

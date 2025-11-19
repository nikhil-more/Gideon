import subprocess
import shlex
from typing import TypedDict, Annotated, Sequence, Any

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_ollama.chat_models import ChatOllama  # you can swap your LLM
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver


# ——— Define the state used by nodes —————————————————————
class AgentState(MessagesState):
    """State carries message history and maybe step queue, results etc."""
    steps: Annotated[list[str], Any]  # planned steps
    current_step: Annotated[int, Any]
    results: Annotated[dict[int, Any], Any]


# ——— Tool node: decompose instruction into steps —————————
def plan_steps(state: AgentState) -> AgentState:
    messages = state["messages"]
    # prompt the LLM to decompose last user instruction into ordered steps
    instruction = messages[-1].content  # assuming last message is user
    prompt = f"""
You are a decomposition assistant. Given the instruction, break it down into ordered, numbered steps.

Instruction: {instruction}

Steps:
1."""
    # invoke LLM
    response = llm.invoke(messages + [SystemMessage(content=prompt)])
    # parse response into list of step strings
    content = response.content.strip()
    # remove prefix “1.” if present, split by newline and numbering
    lines = content.splitlines()
    steps = []
    for line in lines:
        # simple parsing: drop leading “{num}. ”
        parts = line.strip().split(".", 1)
        if len(parts) == 2 and parts[0].strip().isdigit():
            steps.append(parts[1].strip())
        else:
            # fallback: whole line
            steps.append(line.strip())
    # update state
    new = {
        "messages": state["messages"] + [response],
        "steps": steps,
        "current_step": 0,
        "results": {}
    }
    return new


# ——— Tool node: execute a single step —————————————————————
def execute_step(state: AgentState) -> AgentState:
    messages = state["messages"]
    steps = state["steps"]
    idx = state["current_step"]
    if idx >= len(steps):
        # no more steps
        return state

    step = steps[idx]
    result = None

    # decide what kind of step: open application? ask question? explain?
    # Very naive heuristics; you can expand
    low = step.lower()
    if low.startswith("open ") or low.startswith("launch ") or "start " in low:
        # assume it is launching an application; run via shell
        # e.g. "open calculator", "start browser", etc.
        cmd = step.replace("open ", "").replace("launch ", "")
        try:
            # simple: for Linux / Mac. For Windows adapt accordingly.
            subprocess.Popen(shlex.split(cmd))
            result = f"Executed command to open: {cmd}"
        except Exception as e:
            result = f"Error executing command '{cmd}': {e}"
    else:
        # default: ask the LLM to do this step (explain / answer / compute)
        prompt = f"""
You are an assistant. Execute the following step (or respond) in context.

Step: {step}

Conversation history:
{''.join(m.content for m in messages)}

Answer / result:
"""
        response = llm.invoke(messages + [SystemMessage(content=prompt)])
        result = response.content

    # update state: add result, advance idx
    new_messages = state["messages"] + [AIMessage(content=result)]
    new_results = dict(state["results"])
    new_results[idx] = result
    return {
        "messages": new_messages,
        "steps": steps,
        "current_step": idx + 1,
        "results": new_results
    }


# ——— Node: check if finished ——————————————————————————
def is_done(state: AgentState) -> bool:
    return state["current_step"] >= len(state["steps"])


# ——— Main orchestration ———————————————————————————————
if __name__ == "__main__":
    # initialize LLM / pipeline
    model = ChatOllama(model="openchat:latest")  # replace with your open model
    llm = model

    # build graph
    graph = StateGraph(AgentState)
    # add nodes
    graph.add_node(plan_steps, name="planner")
    graph.add_node(execute_step, name="executor")
    # add edges
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "executor")
    graph.add_edge("executor", "executor")  # loop: executor to itself until done
    graph.add_edge("executor", END)

    # compile with memory / checkpointing
    compiled = graph.compile(checkpointer=MemorySaver())

    # receive user input
    user_input = input("Enter your instruction: ")
    init_state: AgentState = {
        "messages": [HumanMessage(content=user_input)],
        "steps": [],
        "current_step": 0,
        "results": {}
    }

    final = compiled.invoke(init_state)
    print("Final results per step:")
    for idx, res in final["results"].items():
        print(f"Step {idx+1}: {res}")

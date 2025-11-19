from langchain_ollama import ChatOllama
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from typing import Annotated

class AgentState(TypedDict):
	messages: Annotated[list, add_messages]
	steps: str
	current_step: int
	llm: ChatOllama

def get_new_state(state: AgentState, messages=None, steps=None, current_step=None):
	new_state = {
			"messages": state["messages"],
			"steps": state["steps"],
			"current_step": state["current_step"],
			"llm": state["llm"]
	}

	if messages is not None:
		new_state["messages"] = messages

	if steps is not None:
		new_state["steps"] = steps

	if current_step is not None:
		new_state["current_step"] = current_step

	return new_state

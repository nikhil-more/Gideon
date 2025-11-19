from agent_state import AgentState, get_new_state
from langchain_core.messages import HumanMessage

def listen_to_query(state: AgentState):
	"""Lister To User Query"""
	user_query = input("User : ")
	# return {"messages": [HumanMessage(content=user_query)], "steps": "", "llm":state["llm"]}
	return get_new_state(state, messages=[HumanMessage(content=user_query)], steps="", current_step=0)
from agent_state import AgentState

def has_user_asked_to_quit(state: AgentState):
	"""Decided if user has asked to end conversation or not"""
	system_message_for_quit = f"""
	You are helpful assistant capable of detecting whether
	user is asking to end the conversation or not. Given the following,
	conversation, determine if user has shown intent to quit conversation.
	Keep your response limited to Yes/No.

	User Query : {state["messages"][-1].content}
	"""
	response = state["llm"].invoke(system_message_for_quit)
	print("Quitting : ", response.content)
	if "Yes" in response.content:
		return "quit_conversation"
	return "split_instructions_in_steps"
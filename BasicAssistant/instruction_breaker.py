from langchain_ollama.chat_models import  ChatOllama
from typing import TypedDict, List
import json
from langgraph.graph import StateGraph, START, END

from BasicAssistant.assistant_prompts import INSTRUCTION_BREAK_DOWN_PROMPT, NEXT_NODE_DECIDER_PROMPT, ARRAY_FORMATTER_PROMPT
# from BasicAssistant.test_prompt import INSTRUCTION_BREAKDOWN_TEST_1, INSTRUCTION_BREAKDOWN_TEST_2

OLLAMA_MODEL = "llama3.1:8b-instruct-q4_1"
REASONING = False

model = ChatOllama(
		model = OLLAMA_MODEL,
		reasoning = REASONING
)

# messages = [
# 		("system", INSTRUCTION_BREAK_DOWN_PROMPT),
# 		("user", INSTRUCTION_BREAKDOWN_TEST_1)
# ]
#
# response = model.invoke(messages)
#
# response.pretty_print()
#
# messages = [
# 		("system", INSTRUCTION_BREAK_DOWN_PROMPT),
# 		("user", INSTRUCTION_BREAKDOWN_TEST_2)
# ]
#
# response = model.invoke(messages)
#
# response.pretty_print()

class AgentState(TypedDict):
	messages: List
	user_query: str
	raw_steps: str
	steps: List
	current_step: int

def get_new_agent_state(state: AgentState, messages:List = None, user_query:str = None, raw_steps:str = None, steps:List = None, current_step:int = None) -> AgentState:
	return {
			"messages": messages if messages is not None else state["messages"],
			"user_query": user_query if user_query is not None else state["user_query"],
			"raw_steps": raw_steps if raw_steps is not None else state["raw_steps"],
			"steps": steps if steps is not None else state["steps"],
			"current_step": current_step if current_step is not None else state["current_step"]
	}

def instruction_breaker(state: AgentState) -> AgentState:
	"""
	Breaks user query in an array of steps to perform
	:param state:
	:return:
	"""
	messages = [
		("system", INSTRUCTION_BREAK_DOWN_PROMPT),
		("user", state["user_query"])
	]

	response = model.invoke(messages)

	response.pretty_print()

	raw_steps = str(response.content)

	return get_new_agent_state(state, raw_steps=raw_steps, steps=[], current_step=-1)

def listener(state: AgentState) -> AgentState:
	"""
	Listens to user query and convert the audio into text
	:param state:
	:return:
	"""
	user_input = input("User Query : ")

	messages = state["messages"]
	messages.append(("user", user_input))

	return get_new_agent_state(state, messages=messages, user_query=user_input)

def steps_parser(state: AgentState) -> AgentState:
	raw_steps = state["raw_steps"]
	try:
		steps = json.loads(raw_steps)
		return get_new_agent_state(state, steps=steps)
	except json.decoder.JSONDecodeError as e:
		print("-" * 40)
		print("Error encountered while parsing steps. trying with llm now")
		messages = [
				("system", ARRAY_FORMATTER_PROMPT),
				("user", raw_steps)
		]

		response = model.invoke(messages)
		raw_steps = response.content
		steps = json.loads(raw_steps)

		return get_new_agent_state(state, raw_steps=raw_steps, steps=steps)

def should_continue_iterate(state: AgentState):
	if state["current_step"] >= len(state["steps"]):
		return "Listener"
	return "StepsIterator"

def steps_iterator(state: AgentState) -> AgentState:
	"""
	Iterates on steps provided to complete user's task
	:param state:
	:return:
	"""
	current_step = state["current_step"]
	current_step += 1
	return get_new_agent_state(state, current_step=current_step)

def launch_node(state: AgentState) -> AgentState:
	"""
	Launches requested application
	:param state:
	:return:
	"""
	action = state["steps"][state["current_step"]]
	print(f"[Launch Node] Executing Action : {action}")
	return get_new_agent_state(state)

def play_node(state: AgentState) -> AgentState:
	"""
	Plays requested video on YouTube
	:param state:
	:return:
	"""
	action = state["steps"][state["current_step"]]
	print(f"[Play Node] Executing Action : {action}")
	return get_new_agent_state(state)

def open_website_node(state: AgentState) -> AgentState:
	"""
	Opens requested website
	:param state:
	:return:
	"""
	action = state["steps"][state["current_step"]]
	print(f"[Open Website Node] Executing Action : {action}")
	return get_new_agent_state(state)

def answer_query_node(state: AgentState) -> AgentState:
	"""
	Answers user's query by taking in account, previous chat history
	:param state:
	:return:
	"""
	action = state["steps"][state["current_step"]]
	print(f"[Query Assistant Node] Executing Action : {action}")
	return get_new_agent_state(state)

def quit_node(state: AgentState) -> AgentState:
	"""
	Quits the conversation
	:param state:
	:return:
	"""
	action = state["steps"][state["current_step"]]
	print(f"[Quit Node] Executing Action : {action}")
	return get_new_agent_state(state)

def functionality_not_implemented_node(state: AgentState) -> AgentState:
	"""
	This node should be called if requested action
	is yet to be implemented in system
	:param state:
	:return:
	"""
	action = state["steps"][state["current_step"]]
	print(f"Sorry, following action is not yet supported : \n {action}")
	print("=" * 40)

	return get_new_agent_state(state)

def decide_next_action(state: AgentState) -> str:
	"""
	Decides which node should be visited
	:param state:
	:return:
	"""
	if state["current_step"] >= len(state["steps"]):
		return "Listener"

	current_step = state["current_step"]

	step = state["steps"][current_step]

	print(f"Executing Step : {current_step + 1} - {step}")

	messages = [
			("system", NEXT_NODE_DECIDER_PROMPT),
			("user", step)
	]
	response = model.invoke(messages)

	print(f"Next Node : {response.content}")

	return response.content

def print_agent_state(state: AgentState):
	"""
	Prints current state of Agent
	:param state:
	:return:
	"""

	messages = state["messages"],
	raw_steps = state["raw_steps"]
	steps = state["steps"]

	print("=" * 40)
	print("Messages : ")
	for message in messages:
		print(message)

	print("-" * 40)
	print(f"Raw Steps : {raw_steps}")

	print("-" * 40)
	print("Steps : ")
	for step in steps:
		print(step)


gideon_builder = StateGraph(AgentState)

gideon_builder.add_node("Listener", listener)
gideon_builder.add_node("InstructionBreaker", instruction_breaker)
gideon_builder.add_node("StepsParser", steps_parser)
gideon_builder.add_node("StepsIterator", steps_iterator)
gideon_builder.add_node("LaunchApplication", launch_node)
gideon_builder.add_node("PlayVideo", play_node)
gideon_builder.add_node("OpenWebsite", open_website_node)
gideon_builder.add_node("QueryAssistant", answer_query_node)
gideon_builder.add_node("QuitConversation", quit_node)

gideon_builder.add_edge(START, "Listener")

gideon_builder.add_edge("Listener", "InstructionBreaker")
gideon_builder.add_edge("InstructionBreaker", "StepsParser")
gideon_builder.add_edge("StepsParser", "StepsIterator")
gideon_builder.add_conditional_edges(
		"StepsIterator",
		lambda state: decide_next_action(state),
		{
				"LaunchApplication": "LaunchApplication",
				"PlayVideo": "PlayVideo",
				"OpenWebsite": "OpenWebsite",
				"QueryAssistant": "QueryAssistant",
				"QuitConversation": "QuitConversation",
				"Listener": "Listener"
		})
gideon_builder.add_edge("LaunchApplication", "StepsIterator")
gideon_builder.add_edge("PlayVideo", "StepsIterator")
gideon_builder.add_edge("OpenWebsite", "StepsIterator")
gideon_builder.add_edge("QueryAssistant", "StepsIterator")

gideon_builder.add_edge("QuitConversation", END)

gideon = gideon_builder.compile()

initial_state : AgentState = {
		"messages": [],
		"user_query": "",
		"raw_steps": "",
		"steps": [],
		"current_step": -1
}

final_state = gideon.invoke(initial_state, {"recursion_limit": 100})

print_agent_state(final_state)
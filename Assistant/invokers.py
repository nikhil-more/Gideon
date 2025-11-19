from langchain_ollama import ChatOllama
from langgraph.graph.state import CompiledStateGraph
from langchain_core.messages import HumanMessage

def stream_graph_updates(graph : CompiledStateGraph, config :  dict[str, dict[str, str]], user_input: str):
	for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}, config):
		for value in event.values():
			print("Assistant:", value["messages"][-1].content)

def invoke_graph(graph : CompiledStateGraph, config :  dict[str, dict[str, str]], user_input: str):
	messages = [HumanMessage(content=user_input)]

	messages = graph.invoke({"messages": messages}, config)

	for m in messages["messages"]:
		m.pretty_print()

def invoke_graph_with_messages(graph : CompiledStateGraph, config :  dict[str, dict[str, str]], messages: list):
	messages = graph.invoke({"messages": messages}, config)

	for m in messages["messages"]:
		m.pretty_print()

def stream_graph_updates_with_messages(graph : CompiledStateGraph, config :  dict[str, dict[str, str]], messages: list, llm: ChatOllama):
	for event in graph.stream({"messages": messages, "steps": "", "current_step":0, "llm": llm}, config):
		for value in event.values():
			print("Assistant:", value["messages"][-1].content)
			print("Steps:", value["steps"])
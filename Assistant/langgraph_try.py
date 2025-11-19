from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_ollama.chat_models import ChatOllama

from agent_state import AgentState, get_new_state
from system_nodes import listen_to_query
from node_decider import has_user_asked_to_quit
from invokers import stream_graph_updates_with_messages

llm = ChatOllama(model="openchat:latest")

def quit_conversation(state:AgentState):
	"""Initiate Closing of the Conversation Session"""
	return get_new_state(state)

def summarize_memory_to_retain(state:AgentState):
	"""Summarize Conversation done with User retaining key information,
	to help in future conversations with user"""
	return get_new_state(state)

def save_conversation_memory(state: AgentState):
	"""Save Conversation to memory"""
	return get_new_state(state)

def chatbot(state: AgentState):
	"""Provide Appropriate Response to messages"""
	return get_new_state(state)

def split_instructions_in_steps(state: AgentState):
	"""Split Instructions In steps"""
	system_message_for_splitting_in_steps = f"""
	You are a decomposition assistant. You receive query from user,
	the query can be a simple question, or an instruction of performing some actions.
	The actions can include
		1. Opening an application
		2. Playing some video on YouTube
		3. Opening a website
		4. Search on Google
	If receiving instructions to perform a actions other than these,
	then politely reply that the action is not currently supported.
	
	Following are some examples on the topic,
	
	User Query : Hey buddy, can you open YouTube for me
	Response : 1. Open YouTube website
	
	User Query : Can you open YouTube and play something just like this on it
	Response : 1. Play "Something Just Like This" on YouTube
	
	User Query : Please help me with working of langgraph. If possible play some video of it on YouTube
	Response :  1. Explain Langgraph Working
				2. Play langgraph related video on YouTube
				
	User Query : Hey gideon, I am working on a security authentication dotnet project. Can you open visual studio code for me. Ohh and also open some helpful articles around this topic on internet
	Response :  1. Applaud user for working on security authentication dotnet project in a sentence
				2. Open Visual Studio Code
				3. Search on Google for security authentication with dotnet related articles

	Instruction: {state["messages"][-1].content}
	
	Steps:
	1.
	"""
	response = llm.invoke(system_message_for_splitting_in_steps)
	return get_new_state(state, steps=response.content)

memory = MemorySaver()

graph_builder = StateGraph(AgentState)

graph_builder.add_node("listening", listen_to_query)
graph_builder.add_node("split_instructions_in_steps", split_instructions_in_steps)
# graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("quit_conversation", quit_conversation)
graph_builder.add_edge(START, "listening")
graph_builder.add_conditional_edges("listening", has_user_asked_to_quit)
graph_builder.add_edge("quit_conversation", END)
# graph_builder.add_edge("chatbot", "listening")
graph_builder.add_edge("split_instructions_in_steps", "listening")

graph = graph_builder.compile(checkpointer=memory)

# we assign a thread id to store the conversation
config = {"configurable": {"thread_id": "1"}}

messages = [SystemMessage(content="""You are a helpful query assistant. Provide appropriate response to user queries""")]
stream_graph_updates_with_messages(graph, config, messages, llm)
from typing import TypedDict, List, Dict, Any
import os
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from rich.console import Console
import re
import json

from assistant_tools import get_time, calc, http_get, launch_app
from assistant_prompts import SYSTEM_PROMPT

console = Console()

# Available tools for Agent to use
available_tools = [get_time, calc, http_get, launch_app]

# Create a lookup dictionary: tool_name -> tool_function for fast access
# This allows the agent to invoke tools be name string rather than function reference
tools_map = {tool.name: tool for tool in available_tools}

# ---------------------------------------------------------------------------------------------------
# AGENT STATE
# ---------------------------------------------------------------------------------------------------
class AgentState(TypedDict):
	messages: List[BaseMessage]
	iterations: int

MAX_ITER = 8

# ---------------------------------------------------------------------------------------------------
# LOCAL OLLAMA SETUP
# ---------------------------------------------------------------------------------------------------
OLLAMA_BASEURL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:latest")

model = ChatOllama(
		base_url=OLLAMA_BASEURL,
		model=OLLAMA_MODEL,
		temperature=0.0,    # Lower Temperature for more consistent formatting with 7B models
		# OpenChat-specific optimizations
		top_p=0.9,          # Slightly reduce randomness for better format adherence
		repeat_penalty=1.1  # Prevent repetitive response
)

# ---------------------------------------------------------------------------------------------------
# AGENT FUNCTIONS
# ---------------------------------------------------------------------------------------------------
def should_continue(state: AgentState) -> str:
	"""
	Determines the next node in the conversation flow.
	This prevents infinite loops by limiting the number of iterations.
	:param state:
	:return:
	"""
	# Safely check: stop if we've hit the maximum iteration limit
	# This prevents runaway conversation that could consume resources
	if state["iterations"] >= MAX_ITER:
		return END  # Terminal the conversation graph
	return "agent"  # Continue to the agent node for another response

def call_model(state: AgentState) -> Dict[str, Any]:
	messages = state["messages"]
	iterations = state["iterations"]

	# Ensure system prompt is always present at the beginning of conversation
	# This maintains consistent behavior and tool-calling format throughout the session
	if not messages or not isinstance(messages[0], SystemMessage):
		# Prepend system message to establish the agent's behavior and response format
		messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

	try:
		response = model.invoke(messages)
		new_messages = messages + [response]

		return {
				"messages": new_messages,
				"iterations": iterations + 1
		}
	except Exception as e:
		error_msg = f"Model_error: {str(e)}"
		console.print(f"[red]{error_msg}[/red]")
		error_response = AIMessage(content=f"FINAL_ANSWER: I encountered an error: {error_msg}")
		return {
				"messages": messages + [error_response],
				"iterations": iterations + 1
		}

def execute_tools(state: AgentState) -> Dict[str, Any]:
	messages = state["messages"]
	iterations = state["iterations"]

	last_message = messages[-1]
	if not isinstance(last_message, AIMessage):
		return {"messages": messages, "iterations": iterations}

	content = last_message.content.strip()

	# Check if this is a final answer
	if "FINAL_ANSWER" in content:
		return {"messages": messages, "iterations": iterations}

	# Try to extract and execute tool call
	try:
		# Use regex to extract JSON tool call from the AI's structured response
		# DOTALL flag allows matching across newlines in case JSON spans multiple lines
		action_match = re.search(r'ACTION_JSON:\s*(\{.*?\})', content, re.DOTALL)
		if not action_match:
			# No tool call pattern found, assume this is a final answer that needs no tools
			return {"messages": messages, "iterations": iterations}

		# Extract the json portion from the regex match (group 1)
		action_json = action_match.group()
		# Parse the JSON string into a Python dictionary
		action_data = json.loads(action_json)

		# Extract tool name and arguments from the parse JSON structure
		tool_name = action_data.get("tool")
		tool_args = action_data.get("args", {}) # Default to empty dict if no args provided

		if tool_name not in tools_map:
			result = f"Error: Unknown tool '{tool_name}'"
		else:
			tool = tools_map[tool_name]
			try:
				if tool_args:
					result = tool.invoke(tool_args)
				else:
					result = tool.invoke({})
			except Exception as e:
				result = f"Tool execution error: {str(e)}"

		# Feed the tool's output back to the agent as a human message
		# This creates a conversation flow: User -> AI -> Tool -> AI (with tool result)
		tool_message = HumanMessage(content=f"Total result: {result}")
		new_messages = messages + [tool_message]

		return {
				"messages": new_messages,
				"iterations": iterations
		}
	except json.JSONDecodeError as e:
		error_msg = f"JSON parsing error: {str(e)}. Please use exact format: ACTION_JSON: {{\"tool\": \"tool_name\", \"args\": {{...}}}}"
		error_message = HumanMessage(content=f"Error: {error_msg}")
		return {
				"messages": messages + [error_message],
				"iterations": iterations
		}
	except Exception as e:
		error_msg = f"Tool execution error: {str(e)}"
		error_message = HumanMessage(content=f"Error: {error_msg}")
		return {
				"messages": messages + [error_message],
				"iterations": iterations
		}

# Create the graph
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", execute_tools)

workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue, {"agent": "tools", END:END})
workflow.add_edge("tools", "agent")

app = workflow.compile()

# ---------------------------------------------------------------------------------------------------
def pretty_print_last(state: AgentState):
	try:
		last = state["messages"][-1]
		if isinstance(last, AIMessage):
			console.print("[bold cyan]AI:[/]", last.content)
		else:
			console.print("[bold green]MSG:[/]", str(last))
	except Exception as e:
		console.print(f"[red]Print error: {e}[/]")

def run_interactive():
	console.print(f"[bold]Local Agent ready (model={OLLAMA_MODEL} base={OLLAMA_BASEURL})[/]")
	console.print("[dim]Available tools: get_time, calc, http_get, launch_app[/]")
	console.print("[dim]Type 'quit' or press Ctrl+C to exit[/]")

	chat_state: AgentState = {"messages": [], "iterations": 0}

	while True:
		try:
			user_in = input("\nYou: ").strip()
		except (EOFError, KeyboardInterrupt):
			print("\nExiting.")
			break

		if not user_in:
			continue

		if user_in.lower() in ('quit', 'exit', 'bye'):
			print("Goodbye!")
			break

		# Add the user's input to the conversation history as a HumanMessage
		chat_state["messages"].append(HumanMessage(content=user_in))
		# Reset iterator counter for each new user input to prevent cross-turn limits
		chat_state["iterations"] = 0    # Each user turn gets fresh MAX_ITER attempts

		try:
			# Execute the Langgraph workflow: agent -> tools -> agent ... until END
			# This runs the complete reasoning loop including tool calls and responses
			final_state = app.invoke(chat_state)
			chat_state = final_state    # Update state with the complete conversation
			pretty_print_last(chat_state)

		except Exception as e:
			console.print(f"[red]Error during execution: {e}[/]")
			# reset state on error
			chat_state = {"messages": [], "iterations": 0}

# ---------------------------------------------------------------------------------------------------
if __name__ == "__main__":
	try:
		run_interactive()
	except Exception as e:
		console.print(f"[red]Fatal error: {e}[/]")
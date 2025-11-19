from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langchain_ollama.chat_models import ChatOllama
from langgraph.graph.state import CompiledStateGraph
import re

from helper_tools import play_video, launch_application, search_web
from listener import Listener
from speaker import Speaker
import torch

SYSTEM_PROMPT = """You are a helpful personal assistant.
Your task is to hold a friendly conversation with user,
while also completing the requests made by him using the tools provided.

STRICT RULES:
    - Keep responses short and informational
    - Do not use  icons
    - Do not use emoji

NOTE : It is not required to call a tool for every task. Use tools only if required or specifically asked
"""

class AgentState(TypedDict):
    messages: List[str]

class Assistant:
    def __init__(self):
        self.assistant : CompiledStateGraph = None
        self.model : ChatOllama = None
        self.is_ready = False
        self.available_tools : List = [play_video, launch_application, search_web]
        self.previous_conversations = [
                ("system", SYSTEM_PROMPT)
            ]
        self.emoji_pattern = re.compile("["
                                   u"\U0001F600-\U0001F64F"  # emoticons
                                   u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                   u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                   u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                   "]+", flags=re.UNICODE)

        self.listener = Listener()
        self.speaker = Speaker()
        self.initialize_llm(model_name="qwen3:4b")
        self.setup_assistant_workflow()
        # self.speaker.speak("I am ready to go!!")

    def initialize_llm(self, model_name: str = "qwen3:4b"):
        llm = ChatOllama(
                model=model_name
        )
        self.model = llm.bind_tools(self.available_tools)

    def process(self, state: AgentState):
        messages = state["messages"]
        response = self.model.invoke(messages)

        print(response.pretty_print())

        self.previous_conversations.append(
                ("assistant", response.content)
        )

        speaker_sentence = self.parse_response(response.content)

        if speaker_sentence is not None or speaker_sentence!="None":
            self.speak(speaker_sentence)
        else:
            print("Invalid Response Content")
            print(response)

        return {
                "messages": messages + [("assistant", response.content)]
        }

    def setup_assistant_workflow(self):
        if self.model is None:
            self.initialize_llm(model_name="qwen3:4b")
        workflow = StateGraph(AgentState)

        workflow.add_node("assistant", self.process)

        workflow.add_edge(START, "assistant")
        workflow.add_edge("assistant", END)

        self.assistant = workflow.compile()

        self.is_ready = True

    def invoke_workflow(self, user_query):
        self.previous_conversations.append(
                ("user", user_query)
        )
        initial_agent_state = {
                "messages": self.previous_conversations
        }

        final_state = self.assistant.invoke(initial_agent_state)

    def listen(self):
        rec_text = self.listener.listen()
        return rec_text

    def speak(self, text):
        self.speaker.speak(text)

    def start_session(self):
        if not self.is_ready:
            self.setup_assistant_workflow()
        try:
            print("Starting...")
            rec_text = self.listen()
            self.invoke_workflow(rec_text)
        except Exception as e:
            print(e)
            self.speaker.speak("Error Encountered")

    def parse_response(self, response):
        response = response.split('</think>')[-1]

        response = self.emoji_pattern.sub(r'', response)  # no emoji

        return response

if __name__=="__main__":
    try:
        print(torch.cuda.memory_summary())
        torch.cuda.empty_cache()
        gideon = Assistant()
        while True:
            gideon.start_session()
    except Exception as e:
        print(e)
        print(torch.cuda.memory_summary())

from langchain_core.tools import tool
from pywhatkit import playonyt, search
import subprocess

@tool()
def play_video(request_text: str):
	"""
	Plays requested video on YouTube
	:param request_text: video/audio to play on YouTube
	:return:
	"""
	print("Playing....", request_text)
	playonyt(request_text)

@tool()
def launch_application(command: str):
	"""
	Executes given command with subprocess module
	to launch an application
	:param command: command required to open an application on ubuntu using terminal
	:return:
	"""
	print("Launching ..... ", command)
	# subprocess.Popen()

@tool()
def search_web(search_text: str):
	"""
	Searches for given text on web
	:param search_text: keywords to search for on web
	:return:
	"""
	print("Searching for .....", search_text)
	search(search_text)
import torch
from TTS.api import TTS
import os
from playsound import playsound

sample_text = """So um mm [laughs], this is interesting. You want me to speak in my native language right? 
I hope this voice is more humane to you 
And you will use my voice in your project.
I will be the assistant's voice"""

class Speaker:
	def __init__(self):
		self.tts : TTS = None

	def initialize_tts(self):
		"""
		Initializes tts engine
		:return:
		"""
		os.environ["TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD"] = "1"
		device = "cuda" if torch.cuda.is_available() else "cpu"
		self.tts = TTS("tts_models/en/ek1/tacotron2").to(device)

	def transform_text_to_speech(self, text : str):
		"""
		Creates audio file 'output.wav' for given text
		:param text:
		:return:
		"""
		if self.tts is None:
			self.initialize_tts()
		self.tts.tts_to_file(text=text, file_path="output.wav")

	def speak(self, text : str):
		"""
		Creates and Plays speech for provided text
		:param text:
		:return:
		"""
		self.transform_text_to_speech(text)
		playsound("./output.wav")

	def cleanup(self):
		pass
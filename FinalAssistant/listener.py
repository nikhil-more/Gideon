import sounddevice as sd
import queue
from faster_whisper import WhisperModel

class Listener:
	def __init__(self):
		self.model : WhisperModel = WhisperModel("small.en", device="cpu", compute_type="int8")
		self.samplerate = 16000
		self.block_duration = 0.5   #seconds
		self.chunk_duration = 2     #seconds
		self.channels = 1
		self.rec_duration = 5

		self.frames_per_block = int(self.samplerate * self.block_duration)
		self.frames_per_chunk = int(self.samplerate * self.chunk_duration)

		self.audio_queue = queue.Queue()
		self.audio_buffer = []

	def initialize_whisper(self):
		self.model = WhisperModel("small.en", device="cpu", compute_type="int8")

	def transcriber(self, audio_data):
		segments, _ = self.model.transcribe(
				audio_data,
				language="en",
				beam_size=1  # Max Speed
		)

		if not segments:
			return "Nothing Recorded"
		sentence = ""
		for segment in segments:
			sentence += segment.text
		return sentence

	def record_speech(self):
		sd.stop()
		try:
			wav = sd.rec(self.rec_duration * self.samplerate, self.samplerate, 1)
		except Exception as e:
			print(e)
			return None
		sd.wait()
		return wav.squeeze()

	def listen(self) -> str:
		if self.model is None:
			self.initialize_whisper()
		print("Listening....")
		audio = self.record_speech()
		sd.wait()
		print("Recording Finished...")
		transcribed_text = self.transcriber(audio)

		print(transcribed_text)
		return transcribed_text
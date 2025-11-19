import torch
from TTS.api import TTS
import os

os.environ["TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD"] = "1"

# Get device
# device = "cuda" if torch.cuda.is_available() else "cpu"

# List available 🐸TTS models
# print(TTS().list_models())

device = "cuda" if torch.cuda.is_available() else "cpu"

# Init TTS
# tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
tts = TTS("tts_models/en/ek1/tacotron2").to(device)

# Run TTS
# ❗ Since this model is multi-lingual voice cloning model, we must set the target speaker_wav and language
# Text to speech list of amplitude values as output
# wav = tts.tts(text="Hello world!", speaker_wav="my/cloning/audio.wav", language="en")

text = """So ummm [laughs], this is interesting. You want me to speak in my native language right? 
I hope this voice is more humane to you 
And you will use my voice in your project.
I will be the assistant's voice"""

# Text to speech to a file
tts.tts_to_file(text=text, file_path="output.wav")
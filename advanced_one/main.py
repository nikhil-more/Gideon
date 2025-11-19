import os
import asyncio
import pyaudio
import struct
import webbrowser
import pygame
import speech_recognition as sr
from dotenv import load_dotenv
from faster_whisper import WhisperModel
from google import genai
from google.genai import types
import edge_tts
import pvporcupine


# --- Configuration ---
load_dotenv()
GEMINI_KEY = os.getenv("GOOGLE_API_KEY")
PICOVOICE_KEY = os.getenv("PICOVOICE_API_KEY")

# -- Tools Definition ---

# Tool A : Custom function to open websites
def open_website(url: str):
    """Opens a website in default browser"""
    webbrowser.open(url)
    return "Website opened successfully."

# Tool B: Google search is built in

# --- 2. SETUP CLIENTS ---
# Gemini client with tools
client = genai.Client(api_key=GEMINI_KEY)

# Whisper model
print("Loading Whisper Model")
whisper_model = WhisperModel("base.en", device="cpu", compute_type="int8")

# TTS Setup
pygame.mixer.init()

# --- 3. HELPER FUNCTIONS ---

async def speak(text: str):
    """Text to Speech using Edge-TTS"""
    print(f"Jarvis: {text}")
    voice = "en-GB-RyanNeural"  # Crisp male voice
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save("reply.mp3")

    pygame.mixer.music.load("reply.mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.1)

def listen_for_command():
    """Records audio after wake word is detected"""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for command...")
        audio = r.listen(source, timeout=5, phrase_time_limit=10)

        # Save to temp file for Whisper
        with open("command.wav", "wb") as f:
            f.write(audio.get_wav_data())
    return "command.wav"

def transcribe_audio(file_path):
    "Transcribes audio using Faster-Whisper"
    segments, _ = whisper_model.transcribe(file_path, beam_size=5)
    text = " ".join([segment.text for segment in segments])
    return text


# --- 4. MAIN BRAIN (GEMINI) ---

def ask_jarvis(prompt, history):
    """Sends prompt to Gemini with Search & Function Calling enabled"""

    # Define Tools
    google_search_tool = types.Tool(google_search=types.GoogleSearch())
    # website_tool = types.Tool(function_declarations=[open_website])

    # Generate content with tools config
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=history + [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
        config=types.GenerateContentConfig(
            tools=[google_search_tool],
            temperature=0.7
        )
    )

    # Handle Function Calls (The "Brain" deciding to do something)
    if response.function_calls:
        for call in response.function_calls:
            if call.name == "open_website":
                # Execute the python function
                result = open_website(**call.args)

                # Pass result back to Gemini so it can say "Okay, I opened it"
                # (Simplified: In a full app, you'd send a tool_response back.
                # For now, we just return a confirmation message.)
                return "I have opened the website for you, sir."
    
    return response.text

# --- 5. THE WAKE WORD LOOP ---

async def main_loop():
    # Initialize Porcupine (Wake Word)
    porcupine = pvporcupine.create(access_key=PICOVOICE_KEY, keywords=["jarvis"])
    pa = pyaudio.PyAudio()
    audio_stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length
    )

    chat_history = []
    print("System Online. Say 'Jarvis'...")

    try:
        while True:
            # # Read audio frame
            # pcm = audio_stream.read(porcupine.frame_length)
            # pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

            # # Check the Wake Word
            # keyword_index = porcupine.process(pcm)
            keyword_index = 1
            if keyword_index >= 0:
                print("Wake Word Detected...")
                # 1. Record User
                audio_file = listen_for_command()

                # 2. Transcribe (Faster Whisper)
                user_text = transcribe_audio(file_path=audio_file)
                print(f"You : {user_text}")

                if user_text.strip():
                    # 3. Think & Act (Gemini)
                    response_text = ask_jarvis(user_text, chat_history)

                    # 4. Speak 
                    await speak(response_text)

                    # Update History (Simple Sliding Window)
                    chat_history.append(types.Content(role="user", parts=[types.Part.from_text(text=user_text)]))
                    chat_history.append(types.Content(role="model", parts=[types.Part.from_text(text=response_text)]))
            
            await asyncio.sleep(0.01)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        audio_stream.close()
        pa.terminate()
        porcupine.delete()

if __name__=="__main__":
    asyncio.run(main_loop())
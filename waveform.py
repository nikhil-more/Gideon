import sounddevice as sd
import numpy as np
import matplotlib.pyplot as plt

# Settings
duration = 10  # seconds
samplerate = 44100
window_size = 1024

# Set up the plot
fig, ax = plt.subplots()
x = np.arange(0, window_size)
line, = ax.plot(x, np.zeros(window_size))
ax.set_ylim([-1, 1])
ax.set_xlim([0, window_size])

# Callback to update waveform
def audio_callback(indata, frames, time, status):
    if status:
        print(status)
    line.set_ydata(indata[:, 0])
    plt.draw()
    plt.pause(0.001)

print("🎙️ Speak into the microphone...")

# Use blocking stream in main thread
with sd.InputStream(callback=audio_callback, channels=1, samplerate=samplerate, blocksize=window_size):
    plt.show()

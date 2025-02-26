import sounddevice as sd

print("Listening for 5 seconds...")
recording = sd.rec(int(5 * 16000), samplerate=16000, channels=1, dtype='int16')
sd.wait()
print("Recording complete. If no errors, the mic is working.")

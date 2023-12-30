from openai import OpenAI
import pyttsx3
from google.cloud import speech
import sounddevice as sd
from scipy.io.wavfile import write

# Create client to OpenAI, gets API Key from environment variable OPENAI_API_KEY
client = OpenAI()

# Open text to speech engine
engine = pyttsx3.init()
engine.setProperty('voice', "com.apple.voice.compact.sv-SE.Alva")  # The only Swedish voice

def speech_to_text(
    config: speech.RecognitionConfig,
    audio: speech.RecognitionAudio,
) -> speech.RecognizeResponse:
    client = speech.SpeechClient()
    # Synchronous speech recognition request
    response = client.recognize(config=config, audio=audio)
    return response

# Prompt the user to ask a question
question = "Ställ din fråga till OpenAI!"
print(question)
engine.say(question)
engine.runAndWait()  # empty output buffer

# Record the sound
freq = 48000
duration = 5
# Start recorder with the given values of duration and sample frequency
recording = sd.rec(int(duration * freq), samplerate=freq, channels=1, dtype='int16')
sd.wait()  # Wait for recording to finish

# Save recording in temporary file (temporary workaround to get correct format)
write("recording.wav", freq, recording)

# Read back recording from file
with open("recording.wav", "rb") as audio_file:
    audiodata = audio_file.read()

# Convert speech to text using Google's speech recognition. Gets credentials from json file
# pointed to in environment variable GOOGLE_APPLICATION_CREDENTIALS
audio = speech.RecognitionAudio(
    content=audiodata,
)
config = speech.RecognitionConfig(
    language_code="sv-SE",
)
response = speech_to_text(config, audio)
for result in response.results:
    transcript = result.alternatives[0].transcript + "?"
    print(transcript)

# Send request to OpenAI
print("Sending request to GPT-3.5, waiting for reply...")
completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {
            "role": "assistant",
            "content": "Answer so that a seven-year-old would understand. Use at most 30 words.",
        },
        {
            "role": "user",
            "content": transcript,
        },
    ],
)
# Extract the text reply part
reply = completion.choices[0].message.content
print(reply)

# Read the response aloud
engine.say(reply)    # convert text to speech
engine.runAndWait()  # wait for speech to finish
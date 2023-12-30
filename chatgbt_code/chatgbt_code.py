from openai import OpenAI
from google.cloud import speech
from google.cloud import texttospeech
import pygame
import sounddevice as sd
from scipy.io.wavfile import write

print("Chatbot started")

# Create client to OpenAI, gets API Key from environment variable OPENAI_API_KEY
client = OpenAI()

# Instantiate a client for Google Text-to-Speech
tts_client = texttospeech.TextToSpeechClient()

def speech_to_text(config: speech.RecognitionConfig, audio: speech.RecognitionAudio) -> speech.RecognizeResponse:
    client = speech.SpeechClient()
    print("Speech to text started")
    response = client.recognize(config=config, audio=audio)
    return response

def text_to_speech(text: str, output_filename: str):
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(language_code="sv-SE", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL)
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    response = tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    with open(output_filename, "wb") as out:
        out.write(response.audio_content)

# Prompt the user to ask a question
question = "Ställ din fråga till OpenAI!"
print(question)
text_to_speech(question, "question.mp3")

# Record the sound
freq = 48000
duration = 5
# Start recorder with the given values of duration and sample frequency
recording = sd.rec(int(duration * freq), samplerate=freq, channels=1, dtype='int16')
sd.wait()  # Wait for recording to finish

# Save recording in temporary file (temporary workaround to get correct format)
write("recording.wav", freq, recording)

# Read the audio file
with open("recording.wav", "rb") as audio_file:
    audiodata = audio_file.read() # Read the audio file

audio = speech.RecognitionAudio(content=audiodata) # Create audio object for Google's speech recognition

# Convert speech to text using Google's speech recognition. Gets credentials from json file
# pointed to in environment variable GOOGLE_APPLICATION_CREDENTIALS
audio = speech.RecognitionAudio(
    content=audiodata,
)
config = speech.RecognitionConfig( # Configuration for the recognizer
    language_code="sv-SE", # Language code for Swedish
)
response = speech_to_text(config, audio) # Send request to API
for result in response.results: # Print the result
    print("Google Speech Recognition thinks you said:")
    transcript = result.alternatives[0].transcript + "?" # Add question mark to transcript
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

# Convert text to speech
text_to_speech(reply, "response.mp3")

# Initialize pygame mixer
pygame.mixer.init()

# Load the mp3 file
pygame.mixer.music.load("response.mp3")

# Play the mp3 file
pygame.mixer.music.play()

# Wait for the audio to finish playing
while pygame.mixer.music.get_busy():
    pygame.time.Clock().tick(10)
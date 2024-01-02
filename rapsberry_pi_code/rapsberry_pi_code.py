from openai import OpenAI
from google.cloud import speech
from google.cloud import texttospeech
import pygame
import sounddevice as sd
from scipy.io.wavfile import write
import pyaudio
import wave
import os
from digitalio import DigitalInOut, Direction, Pull
import board

print("Chatbot started")

# Create client to OpenAI, gets API Key from environment variable OPENAI_API_KEY
client = OpenAI()

# Instantiate a client for Google Text-to-Speech
tts_client = texttospeech.TextToSpeechClient()

# Initialize transcript
transcript = ""

# Setup button
button = DigitalInOut(board.D17) # Button connected to pin 17
button.direction = Direction.INPUT # Input
button.pull = Pull.UP # Pull up resistor

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

# Initialize pygame mixer
FORMAT = pyaudio.paInt16
CHANNELS = 1           # Number of channels
BITRATE = 44100        # Audio Bitrate
CHUNK_SIZE = 2048     # Chunk size to 
RECORDING_LENGTH = 10  # Recording Length in seconds
WAVE_OUTPUT_FILENAME = "recording.wav"
audio = pyaudio.PyAudio()
device_id = 2 # Choose a device adafriut voice bonnet

print("Recording using Input Device ID "+str(device_id))

stream = audio.open( # Open the stream
    format=FORMAT, # Format
    channels=CHANNELS, # Number of channels
    rate=BITRATE, # Bitrate
    input=True, # Input 
    input_device_index = device_id, # Input device
    frames_per_buffer=CHUNK_SIZE # Chunk size
)

recording_frames = [] # Initialize recording frames

while True: # Loop forever
    if not button.value:  # Button is pressed
        for i in range(int(BITRATE / CHUNK_SIZE * RECORDING_LENGTH)): # Record for RECORDING_LENGTH seconds
            data = stream.read(CHUNK_SIZE) # Read data from stream
            recording_frames.append(data) # Append data to recording frames

        stream.stop_stream() # Stop the stream
        stream.close() # Close the stream
        audio.terminate() # Terminate the audio

        # Save recording to file
        waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb') # Open the file
        waveFile.setnchannels(CHANNELS) # Set number of channels
        waveFile.setsampwidth(audio.get_sample_size(FORMAT)) # Set sample width
        waveFile.setframerate(BITRATE) # Set framerate
        waveFile.writeframes(b''.join(recording_frames)) # Write frames to file
        waveFile.close() # Close the file

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
                    "content": "Answer the question, Use at most 30 words, and in Swedish.",
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
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
from PIL import Image, ImageDraw, ImageFont
import adafruit_sharpmemorydisplay
import busio
import digitalio
import textwrap

print("Chatbot started")

# Create client to OpenAI, gets API Key from environment variable OPENAI_API_KEY
client = OpenAI()

# Instantiate a client for Google Text-to-Speech
tts_client = texttospeech.TextToSpeechClient()

# Initialize transcript
transcript = ""

# Initialize PyAudio
py_audio = pyaudio.PyAudio()

# Setup button
button = DigitalInOut(board.D17) # Button connected to pin 17
button.direction = Direction.INPUT # Input
button.pull = Pull.UP # Pull up resistor

# Initialize the SPI and the display
spi = busio.SPI(board.SCK, MOSI=board.MOSI)
scs = digitalio.DigitalInOut(board.D6)  # inverted chip select
display = adafruit_sharpmemorydisplay.SharpMemoryDisplay(spi, scs, 144, 168)

# Clear the display
display.fill(1)
display.show()

# Load a TrueType or OpenType font
font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
if os.path.isfile(font_path):
    font = ImageFont.truetype(font_path, 12)  # Increase the size to 30
else:
    print(f"The file {font_path} does not exist.")

# Create an image to draw on
image = Image.new('1', (display.width, display.height), color=1)

# Create a draw object
draw = ImageDraw.Draw(image)

# Calculate the maximum number of characters that can fit in a line
bbox = draw.textbbox((0, 0), "x", font=font)
char_width, char_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
max_chars = display.width // char_width

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
BITRATE = 48000        # Audio Bitrate
CHUNK_SIZE = 2048     # Chunk size to 
RECORDING_LENGTH = 7  # Recording Length in seconds
WAVE_OUTPUT_FILENAME = "recording.wav"
audio = pyaudio.PyAudio()
device_id = 2 # Choose a device adafriut voice bonnet

print("Recording using Input Device ID "+str(device_id))

print("Press the button to ask a question")

while True: # Loop forever    
    if not button.value:  # Button is pressed
        print("Button pressed")
        
        # Clear the display
        display.fill(1)
        display.show()

        stream = py_audio.open( # Open the stream
            format=FORMAT, # Format
            channels=CHANNELS, # Number of channels
            rate=BITRATE, # Bitrate
            input=True, # Input 
            input_device_index = device_id, # Input device
            frames_per_buffer=CHUNK_SIZE # Chunk size
        )
        recording_frames = [] # Initialize recording frames

        for i in range(int(BITRATE / CHUNK_SIZE * RECORDING_LENGTH)): # Record for RECORDING_LENGTH seconds
            data = stream.read(CHUNK_SIZE) # Read data from stream
            recording_frames.append(data) # Append data to recording frames

        # Correct
        stream.stop_stream()
        stream.close()

        # Save recording to file
        waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb') # Open the file
        waveFile.setnchannels(CHANNELS) # Set number of channels
        waveFile.setsampwidth(py_audio.get_sample_size(FORMAT)) # Set sample width
        waveFile.setframerate(BITRATE) # Set framerate
        waveFile.writeframes(b''.join(recording_frames)) # Write frames to file
        waveFile.close() # Close the file

        # Read the audio file
        with open("recording.wav", "rb") as audio_file:
            audiodata = audio_file.read() # Read the audio file

        recognition_audio = speech.RecognitionAudio(content=audiodata) # Create audio object for Google's speech recognitionCreate audio object for Google's speech recognition

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
            # Draw the text on the image
            text = transcript
            wrapped_text = textwrap.fill(text, width=max_chars, break_long_words=True)
            lines = wrapped_text.split('\n')
            y_text = 0
            for line in lines:
                bbox = draw.textbbox((0, y_text), line, font=font)
                width, height = bbox[2] - bbox[0], bbox[3] - bbox[1]
                if y_text + height > display.height:
                    break
                draw.text((0, y_text), line, font=font, fill=0)
                y_text += height

            # Display the image on the display
            display.image(image)
            display.show()

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

        # Draw a line to separate the question and the response
        y_text += font.getsize(' ')[1]
        draw.line((0, y_text, display.width, y_text), fill=0)

        # Draw the text on the image
        text = reply
        wrapped_text = textwrap.fill(text, width=max_chars, break_long_words=True)
        lines = wrapped_text.split('\n')
        y_text += font.getsize(' ')[1]
        for line in lines:
            bbox = draw.textbbox((0, y_text), line, font=font)
            width, height = bbox[2] - bbox[0], bbox[3] - bbox[1]
            if y_text + height > display.height:
                break
            draw.text((0, y_text), line, font=font, fill=0)
            y_text += height
        
        # Display the image on the display
        display.image(image)
        display.show()

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

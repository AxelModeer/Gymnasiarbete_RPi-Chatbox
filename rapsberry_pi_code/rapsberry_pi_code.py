# Standard library imports
import os
import time
import atexit
import wave
import textwrap

# Third party imports

# Audio processing libraries
import pyaudio
import pygame
import sounddevice as sd
from scipy.io.wavfile import write

# Google Cloud services
from google.cloud import speech, texttospeech

# Machine learning library
from openai import OpenAI

# Hardware interaction libraries
import busio
import digitalio
import neopixel
import adafruit_dotstar
import adafruit_sharpmemorydisplay

# Local application/library specific imports
from PIL import Image, ImageDraw, ImageFont
from digitalio import DigitalInOut, Direction, Pull
import board

print("Chatbot started")

# Set environment variables
os.environ['OPENAI_API_KEY'] = "key"
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "key.json"

#setup LEDs on the bonnet
DOTSTAR_DATA = board.D5
DOTSTAR_CLOCK = board.D6 
dots = adafruit_dotstar.DotStar(DOTSTAR_CLOCK, DOTSTAR_DATA, 3, brightness=0.1)

#setup LEDs on the ring
pixels = neopixel.NeoPixel(board.D12, 16)
pixels.brightness = 0.1

def exit_handler(): # Turn off the LEDs and clear the display when the program exits
    # Clear the display
    display.fill(1)
    display.show()

    # Turn off all audio devices
    pygame.mixer.quit()
    stream.stop_stream()
    stream.close()
    py_audio.terminate()

    set_color(0, 0, 0)  # Set all LEDs to off

# Register the exit handler
atexit.register(exit_handler)

def set_color(r, g, b):
    for i in range(3):
        dots[i] = (g, b, r)  # Change the order to GBR, because it is the oder that the bonnet uses
    dots.show()
    pixels.fill((r, g, b)) # Set all LEDs to the specified color
    pixels.show()
    
set_color(255, 255, 0)  # Set all LEDs to yellow

# Function to convert speech to text
def speech_to_text(_config: speech.RecognitionConfig, _audio: speech.RecognitionAudio) -> speech.RecognizeResponse: 
    print("Speech to text started")
    _response = stt_client.recognize(config=_config, audio=_audio) # Send request to API
    return _response # Return the response

# Function to convert text to speech
def text_to_speech(_text: str, _output_filename: str): 
    _synthesis_input = texttospeech.SynthesisInput(text=_text) # Create input for the text to speech
    _voice = texttospeech.VoiceSelectionParams(language_code="sv-SE", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL) # Set the voice
    _audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3) # Set the audio encoding
    _response = tts_client.synthesize_speech(input=_synthesis_input, voice=_voice, audio_config=_audio_config) # Send request to API
    with open(_output_filename, "wb") as out: # Write the response to a file
        out.write(_response.audio_content)

# Function to handle errors
def handle_error(problem):
    
    set_color(255, 0, 0)  # Set all LEDs to red

    # Clear the display
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, display.width, display.height), fill=1)
    display.image(image)
    display.show()

    # Draw the error message on the image
    draw = ImageDraw.Draw(image)
    text = str(problem)
    wrapped_text = textwrap.fill(text, width=max_chars, break_long_words=True)
    lines = wrapped_text.split('\n')
    y_text = 0  # Initialize y_text here
    for line in lines:
        bbox = draw.textbbox((0, y_text), line, font=font)
        width, height = bbox[2] - bbox[0], bbox[3] - bbox[1]
        if y_text + height > display.height:
            break
        draw.text((0, y_text), line, font=font, fill=0)
        y_text += height

    # Display the image
    display.image(image)
    display.show()

    # Wait for user input before closing the program
    input("Press ENTER to close the program.")

try:
    # Create client to OpenAI, gets API Key from environment variable OPENAI_API_KEY
    client = OpenAI()

    # Instantiate a client for Google Text-to-Speech API
    tts_client = texttospeech.TextToSpeechClient()
    # Create a client for Google's speech recognition API
    stt_client = speech.SpeechClient() 

    # Initialize transcript
    transcript = ""

    # Setup button
    button = DigitalInOut(board.D17) # Button connected to pin 17
    button.direction = Direction.INPUT # Input
    button.pull = Pull.UP # Pull up resistor

    # Initialize the SPI and the display
    spi = busio.SPI(board.SCK, MOSI=board.MOSI)
    scs = digitalio.DigitalInOut(board.D26)  # inverted chip select
    display = adafruit_sharpmemorydisplay.SharpMemoryDisplay(spi, scs, 144, 168)

    # Clear the display
    display.fill(1)
    display.show()

    # Load a TrueType or OpenType font
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    if os.path.isfile(font_path):
        font = ImageFont.truetype(font_path, 12)  # Increase the size to 12
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

    print("Press the button to ask a question")
    set_color(0, 255, 0)  # Set all LEDs to green

    while True: # Loop forever    
        if not button.value:  # Button is pressed
            print("Button pressed")

            # initialize audio recording
            FORMAT = pyaudio.paInt16 # Format of the audio
            CHANNELS = 1           # Number of channels 
            BITRATE = 48000        # Audio Bitrate
            CHUNK_SIZE = 2048     # Chunk size to 
            RECORDING_LENGTH = 7  # Recording Length in seconds
            WAVE_OUTPUT_FILENAME = "recording.wav" # Name of the file to save the recording to
            py_audio = pyaudio.PyAudio() # Initialize PyAudio
            device_id_input = 3 # Choose a device adafriut voice bonnet 2 if using monitor 1 if not
            device_id_output = 1 # Choose a device bcm2835 Headphones
            
            # Clear the display by drawing a rectangle that covers the entire screen
            draw = ImageDraw.Draw(image)
            draw.rectangle((0, 0, display.width, display.height), fill=1)
            display.image(image)
            display.show()           
            
            stream = py_audio.open( # Open the stream
                format=FORMAT,
                channels=CHANNELS,
                rate=BITRATE,
                input=True,
                output=True,
                input_device_index=device_id_input,
                output_device_index=device_id_output, # Index of 'bcm2835 Headphones'
                frames_per_buffer=CHUNK_SIZE
            )
            recording_frames = [] # Initialize recording frames

            set_color(0, 0, 255)  # Set all LEDs to blue

            while not button.value:  # Record as long as the button is being pressed
                data = stream.read(CHUNK_SIZE)  # Read data from stream
                recording_frames.append(data)  # Append data to recording frames

            set_color(0, 255, 255)  # Set all LEDs to cyan

            # Stop the stream
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
                audiodata = audio_file.read() # Read the audio file and save as binary data

            # Send request to Google's speech recognition
            audio = speech.RecognitionAudio(content=audiodata,) # Create audio object for Google's speech recognition
            config = speech.RecognitionConfig(language_code="sv-SE",) # Set the language code
            response = speech_to_text(config, audio) # Send request to API

            y_text = 0  # Initialize y_text here
            if response.results: # If there is a response aka if the API understood the audio
                for result in response.results: # Print the result
                    print("Google Speech Recognition thinks you said:")
                    transcript = result.alternatives[0].transcript + "?" # Add question mark to transcript
                    print(transcript)
                    # Draw the text on the image
                    text = transcript
                    wrapped_text = textwrap.fill(text, width=max_chars, break_long_words=True) # Wrap the text
                    lines = wrapped_text.split('\n') # Split the text into lines
                    for line in lines: # Loop through the lines
                        bbox = draw.textbbox((0, y_text), line, font=font) # Get the bounding box of the text
                        width, height = bbox[2] - bbox[0], bbox[3] - bbox[1] # Calculate the width and height of the text
                        if y_text + height > display.height: # If the text is too long to fit on the display,
                            break
                        draw.text((0, y_text), line, font=font, fill=0) # Draw the text on the image
                        y_text += height # Increment y_text by the height of the text

                    # Display the image on the display
                    display.image(image)
                    display.show()

                # Send request to OpenAI
                print("Sending request to GPT-3.5, waiting for reply...")
                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        { # Kontext
                            "role": "assistant",
                            "content": "Answer the question, Use at most 30 words, and in Swedish.",
                        },
                        { # Question
                            "role": "user",
                            "content": transcript,
                        },
                    ],
                )
                # Extract the text reply part
                reply = completion.choices[0].message.content
                print(reply)

                # Draw a line to separate the question and the response
                y_text +=  font.getbbox(' ')[3]
                draw.line((0, y_text, display.width, y_text), fill=0)

                # Draw the text on the image
                text = reply
                wrapped_text = textwrap.fill(text, width=max_chars, break_long_words=True)
                lines = wrapped_text.split('\n')
                y_text +=  font.getbbox(' ')[3]
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

                set_color(255, 0, 255)  # Set all LEDs to magenta
                
                # Play the audio
                pygame.mixer.init() # Initialize pygame mixer 
                pygame.mixer.music.load("response.mp3") # Load the mp3 file
                pygame.mixer.music.play() # Play the mp3 file
                while pygame.mixer.music.get_busy(): # Wait for the audio to finish playing
                    pygame.time.Clock().tick(10)
                pygame.mixer.quit()  # Close the mixer

                set_color(0, 255, 0)  # Set all LEDs to green

                stream.stop_stream() 
                stream.close()
                py_audio.terminate()

            else:
                print("Mikrofonen uppfate inte vad du sa, kan du säga det igen?")

                # Draw the text on the image
                text = "Mikrofonen uppfate inte vad du sa, kan du säga det igen?"
                wrapped_text = textwrap.fill(text, width=max_chars, break_long_words=True)
                lines = wrapped_text.split('\n')
                y_text += font.getbbox(' ')[3]
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

                stream.stop_stream()
                stream.close()
                py_audio.terminate()

                set_color(0, 255, 0)  # Set all LEDs to green 

        time.sleep(0.1) # Sleep for 0.1 seconds
except Exception as problem:
    handle_error(problem)

# Verbal ChatGPT on RPI and PC

## Setup
This project uses three APIs: [ChatGPT model 3.5](https://platform.openai.com/docs/api-reference/authentication) and Google Cloud's [TTS](https://cloud.google.com/text-to-speech?hl=sv) and [STT](https://cloud.google.com/speech-to-text?hl=sv).
For them to work, they both require keys and that the device is authenticated.
To get keys and authenticate, I recommend following [guide for ChatGPT](https://platform.openai.com/docs/api-reference/authentication) and this [guide for Google](https://learn.adafruit.com/using-google-assistant-on-the-braincraft-hat/google-setup),
the guide for Google Cloud is for Google Assistant; however, in that step, just change it out for TTS and STT.
PS: this project is using a bookworm version of Raspberry Pi OS.

When you have the keys before you can use them, you need to set them as environment variables. For this, there are two options. 
First, you can code them in. For that, just put them in the designated spot in the Raspberry Pi code. I have not yet put that option in the PC code.
The second option is to set them manually as environment variables when you are in a virtual environment. To do that, use this in terminal:
```bash
export GOOGLE_APPLICATION_CREDENTIALS='key.json'
```
However, if you put them in manually, you need to put them in every time you enter the virtual environment.

## Usage
To be able to use the entirety of the code, you need to run it with sudo privileges due to how Neopixel works.
This has the problem of it not being able to find the Python libraries if you installed them in a virtual environment.
To circumvent this, use the following command in the terminal to run the code if you are still in the virtual environment:
```bash
sudo -E env “PATH=$PATH” python3 /CodeAdress.py
```
Alternatively, if you are outside of the virtual environment, run the code with this command:
```bash
sudo -E env "PATH=$PATH" /home/user/env/bin/python3 /CodeAdress.py
```

However, if you want to make it so that the program starts immediately after the Raspberry Pi's startup, I recommend using crontab, which you gain access to by using this command:
```bash
sudo crontab -e
```
Then just put in to make it start on reboot after 30 seconds to give it time to connect to the WiFi:
```bash
@reboot sleep 30 && sudo -E env "PATH=$PATH" /home/user/env/bin/python3 /CodeAdress.py
```
After that, you can ask away. Remember that the APIs have a cost, so you need to have some credit on them. According to my calculation, the cost is around 10,000 questions per $6.

Let me know if you need further assistance or if you have any questions!

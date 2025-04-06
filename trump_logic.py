# FIX ALL DONT USE BEFORE FIX !!!!

# 1. Record/Listen to microphone
from speech_recognition_module import main

# Call the function directly to get the latest sentence
latest_sentence = main()

# 2. Generate response with Trump-style GPT
def get_trump_response(text_input):
    response = send_to_gpt_api(text_input)  # your existing code here
    return response

# 3. Send to TTS (Trump voice)
def generate_trump_voice(response_text):
    speak_with_trump_voice(response_text)  # can be Selenium automation or ElevenLabs/etc.

# 4. Main loop
while True:
    text = listen_and_transcribe()
    print("You said:", text)

    response = get_trump_response(text)
    print("Trump says:", response)

    generate_trump_voice(response)

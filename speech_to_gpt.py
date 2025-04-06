import openai
import os
from dotenv import load_dotenv

import argparse
import numpy as np
import speech_recognition as sr
import whisper
import torch

from datetime import datetime, timedelta
from queue import Queue
from time import sleep
from sys import platform

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import os
import time

# Load API key from .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def listener():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="medium", help="Model to use",
                        choices=["tiny", "base", "small", "medium", "large"])
    parser.add_argument("--non_english", action='store_true',
                        help="Don't use the english model.")
    parser.add_argument("--energy_threshold", default=1000,
                        help="Energy level for mic to detect.", type=int)
    parser.add_argument("--record_timeout", default=10,
                        help="How real time the recording is in seconds.", type=float)
    parser.add_argument("--phrase_timeout", default=5,
                        help="How much empty space between recordings before we "
                             "consider it a new line in the transcription.", type=float)
    if 'linux' in platform:
        parser.add_argument("--default_microphone", default='pulse',
                            help="Default microphone name for SpeechRecognition. "
                                 "Run this with 'list' to view available Microphones.", type=str)
    args = parser.parse_args()

    # The last time a recording was retrieved from the queue.
    phrase_time = None
    # Thread safe Queue for passing data from the threaded recording callback.
    data_queue = Queue()
    # We use SpeechRecognizer to record our audio because it has a nice feature where it can detect when speech ends.
    recorder = sr.Recognizer()
    recorder.energy_threshold = args.energy_threshold
    # Definitely do this, dynamic energy compensation lowers the energy threshold dramatically to a point where the SpeechRecognizer never stops recording.
    recorder.dynamic_energy_threshold = False

    # Important for linux users.
    # Prevents permanent application hang and crash by using the wrong Microphone
    if 'linux' in platform:
        mic_name = args.default_microphone
        if not mic_name or mic_name == 'list':
            print("Available microphone devices are: ")
            for index, name in enumerate(sr.Microphone.list_microphone_names()):
                print(f"Microphone with name \"{name}\" found")
            return
        else:
            for index, name in enumerate(sr.Microphone.list_microphone_names()):
                if mic_name in name:
                    source = sr.Microphone(sample_rate=16000, device_index=index)
                    break
    else:
        source = sr.Microphone(sample_rate=16000)

    # Load / Download model
    model = args.model
    if args.model != "large" and not args.non_english:
        model = model + ".en"
    audio_model = whisper.load_model(model)

    record_timeout = args.record_timeout
    phrase_timeout = args.phrase_timeout

    transcription = ['']

    with source:
        recorder.adjust_for_ambient_noise(source)

    def record_callback(_, audio: sr.AudioData) -> None:
        """
        Threaded callback function to receive audio data when recordings finish.
        audio: An AudioData containing the recorded bytes.
        """
        # Grab the raw bytes and push it into the thread safe queue.
        data = audio.get_raw_data()
        data_queue.put(data)

    # Create a background thread that will pass us raw audio bytes.
    recorder.listen_in_background(source, record_callback, phrase_time_limit=record_timeout)

    # Cue the user that we're ready to go.
    print("💬 Trump is ready. You have the freedom to speak your mind (or 'exit' to stop):")

    while True:
        try:
            now = datetime.utcnow()
            # Pull raw recorded audio from the queue.
            if not data_queue.empty():
                phrase_complete = False
                # If enough time has passed between recordings, consider the phrase complete.
                # Clear the current working audio buffer to start over with the new data.
                if phrase_time and now - phrase_time > timedelta(seconds=phrase_timeout):
                    phrase_complete = True
                # This is the last time we received new audio data from the queue.
                phrase_time = now

                # Combine audio data from queue
                audio_data = b''.join(data_queue.queue)
                data_queue.queue.clear()

                # Convert in-ram buffer to something the model can use directly without needing a temp file.
                audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

                # Read the transcription.
                result = audio_model.transcribe(audio_np, fp16=torch.cuda.is_available())
                text = result['text'].strip().lower()

                # Voice-triggered exit
                exit_commands = [
                    "exit", "quit", "stop", "goodbye trump", "stop talking",
                    "i'm done", "that's enough", "shut up"
                ]
                if text in exit_commands:
                    print("👋 Voice exit detected. Trump is done talking. Goodbye.")
                    break

                # If we detected a pause between recordings, add a new item to our transcription.
                if phrase_complete:
                    transcription.append(text)
                    response = get_trump_response(text)

                    # Timestamp and print both "You" and "Trump" responses
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] You: {text}")
                    print(f"[{timestamp}] Trump: {response}\n")
                    return response
                else:
                    transcription[-1] = text

                # Live transcription display while speaking
                if not phrase_complete:
                    print(f"📝 Listening: {text}", end='\r', flush=True)

            else:
                # Infinite loops are bad for processors, must sleep.
                sleep(0.25)
        except KeyboardInterrupt:
            break


def get_trump_response(user_input):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # or "gpt-3.5-turbo" if you don't have GPT-4 access
        messages=[
            {"role": "system", "content": "You are Donald Trump. Respond in his unique voice, style, and attitude. Be confident, opinionated, and dramatic."},
            {"role": "user", "content": user_input}
        ]
    )
    return response["choices"][0]["message"]["content"]



def website(response):
    # === Setup Chrome ===
    options = Options()
    options.add_experimental_option("detach", True)
    prefs = {"download.default_directory": os.path.join(os.path.expanduser("~"), "Downloads")}
    options.add_experimental_option("prefs", prefs)

    # options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://elontalks.com/")
    driver.set_window_size(3456, 2160)


    # === Select Donald Trump Voice ===
    try:
        image_area = driver.find_element(By.XPATH, "//img[@alt='Donald Trump']")
        image_area.click()
    except:
        print("No Trump image button found.")

    # === Interact with Video (Optional) ===
    try:
        video_element = driver.find_element(By.XPATH, "//video[source[@src='/trump_3.mp4']]")
        video_element.click()
    except:
        print("Default Trump video not found.")

    # === Input Text ===
    text_area = driver.find_element(By.ID, "text")
    text_area.send_keys(response)

    # === Click 'Create Video' ===
    create_video_button = driver.find_element(By.CLASS_NAME, "w-60")
    create_video_button.click()

    # === Wait for Output Video ===
    print("Waiting for output video to appear...")
    time.sleep(17)
    WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.TAG_NAME, "video")))

     # === Click Enlarge (optional - retry loop) ===
    for _ in range(5):
        try:
            pause_button = driver.find_element(By.XPATH, "//button[contains(@class, 'pause')]")
            pause_button.click()
            break
        except:
            time.sleep(1)

    # # === Click Pause (optional - retry loop) ===
    # for _ in range(5):
    #     try:
    #         pause_button = driver.find_element(By.XPATH, "//button[contains(@class, 'pause')]")
    #         pause_button.click()
    #         break
    #     except:
    #         time.sleep(1)

    
    # # === Click 'Download' Link ===
    # try:
    #     download_button = driver.find_element(By.XPATH, "//a[contains(text(), 'Download')]")
    #     download_button.click()
    #     print("Download started.")
    # except:
    #     print("No download button found.")

    # # === Wait and Rename Downloaded File ===
    # download_dir = os.path.join(os.path.expanduser("~"), "Downloads")

    # def get_latest_tmp_file(folder):
    #     latest_file = None
    #     latest_time = 0
    #     for filename in os.listdir(folder):
    #         if filename.endswith(".tmp") or filename.endswith(".mp4"):
    #             full_path = os.path.join(folder, filename)
    #             ctime = os.path.getctime(full_path)
    #             if ctime > latest_time:
    #                 latest_file = full_path
    #                 latest_time = ctime
    #     return latest_file

    # def is_file_stable(file_path, wait_time=10):
    #     try:
    #         size = os.path.getsize(file_path)
    #         time.sleep(wait_time)
    #         return size == os.path.getsize(file_path)
    #     except:
    #         return False

    # print("Waiting for downloaded video to finish...")
    # time.sleep(3)

    # latest_tmp = get_latest_tmp_file(download_dir)
    # final_path = os.path.join(download_dir, "trump_video.mp4")

    # if latest_tmp and is_file_stable(latest_tmp, 10):
    #     if os.path.exists(final_path):
    #         os.remove(final_path)
    #     try:
    #         os.rename(latest_tmp, final_path)
    #         print(f"Downloaded video saved as: {final_path}")
    #     except Exception as e:
    #         print(f"Rename failed: {e}")
    # else:
    #     print("Downloaded file was not found or not stable.")

    # # Close the browser after actions
    # # driver.quit()


# Simple chat loop
if __name__ == "__main__":
    response = listener()
    website(response)

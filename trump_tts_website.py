from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import os
import time

# === Setup Chrome ===
options = Options()
options.add_experimental_option("detach", True)
prefs = {"download.default_directory": os.path.join(os.path.expanduser("~"), "Downloads")}
options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get("https://elontalks.com/")

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
text_area.send_keys("Hello, I am Donald Trump. This is an example sentence.")

# === Click 'Create Video' ===
create_video_button = driver.find_element(By.CLASS_NAME, "w-60")
create_video_button.click()

# === Wait for Output Video ===
print("Waiting for output video to appear...")
time.sleep(17)
WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.TAG_NAME, "video")))

# === Click Pause (optional - retry loop) ===
for _ in range(5):
    try:
        pause_button = driver.find_element(By.XPATH, "//button[contains(@class, 'pause')]")
        pause_button.click()
        break
    except:
        time.sleep(1)

# === Click 'Download' Link ===
try:
    download_button = driver.find_element(By.XPATH, "//a[contains(text(), 'Download')]")
    download_button.click()
    print("Download started.")
except:
    print("No download button found.")

# === Wait and Rename Downloaded File ===
download_dir = os.path.join(os.path.expanduser("~"), "Downloads")

def get_latest_tmp_file(folder):
    latest_file = None
    latest_time = 0
    for filename in os.listdir(folder):
        if filename.endswith(".tmp") or filename.endswith(".mp4"):
            full_path = os.path.join(folder, filename)
            ctime = os.path.getctime(full_path)
            if ctime > latest_time:
                latest_file = full_path
                latest_time = ctime
    return latest_file

def is_file_stable(file_path, wait_time=10):
    try:
        size = os.path.getsize(file_path)
        time.sleep(wait_time)
        return size == os.path.getsize(file_path)
    except:
        return False

print("Waiting for downloaded video to finish...")
time.sleep(3)

latest_tmp = get_latest_tmp_file(download_dir)
final_path = os.path.join(download_dir, "trump_video.mp4")

if latest_tmp and is_file_stable(latest_tmp, 10):
    if os.path.exists(final_path):
        os.remove(final_path)
    try:
        os.rename(latest_tmp, final_path)
        print(f"Downloaded video saved as: {final_path}")
    except Exception as e:
        print(f"Rename failed: {e}")
else:
    print("Downloaded file was not found or not stable.")


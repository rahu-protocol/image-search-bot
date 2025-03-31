import os
import time
from urllib.parse import unquote, urlparse, parse_qs
from datetime import datetime
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# ---------- Chrome Options Helper ----------
def get_chrome_options():
    options = uc.ChromeOptions()
    options.headless = False
    options.add_argument("--window-size=1280,800")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    return options

# ---------- Timestamped Screenshot Helper ----------
def save_debug_artifacts(driver, name_prefix):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    driver.save_screenshot(f"{name_prefix}_{timestamp}.png")
    with open(f"{name_prefix}_{timestamp}.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)

# ---------- Yandex Search ----------
def yandex_reverse_image_search(image_file):
    image_path = os.path.abspath(image_file)
    driver = uc.Chrome(options=get_chrome_options())

    try:
        print("🟡 Opening Yandex...")
        driver.get("https://yandex.com/images/")
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Image search"]'))).click()

        print("🟡 Uploading image...")
        file_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//input[@type="file"]')))
        file_input.send_keys(image_path)
        time.sleep(8)

        print("🟢 Scraping results...")
        results = driver.find_elements(By.XPATH, '//a[contains(@href, "http") and not(contains(@href, "yandex"))]')
        urls = [r.get_attribute("href") for r in results if r.get_attribute("href")]

        save_debug_artifacts(driver, "yandex_debug")
        return urls[:5] if urls else []

    except Exception as e:
        print(f"⚠️ Yandex error: {e}")
        return [f"⚠️ Yandex error: {e}"]

    finally:
        driver.quit()

# ---------- Bing Search ----------
def bing_reverse_image_search(image_file):
    image_path = os.path.abspath(image_file)
    driver = uc.Chrome(options=get_chrome_options())

    try:
        print("🟡 Opening Bing Images...")
        driver.get("https://www.bing.com/images/search")
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "sbi_b"))).click()

        print("🟡 Uploading image...")
        upload_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//input[@type="file"]')))
        upload_input.send_keys(image_path)
        time.sleep(8)

        print("🟢 Scraping results...")
        results = driver.find_elements(By.XPATH, '//a[contains(@href, "mediaurl=")]')

        urls = []
        for r in results:
            href = r.get_attribute("href")
            if href and "mediaurl=" in href:
                parsed = urlparse(href)
                qs = parse_qs(parsed.query)
                media = qs.get("mediaurl", [""])[0]
                if media:
                    urls.append(unquote(media))

        save_debug_artifacts(driver, "bing_debug")
        return urls[:5] if urls else []

    except Exception as e:
        print(f"⚠️ Bing error: {e}")
        return [f"⚠️ Bing error: {e}"]

    finally:
        driver.quit()

# ---------- Google Search ----------
def google_reverse_image_search(image_file):
    image_path = os.path.abspath(image_file)
    driver = uc.Chrome(options=get_chrome_options())

    try:
        print("🟡 Opening Google Images...")
        driver.get("https://images.google.com/")
        wait = WebDriverWait(driver, 15)

        print("🟡 Clicking camera icon...")
        camera_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="Search by image"]')))
        camera_button.click()

        print("🟡 Clicking 'Upload a file' button...")
        upload_span = wait.until(EC.element_to_be_clickable((By.XPATH, '//span[@role="button" and contains(text(), "upload a file")]')))
        upload_span.click()

        print("🟡 Uploading image...")
        file_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@type="file"]')))
        file_input.send_keys(image_path)

        print("🟡 Waiting for results page...")
        time.sleep(8)

        print("🟢 Scraping result links...")
        result_links = driver.find_elements(By.XPATH, '//a[@jsname="UWckNb"]')
        urls = list({a.get_attribute("href") for a in result_links if a.get_attribute("href")})

        save_debug_artifacts(driver, "google_debug")

        if not urls:
            print("⚠️ No direct result links found. Returning fallback URL.")
            return [driver.current_url]

        return urls[:3]

    except TimeoutException:
        print("⚠️ Google search timed out.")
        return ["⚠️ Google timeout."]
    except Exception as e:
        print(f"⚠️ Google error: {e}")
        return [f"⚠️ Google error: {e}"]
    finally:
        driver.quit()

# 🕵️‍♂️ Telegram Reverse Image Bot

A powerful Telegram bot that extracts image metadata and performs automated reverse image searches on **Yandex**, **Bing**, and **Google**. Built for OSINT professionals, researchers, and curious users who want to know *where an image has been online* — and *what it reveals*.

---

## ✨ Features

- 🧠 **EXIF Metadata Extraction** (camera model, GPS, timestamp, etc.)
- 🌍 **GPS Coordinates & Google Maps link** (if available)
- 🧪 **.HEIC Support** (auto-converts to JPEG)
- 🔍 **Reverse Image Search on:**
  - **Yandex**
  - **Bing**
  - **Google Images**
- 📸 Telegram-native interface
- 📁 Supports both photos and uncompressed document images

---

## 📸 Example Output

📍 GPS Location: 51.504106, -0.074575
🌍 View on Map: https://maps.google.com/?q=51.504106,-0.074575
Camera model: Pixel 2
Creation date: 2018-08-22
...

🔍 Reverse Image Search Results

🟣 Yandex: • https://some-yandex-result.com ...

🔵 Bing: • https://some-bing-result.com ...

🔴 Google: • https://some-google-result.com


## 🛠️ Setup Instructions

1. **Clone the repo**
   git clone https://github.com/yourusername/telegram-reverse-image-bot.git
   cd telegram-reverse-image-bot
   
3. Install requirements
pip install -r requirements.txt

3.Add your Telegram Bot Token
Open image_bot.py and replace:
BOT_TOKEN = 'your_bot_token_here'
Or modify the code to load from .env.

4. Run the bot
python image_bot.py

🧪 Requirements
Python 3.8+

Telegram bot token (via @BotFather)

Chrome installed (for undetected-chromedriver to work)

🧰 Tech Stack
python-telegram-bot
undetected-chromedriver
pillow + pillow-heif
hachoir (for deep metadata parsing)
piexif
asyncio, concurrent.futures

⚖️ Disclaimer
This tool is intended for educational and research purposes only.
Respect site terms of service and usage limits. Do not abuse automated search engines.
Use responsibly in accordance with OSINT ethics and applicable laws.

📄 License
MIT License

import logging
import io
import asyncio
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from functools import partial

import pillow_heif
from PIL import Image
import piexif
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes,
)

from image_search import (
    yandex_reverse_image_search,
    bing_reverse_image_search,
    google_reverse_image_search,
)

# Telegram Bot Token
BOT_TOKEN = 'INSERT_TELEGRAM_BOT_KEY'

# Enable Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- GPS Extraction Helper ----------
def extract_gps_info(exif_data):
    try:
        gps_data = exif_data.get("GPS")
        if not gps_data:
            return None

        def convert_to_degrees(value):
            d, m, s = value
            return float(d[0]) / d[1] + float(m[0]) / m[1] / 60 + float(s[0]) / s[1] / 3600

        lat = convert_to_degrees(gps_data[piexif.GPSIFD.GPSLatitude])
        if gps_data[piexif.GPSIFD.GPSLatitudeRef] != b'N':
            lat = -lat

        lon = convert_to_degrees(gps_data[piexif.GPSIFD.GPSLongitude])
        if gps_data[piexif.GPSIFD.GPSLongitudeRef] != b'E':
            lon = -lon

        return (lat, lon)
    except Exception:
        return None

# ---------- Metadata Extraction ----------
def extract_metadata(image_bytes):
    results = []
    temp_file_path = None

    try:
        img = Image.open(io.BytesIO(image_bytes))
        exif_raw = img.info.get('exif')
        if exif_raw:
            exif_data = piexif.load(exif_raw)
            gps_coords = extract_gps_info(exif_data)
            if gps_coords:
                lat, lon = gps_coords
                results.append(f"📍 GPS Location: {lat:.6f}, {lon:.6f}")
                results.append(f"🌍 View on Map: https://maps.google.com/?q={lat:.6f},{lon:.6f}")
    except Exception as e:
        results.append(f"⚠️ piexif error: {e}")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            temp_file.write(image_bytes)
            temp_file_path = temp_file.name

        parser = createParser(temp_file_path)
        if not parser:
            results.append("Unable to parse file with hachoir.")
        else:
            metadata = extractMetadata(parser)
            if metadata:
                results.extend([item.replace("- ", "") for item in metadata.exportPlaintext()])
            else:
                results.append("No metadata found with hachoir.")
    except Exception as e:
        results.append(f"⚠️ hachoir error: {e}")
    finally:
        try:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        except Exception:
            pass

    return "\n".join(results) if results else "No metadata extracted."

# ---------- /start Command ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send me a photo or image file, and I'll extract its metadata and run reverse image search. "
        "If you can send uncompressed the results will be better."
    )

# ---------- Main Image Handler ----------
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Image received.")
    file, filename, mimetype = None, None, None

    # Get image from Telegram
    if update.message.photo:
        logger.info("Photo upload detected.")
        photo = update.message.photo[-1]
        file = await photo.get_file()
        filename = photo.file_unique_id + ".jpg"
        mimetype = "image/jpeg"
    elif update.message.document and update.message.document.mime_type.startswith("image/"):
        logger.info("Document image upload detected.")
        file = await update.message.document.get_file()
        filename = update.message.document.file_name
        mimetype = update.message.document.mime_type
    else:
        await update.message.reply_text("That doesn’t look like an image I can analyze.")
        return

    # Download file
    image_bytes = await file.download_as_bytearray()
    logger.info(f"Received file: {filename}, MIME type: {mimetype}")

    # Convert HEIC to JPEG if needed
    if filename.lower().endswith(".heic") or mimetype == "image/heic":
        await update.message.reply_text(".HEIC file detected. Trying to convert...")
        try:
            heif_file = pillow_heif.read_heif(io.BytesIO(image_bytes))
            img = Image.frombytes(heif_file.mode, heif_file.size, heif_file.data, "raw")
            output = io.BytesIO()
            img.save(output, format="JPEG")
            image_bytes = output.getvalue()
            await update.message.reply_text("Converted HEIC to JPEG.")
        except Exception as e:
            logger.error("HEIC conversion failed:", exc_info=e)
            await update.message.reply_text(f"Failed to convert HEIC: {e}")
            return

    # Save image temporarily
    local_path = os.path.join(tempfile.gettempdir(), filename)
    with open(local_path, "wb") as f:
        f.write(image_bytes)

    # Extract and send metadata
    metadata_text = extract_metadata(image_bytes)
    await update.message.reply_text("Metadata:\n" + metadata_text)

    # Inform user about reverse search
    await update.message.reply_text("Running reverse image search on Yandex, Bing, and Google...")

    # Run reverse image searches in parallel
    def run_searches(path):
        try:
            yandex_links = yandex_reverse_image_search(path)
        except Exception as e:
            yandex_links = [f"Yandex error: {e}"]
        try:
            bing_links = bing_reverse_image_search(path)
        except Exception as e:
            bing_links = [f"Bing error: {e}"]
        try:
            google_links = google_reverse_image_search(path)
        except Exception as e:
            google_links = [f"Google error: {e}"]
        return yandex_links, bing_links, google_links

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        yandex_links, bing_links, google_links = await loop.run_in_executor(pool, partial(run_searches, local_path))

    # Format and send results
    def format_links(name, emoji, links):
        if links:
            safe_links = [link.replace("_", "\\_") for link in links]
            return f"{emoji} *{name}:*\n" + "\n".join(f"• {link}" for link in safe_links) + "\n\n"
        return f"{emoji} *{name}:*\n• No results found.\n\n"

    reply = "🔍 *Reverse Image Search Results*\n\n"
    reply += format_links("Yandex", "🟣", yandex_links)
    reply += format_links("Bing", "🔵", bing_links)
    reply += format_links("Google", "🔴", google_links)

    await update.message.reply_text(reply, parse_mode="Markdown")

# ---------- Bot Entry Point ----------
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_image))
    logger.info("🤖 Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError:
        import nest_asyncio
        nest_asyncio.apply()
        asyncio.get_event_loop().run_until_complete(main())

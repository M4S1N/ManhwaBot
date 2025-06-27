import httpx
from bs4 import BeautifulSoup
from app.core.logger import logger
import re
from io import BytesIO
from PIL import Image
from reportlab.lib.pagesizes import letter
import asyncio

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

async def get_chapter_url(base_url: str, chapter_number: int) -> str:
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(base_url, headers=HEADERS)
            response.raise_for_status()
    except httpx.RequestError as e:
        logger.error(f"Failed to fetch base URL {base_url}: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Search for chapters in <li class="wp-manga-chapter">
    chapter_items = soup.select("li.wp-manga-chapter a")

    for link in chapter_items:
        text = link.text.strip()
        match = re.search(r'cap[ií]tulo[\s#-]*([0-9]+)\b(?!\.\d)', text, re.IGNORECASE)
        if match:
            number = int(match.group(1))
            if number == chapter_number:
                chapter_href = link.get("href")
                logger.debug(f"Match found for chapter {chapter_number}: {chapter_href}")
                return chapter_href

    logger.error(f"Chapter {chapter_number} not found in {base_url}")
    return None


async def get_chapter_images(chapter_url: str) -> list:
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(chapter_url, headers=HEADERS)
        response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract image URLs from the chapter page
    image_tags = soup.select("div.page-break img")
    image_urls = [(img.get("src") or img.get("data-src")).strip() for img in image_tags if img.get("src") or img.get("data-src")]

    return image_urls

async def scrape_chapter_images(base_url: str, chapter_number: int, whit_progress_bar = False, telegram_msg = None) -> list:
    logger.info(f"Searching chapter {chapter_number} in {base_url}")
    chapter_url = await get_chapter_url(base_url, chapter_number)

    if not chapter_url:
        return []
    
    logger.info(f"Chapter URL: {chapter_url}")
    images = await get_chapter_images(chapter_url)

    logger.info(f"Found {len(images)} images in chapter {chapter_number}")
    total = len(images)
    image_data = []
    async with httpx.AsyncClient(follow_redirects=True) as client:
        for idx, url in enumerate(images, start=1):
            try:
                logger.debug(f"Downloading image {idx}: {url}")
                response = await client.get(url)
                response.raise_for_status()
                img_bytes = response.content

                pil = await asyncio.to_thread(Image.open, BytesIO(img_bytes))
                pil = pil.convert("RGB")
                w, h = pil.size
                max_w = int(letter[0])

                if w > max_w:
                    new_h = int(max_w * h / w)
                    pil = await asyncio.to_thread(pil.resize, (max_w, new_h), Image.LANCZOS)
                    pil.size
                buf = BytesIO()

                await asyncio.to_thread(pil.save, buf, "JPEG", quality=90, optimize=True)
                buf.seek(0)
                image_data.append(buf.getvalue())
                buf.close()

                if whit_progress_bar and telegram_msg is not None:
                    progress = int(idx / total * 100)
                    bar = "█" * (progress // 10) + "░" * (10 - (progress // 10))
                    await telegram_msg.edit_text(
                        text=f"⬇️ <b>Descargando contenido...</b>\n[{bar}] {progress}%",
                        parse_mode="HTML"
                    )
            except httpx.RequestError as e:
                logger.error(f"Error downloading image {idx} from {url}: {e}")
    return image_data

# Usage example
if __name__ == "__main__":
    base = "https://taurusmanga.com/manga/subiendo-de-nivel-10-000-anos-en-el-futuro/"
    chapter = 216
    try:
        image_urls = scrape_chapter_images(base, chapter)
        for i, url in enumerate(image_urls, 1):
            print(f"Image {i}: {url}")
    except Exception as e:
        print("Error:", e)

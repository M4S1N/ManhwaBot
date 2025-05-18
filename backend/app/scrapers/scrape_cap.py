import requests
from bs4 import BeautifulSoup
from app.core.logger import logger
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def get_chapter_url(base_url: str, chapter_number: int) -> str:
    try:
        response = requests.get(base_url, headers=HEADERS)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch base URL {base_url}: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Search for chapters in <li class="wp-manga-chapter">
    chapter_items = soup.select("li.wp-manga-chapter a")

    for link in chapter_items:
        text = link.text.strip()
        match = re.search(r'cap[ií]tulo[\s#-]*([0-9]+)', text, re.IGNORECASE)
        if match:
            number = int(match.group(1))
            if number == chapter_number:
                chapter_href = link.get("href")
                logger.debug(f"Match found for chapter {chapter_number}: {chapter_href}")
                return chapter_href

    logger.error(f"Chapter {chapter_number} not found in {base_url}")
    return None


def get_chapter_images(chapter_url: str) -> list:
    response = requests.get(chapter_url, headers=HEADERS)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract image URLs from the chapter page
    image_tags = soup.select("div.page-break img")
    image_urls = [img.get("src") or img.get("data-src") for img in image_tags if img.get("src") or img.get("data-src")]

    return image_urls

def scrape_chapter_images(base_url: str, chapter_number: int) -> list:
    logger.info(f"Searching chapter {chapter_number} in {base_url}")
    chapter_url = get_chapter_url(base_url, chapter_number)

    if not chapter_url:
        return []
    
    logger.info(f"Chapter URL: {chapter_url}")
    images = get_chapter_images(chapter_url)

    logger.info(f"Found {len(images)} images in chapter {chapter_number}")

    image_data = []
    for idx, url in enumerate(images, start=1):
        try:
            logger.debug(f"Downloading image {idx}: {url}")
            response = requests.get(url)
            response.raise_for_status()
            image_data.append(response.content)
        except requests.RequestException as e:
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

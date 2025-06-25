import requests
from bs4 import BeautifulSoup
from app.models.chapter import ChapterModel
import re
import logging
from app.core.logger import logger

def get_chapters_for_comic(comic: ChapterModel) -> list[ChapterModel]:
    logger.info(f"Requesting comic page: {comic.name}")
    response = requests.get(comic.url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    chapters = []
    for link in soup.select("li.wp-manga-chapter a"):
        text = link.text.strip()
        match = re.search(r'cap[ií]tulo[\s#-]*([0-9]+)\b(?!\.\d)', text, re.IGNORECASE)
        if match:
            number = int(match.group(1))
            chapter = ChapterModel(
                name=text,
                number=number,
                url=link.get("href")
            )
            logger.info(f"Chapter found: {chapter.name} (number: {chapter.number}) url: {chapter.url}")
            chapters.append(chapter)
    logger.info(f"Total chapters found: {len(chapters)}")
    return chapters

if __name__ == "__main__":
    test_url = "https://taurusmanga.com/manga/subiendo-de-nivel-10-000-anos-en-el-futuro/"
    chapters = get_chapters_for_comic(test_url)
    for chapter in chapters:
        print(f"{chapter.number}: {chapter.name} -> {chapter.url}")

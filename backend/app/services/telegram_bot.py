from app.models.comic import ComicModel
from app.models.chapter import ChapterModel
from app.scrapers.scrape_comic import get_chapters_for_comic
from app.core.logger import logger
from app.api.routes.file import file as file_endpoint
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import os
from io import BytesIO
from dotenv import load_dotenv
import json
import threading
import asyncio

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
COMICS_ENV = os.getenv("COMICS", "")
CHAPTERS_PER_PAGE = int(os.getenv("CHAPTERS_PER_PAGE", 20))
COLUMN_NUMBER = int(os.getenv("COLUMN_NUMBER", 3))
CHAPTERS_CACHE = {}

def get_comics() -> list[ComicModel]:
    comics = []
    try:
        comics_data = json.loads(COMICS_ENV)
        for entry in comics_data:
            comics.append(ComicModel(name=entry["name"], url=entry["url"]))
        logger.info(f"{len(comics)} comics loaded from COMICS_ENV.")
    except Exception as e:
        logger.error(f"Error parsing COMICS_ENV: {e}")
    return comics

def get_chapters(comic: ComicModel) -> list[ChapterModel]:
    if comic.name in CHAPTERS_CACHE:
        logger.info(f"Chapters for {comic.name} loaded from cache.")
        return CHAPTERS_CACHE[comic.name]
    logger.info(f"Getting chapters for comic: {comic.name}")
    try:
        chapters = get_chapters_for_comic(comic)
        logger.info(f"{len(chapters)} chapters found for {comic.name}")
        CHAPTERS_CACHE[comic.name] = chapters
        return chapters
    except Exception as e:
        logger.error(f"Error getting chapters for {comic.name}: {e}")
        return []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/start command received from {update.effective_user.username}")
    CHAPTERS_CACHE.clear()
    comics = get_comics()
    if not comics:
        logger.warning("No comics available to display.")
        await update.message.reply_text("No comics available.")
        return
    keyboard = [
        [InlineKeyboardButton(comic.name, callback_data=f"comic|{comic.name}")]
        for comic in comics
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "¡Bienvenido! Selecciona un manhwa para ver los capítulos.",
        reply_markup=reply_markup
    )

def paginate_chapters(chapters, page):
    total_pages = (len(chapters) - 1) // CHAPTERS_PER_PAGE
    start = page * CHAPTERS_PER_PAGE
    end = start + CHAPTERS_PER_PAGE
    return chapters[start:end], total_pages

def build_keyboard(page_chapters, comic_name):
    keyboard = []
    row = []
    for idx, chap in enumerate(page_chapters, 1):
        row.append(InlineKeyboardButton(chap.name, callback_data=f"chapter|{comic_name}|{chap.number}"))
        if idx % COLUMN_NUMBER == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return keyboard

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    logger.info(f"Callback received: {data} from {update.effective_user.username}")

    if data.startswith("comic|"):
        comic_name = data.split("|")[1]
        page = 0
        comic = next((c for c in get_comics() if c.name == comic_name), None)
        if not comic:
            logger.warning(f"Comic not found: {comic_name}")
            await query.edit_message_text("Comic not found.")
            return
        
        chapters = sorted(get_chapters(comic), key=lambda c: c.number, reverse=True)
        if not chapters:
            logger.warning(f"No chapters found for comic: {comic.name}")
            await query.edit_message_text("No chapters found for this comic.")
            return
        page_chapters, total_pages = paginate_chapters(chapters, page)
        keyboard = build_keyboard(page_chapters, comic.name)
        nav_buttons = []
        
        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton("Start", callback_data=f"page|{comic.name}|{total_pages}"))
            nav_buttons.append(InlineKeyboardButton("Previous", callback_data=f"page|{comic.name}|{page+1}"))
        
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("Next", callback_data=f"page|{comic.name}|{page-1}"))
            nav_buttons.append(InlineKeyboardButton("End", callback_data=f"page|{comic.name}|0"))
        if nav_buttons:
            keyboard.append(nav_buttons)
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=f"Comic: {comic.name}\nSelect a chapter (Page {page+1}/{total_pages+1}):",
            reply_markup=reply_markup
        )

    elif data.startswith("page|"):
        _, comic_name, page_str = data.split("|")
        page = int(page_str)
        comic = next((c for c in get_comics() if c.name == comic_name), None)
        if not comic:
            logger.warning(f"Comic not found for pagination: {comic_name}")
            await query.edit_message_text("Comic not found.")
            return
        
        chapters = sorted(get_chapters(comic), key=lambda c: c.number, reverse=True)
        page_chapters, total_pages = paginate_chapters(chapters, page)
        keyboard = build_keyboard(page_chapters, comic.name)
        nav_buttons = []
        
        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton("Start", callback_data=f"page|{comic.name}|{total_pages}"))
            nav_buttons.append(InlineKeyboardButton("Previous", callback_data=f"page|{comic.name}|{page+1}"))
        
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("Next", callback_data=f"page|{comic.name}|{page-1}"))
            nav_buttons.append(InlineKeyboardButton("End", callback_data=f"page|{comic.name}|0"))
        if nav_buttons:
            keyboard.append(nav_buttons)
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=f"Comic: {comic.name}\nSelect a chapter (Page {page+1}/{total_pages+1}):",
            reply_markup=reply_markup
        )

    elif data.startswith("chapter|"):
        _, comic_name, chap_number = data.split("|")
        comic = next((c for c in get_comics() if c.name == comic_name), None)
        if not comic:
            logger.warning(f"Comic not found when selecting chapter: {comic_name}")
            await query.edit_message_text("Comic not found.")
            return
        chapters = get_chapters(comic)
        chapter = next((ch for ch in chapters if str(ch.number) == chap_number), None)
        if not chapter:
            logger.warning(f"Chapter not found: {chap_number} in {comic.name}")
            await query.edit_message_text("Chapter not found.")
            return
        try:
            logger.info(f"Requesting PDF: {comic.name} - {chapter.name}")
            response = await file_endpoint(url=comic.url, cap=chapter.number)
            pdf_bytes = b""
            async for chunk in response.body_iterator:
                pdf_bytes += chunk
            pdf_file = BytesIO(pdf_bytes)
            pdf_file.name = f"{comic.name} - {chapter.name}.pdf"
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=pdf_file,
                filename=pdf_file.name,
                caption=f"{comic.name} - {chapter.name}"
            )
            await query.edit_message_text(
                text=f"PDF enviado: {comic.name} - {chapter.name}"
            )
        except Exception as e:
            logger.error(f"Error requesting download: {e}")
            await query.edit_message_text(
                text=f"Error descargando {comic.name} - {chapter.name}."
            )

def start_bot():
    logger.info("Starting Telegram bot...")

    def run():
        asyncio.set_event_loop(asyncio.new_event_loop())
        app = Application.builder().token(TELEGRAM_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CallbackQueryHandler(handle_button))
        app.run_polling(close_loop=False, stop_signals=None)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
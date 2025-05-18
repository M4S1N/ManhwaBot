from fastapi import APIRouter, Query, status, Response
from fastapi.responses import StreamingResponse
from app.core.logger import logger
from app.scrapers.scrape_cap import scrape_chapter_images
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from PIL import Image
import requests

router = APIRouter()

def images_to_pdf_stream(images):
    """
     Ahora `images` ya trae cada imagen redimensionada y comprimida en JPEG
     (bytes) por el scraper.
     """
    buffer = BytesIO()
    c = canvas.Canvas(buffer)

    for img_data in images:
        # img_data ya es JPEG en bytes, lo metemos directo
        reader = ImageReader(BytesIO(img_data))
        w, h = reader.getSize()
        c.setPageSize((w, h))
        c.drawImage(reader, 0, 0, width=w, height=h)

        c.showPage()

        # — Emitir chunk parcial —
        c.saveState()
        buffer.seek(0)
        chunk = buffer.read()
        if chunk:
            yield chunk
        buffer.truncate(0)
        buffer.seek(0)

    # Finaliza PDF completo
    c.save()
    buffer.seek(0)
    remainder = buffer.read()
    if remainder:
        yield remainder


@router.get("/file", status_code=status.HTTP_200_OK)
async def file(
    url: str = Query(..., description="URL to scrape"),
    cap: int = Query(..., description="Chapter number")
):
    logger.info(f"Scraping URL: {url} with cap: {cap}")
    try:
        images = await scrape_chapter_images(url, cap)
        if not images:
            logger.warning(f"No images found for chapter {cap} in {url}")
            return Response("No images found", status_code=status.HTTP_404_NOT_FOUND)

        filename = f"chapter_{cap}.pdf"
        logger.info(f"Streaming PDF with {len(images)} pages")

        return StreamingResponse(
            images_to_pdf_stream(images),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        logger.error(f"Error processing chapter {cap} from {url}: {e}", exc_info=True)
        return Response("Internal server error", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

from fastapi import APIRouter, Query, status, Response
from fastapi.responses import StreamingResponse
from app.core.logger import logger
from app.scrapers.scrape_cap import scrape_chapter_images
from app.services.pdf_builder import images_to_pdf_stream
from reportlab.lib.pagesizes import letter
from PIL import Image
import requests

router = APIRouter()

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

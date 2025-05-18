from fastapi import APIRouter, Query, status, Response
from fastapi.responses import StreamingResponse
from app.core.logger import logger
from app.scrapers.scrape_cap import scrape_chapter_images
from app.services.pdf_builder import build_pdf_from_images
from io import BytesIO

router = APIRouter()


@router.get("/file", status_code=status.HTTP_202_ACCEPTED)
async def file(
    url: str = Query(..., description="URL to scrape"),
    cap: int = Query(..., description="Chapter number")
):
    logger.info(f"Scraping URL: {url} with cap: {cap}")
    try:
        images = scrape_chapter_images(url, cap)
        if not images:
            logger.warning(f"No images found for chapter {cap} in {url}")
            return Response(content="No images found", status_code=status.HTTP_404_NOT_FOUND)
        
        pdf_buffer = build_pdf_from_images(images)

        filename = f"chapter_{cap}.pdf"
        logger.info(f"Returning PDF with {len(images)} pages")

        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        logger.error(f"Error processing chapter {cap} from {url}: {e}")
        return Response(content="Internal server error", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

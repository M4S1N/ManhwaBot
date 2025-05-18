from fastapi import APIRouter, Query, status, Response
from fastapi.responses import StreamingResponse
from app.core.logger import logger
from app.scrapers.scrape_cap import scrape_chapter_images
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import requests

router = APIRouter()

def images_to_pdf_stream(images):
    """
    Generador que crea un PDF donde cada página tiene el ancho fijo de 'letter'
    y ajusta la altura a la proporción de cada imagen.
    """
    page_w, _ = letter  # ancho fijo

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(page_w, letter[1]))  # altura inicial no importa

    for img in images:
        # 1) URL → bytes
        if isinstance(img, str):
            resp = requests.get(img)
            img_data = resp.content
        # 2) bytes/bytearray
        elif isinstance(img, (bytes, bytearray)):
            img_data = img
        # 3) PIL Image u otro → bytes
        else:
            bio = BytesIO()
            img.save(bio, format="PNG")
            img_data = bio.getvalue()

        # crea ImageReader y lee tamaño original
        reader = ImageReader(BytesIO(img_data))
        img_w, img_h = reader.getSize()

        # calculamos altura manteniendo aspect ratio con ancho fijo
        draw_w = page_w
        draw_h = (img_h / img_w) * draw_w

        # ajustamos el tamaño de la página antes de dibujar
        c.setPageSize((page_w, draw_h))

        # dibujamos la imagen ocupando todo el ancho y la altura calculada
        c.drawImage(reader, 0, 0, width=draw_w, height=draw_h)
        c.showPage()

        # emitimos chunk parcial
        c.saveState()
        buffer.seek(0)
        chunk = buffer.read()
        if chunk:
            yield chunk
        buffer.truncate(0)
        buffer.seek(0)

    # finalizamos PDF
    c.save()
    buffer.seek(0)
    remaining = buffer.read()
    if remaining:
        yield remaining


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
            return Response(content="No images found", status_code=status.HTTP_404_NOT_FOUND)

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
        return Response(content="Internal server error", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

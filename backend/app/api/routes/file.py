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

def images_to_pdf_stream(images, jpeg_quality: int = 70, max_width: int = int(letter[0])):
    """
    Generador que crea un PDF donde cada página tiene el ancho fijo de 'letter[0]'
    y ajusta la altura a la proporción de cada imagen,
    redimensionando y comprimiendo a JPEG.
    """
    page_w = max_width

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    for img in images:
        # — Obtener bytes de la imagen —
        if isinstance(img, str):
            resp = requests.get(img, timeout=30)
            resp.raise_for_status()
            img_data = resp.content
        elif isinstance(img, (bytes, bytearray)):
            img_data = img
        else:
            # Ya es PIL.Image
            bio = BytesIO()
            img.save(bio, format="PNG")
            img_data = bio.getvalue()

        # — Abrir con PIL, redimensionar proporcionalmente al ancho máximo —
        pil = Image.open(BytesIO(img_data))
        pil = pil.convert("RGB")  # JPEG sólo RGB
        w, h = pil.size
        if w > page_w:
            new_h = int(page_w * h / w)
            pil = pil.resize((page_w, new_h), Image.LANCZOS)
            w, h = pil.size

        # — Volcar a JPEG comprimido en memoria —
        out = BytesIO()
        pil.save(out, format="JPEG", quality=jpeg_quality, optimize=True)
        jpeg_bytes = out.getvalue()
        out.close()

        # — Insertar en PDF manteniendo proporción —
        reader = ImageReader(BytesIO(jpeg_bytes))
        draw_w = page_w
        draw_h = h * (page_w / w)
        c.setPageSize((draw_w, draw_h))
        c.drawImage(reader, 0, 0, width=draw_w, height=draw_h)
        c.showPage()

        # — Emitir chunk parcial —
        c.saveState()
        buffer.seek(0)
        chunk = buffer.read()
        if chunk:
            yield chunk
        buffer.truncate(0)
        buffer.seek(0)

    # — Finaliza PDF completo —
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
            images_to_pdf_stream(images, jpeg_quality=70, max_width=int(letter[0])),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        logger.error(f"Error processing chapter {cap} from {url}: {e}", exc_info=True)
        return Response("Internal server error", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

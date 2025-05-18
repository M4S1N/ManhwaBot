from fastapi import APIRouter, Query, status, Response, BackgroundTasks
from fastapi.responses import FileResponse
from app.core.logger import logger
from app.scrapers.scrape_cap import scrape_chapter_images
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from PIL import Image
import os
import shutil
import tempfile

router = APIRouter()

@router.get("/file", status_code=status.HTTP_200_OK)
async def file(
    background_tasks: BackgroundTasks,
    url: str = Query(..., description="URL to scrape"),
    cap: int = Query(..., description="Chapter number")
):
    logger.info(f"Scraping URL: {url} with cap: {cap}")
    # Resto del código tal cual…
    try:
        workdir = tempfile.mkdtemp(prefix=f"chap_{cap}_")
        image_paths = await scrape_chapter_images(url, cap, download_dir=workdir)
        if not image_paths:
            shutil.rmtree(workdir)
            return Response("No images found", status_code=status.HTTP_404_NOT_FOUND)

        pdf_path = os.path.join(workdir, f"chapter_{cap}.pdf")
        c = canvas.Canvas(pdf_path, pagesize=letter)
        page_w = int(letter[0])

        for img_path in image_paths:
            pil = Image.open(img_path).convert("RGB")
            w, h = pil.size
            if w > page_w:
                new_h = int(page_w * h / w)
                pil = pil.resize((page_w, new_h), Image.LANCZOS)
                w, h = pil.size

            # Usa un buffer temporal para JPEG
            img_buf = tempfile.SpooledTemporaryFile()
            pil.save(img_buf, format="JPEG", quality=70, optimize=True)
            img_buf.seek(0)
            reader = ImageReader(img_buf)

            draw_w, draw_h = page_w, int(h * (page_w / w))
            c.setPageSize((draw_w, draw_h))
            c.drawImage(reader, 0, 0, width=draw_w, height=draw_h)
            c.showPage()
            img_buf.close()

        c.save()
        logger.info(f"PDF generado en {pdf_path}, tamaño: {os.path.getsize(pdf_path)} bytes")

        background_tasks.add_task(shutil.rmtree, workdir)

        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"chapter_{cap}.pdf"
        )

    except Exception as e:
        shutil.rmtree(workdir, ignore_errors=True)
        logger.error(f"Error processing chapter {cap} from {url}: {e}", exc_info=True)
        return Response("Internal server error", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

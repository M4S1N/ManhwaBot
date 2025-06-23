from PIL import Image
from io import BytesIO
from app.core.logger import logger
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

def build_pdf_from_images(image_data: list[bytes]) -> BytesIO:
    if not image_data:
        raise ValueError("No image data provided")

    images = []
    for idx, data in enumerate(image_data):
        try:
            img = Image.open(BytesIO(data)).convert("RGB")
            images.append(img)
        except Exception as e:
            logger.error(f"Failed to load image {idx + 1}: {e}")
    
    if not images:
        raise ValueError("No valid images to create PDF")

    pdf_buffer = BytesIO()
    try:
        images[0].save(pdf_buffer, format="PDF", save_all=True, append_images=images[1:])
        pdf_buffer.seek(0)
    except Exception as e:
        logger.error(f"Error creating PDF: {e}")
        raise

    return pdf_buffer

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
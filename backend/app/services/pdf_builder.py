from PIL import Image
from io import BytesIO
from app.core.logger import logger

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

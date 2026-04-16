import asyncio
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

from app.services.ocr_service import extract_text

async def main():
    # Generate a dummy image with some text
    img = Image.new('RGB', (200, 100), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((10, 40), "Hello EasyOCR", fill=(0, 0, 0))
    
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_bytes = img_byte_arr.getvalue()
    
    print("Testing EasyOCR extraction...")
    text = await extract_text(img_bytes)
    print(f"Extracted Text: {text}")

if __name__ == "__main__":
    asyncio.run(main())

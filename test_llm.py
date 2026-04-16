import asyncio
import logging
from app.services.llm_service import parse_prescription

logging.basicConfig(level=logging.DEBUG)

async def test():
    text = "Take Amoxicillin 500mg twice daily in the morning and evening"
    try:
        meds = await parse_prescription(text)
        print("SUCCESS:", meds)
    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    asyncio.run(test())

# core/plant_detector.py
from openai import OpenAI
from config import CFG

client = OpenAI(api_key=CFG["openai_api_key"])

async def detect_plant_name(text):
    prompt = f"""
The user says: '{text}'.
Extract only the plant, crop or tree name. 
Return only ONE word (example: apple, potato, tomato, wheat, cotton).
If not found, return NONE.
"""

    rsp = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=10
    )

    plant = rsp.choices[0].message.content.lower().strip()
    return plant

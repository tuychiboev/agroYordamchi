# core/gpt_disease.py
import base64
from openai import OpenAI
from config import CFG

client = OpenAI(api_key=CFG["openai_api_key"])

async def gpt_detect_disease(plant, img_bytes):
    b64 = base64.b64encode(img_bytes).decode()

    prompt = f"""
You are an agronomist. Detect the disease of this plant: {plant}.
Return compact structured info: diagnosis, cause, treatment, prevention.
No extra text.
"""

    rsp = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                ]
            }
        ],
        max_tokens=300
    )

    return rsp.choices[0].message.content.strip()

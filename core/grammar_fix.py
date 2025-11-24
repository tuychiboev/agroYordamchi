# core/grammar_fix.py
from openai import OpenAI
from config import CFG

client = OpenAI(api_key=CFG["openai_api_key"])

async def grammar_fix(text, lang_code):
    prompt = f"""
Fix grammar, improve structure, keep compact.
Language: {lang_code}.
Text:
{text}
"""

    rsp = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200
    )

    return rsp.choices[0].message.content.strip()

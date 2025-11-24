from core.gpt_client import gpt_yes_no

ALLOWED_PROMPT = """
Check if this user message is about farming, agriculture, crops, plants,
diseases, soil, weather, irrigation, fertilizer, pests, agro-tech,
or anything related to agriculture.

Answer only: YES or NO.
"""

async def is_allowed_topic(text: str):
    ans = await gpt_yes_no(ALLOWED_PROMPT + "\nMessage: " + text)
    return ans == "YES"

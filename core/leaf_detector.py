from core.gpt_client import gpt_yes_no

async def is_leaf_image(img_bytes):
    prompt = (
        "Determine if this image contains a plant, leaf, crop, or tree. "
        "Answer only: YES or NO."
    )
    ans = await gpt_yes_no(prompt, img_bytes)
    return ans == "YES"

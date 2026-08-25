"""
Generate images without a local GPU, using Hugging Face's hosted Inference API.
Setup: pip install huggingface_hub, get a free Read token at https://huggingface.co/settings/tokens
Note: FLUX.2-klein-4B is NOT supported for hosted text-to-image as of Aug 2026 (image-to-image only).
Use FLUX.1-schnell or stabilityai/stable-diffusion-3.5-large for the hosted path instead.
"""

import os
from huggingface_hub import InferenceClient

HF_TOKEN = os.environ.get("HF_TOKEN", "PASTE_YOUR_TOKEN_HERE")
MODEL_ID = "black-forest-labs/FLUX.1-schnell"

PROMPT = (
    "A classic 1990s hand-drawn animated jungle film, clean ink outlines, flat cel shading, "
    "warm afternoon sunlight filtering through jungle leaves onto a light beige garden path. "
    "Tinku, a small sleek gray cat with soft fur, pointed ears, sharp green eyes, and a long "
    "graceful tail, sits calmly on warm green grass. Beside him, Monu, a friendly dog with "
    "golden-brown fur, floppy ears, bright loyal eyes, and a wagging tail, digs playfully in "
    "the soil nearby. Both characters fully visible, exploring a garden together surrounded by "
    "jungle plants and foliage. Not photorealistic, not 3D render, no modern digital art style."
)

def main():
    if HF_TOKEN == "PASTE_YOUR_TOKEN_HERE":
        raise SystemExit("Set HF_TOKEN (env var or paste into script) before running.")
    client = InferenceClient(model=MODEL_ID, token=HF_TOKEN)
    image = client.text_to_image(PROMPT)
    image.save("output_hosted.png")
    print("Saved: output_hosted.png")

if __name__ == "__main__":
    main()

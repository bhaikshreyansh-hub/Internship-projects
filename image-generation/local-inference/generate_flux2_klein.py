"""
Generate images using FLUX.2 [klein] 4B (Black Forest Labs) — local model, not hosted API.
Model: https://huggingface.co/black-forest-labs/FLUX.2-klein-4B
License: Apache 2.0. VRAM: ~13GB (fits T4 16GB with cpu offload).
"""

import torch
from diffusers import Flux2KleinPipeline

MODEL_ID = "black-forest-labs/FLUX.2-klein-4B"

PROMPT = (
    "Chiku and Pinku starting their adventure in the garden. Style: Classic 1990s hand-drawn "
    "animated jungle film with clean ink outlines and cel shading. Chiku, the small sleek cat "
    "with soft gray fur. Pointed ears. Sharp green eyes. Long graceful tail. Four agile legs. "
    "Standing on grass. Pinku, the friendly dog with golden brown fur. Floppy ears. Bright loyal "
    "eyes. Wagging tail. Four legs. Running beside Chiku. Both characters visible. Jungle garden "
    "setting with lush green grass and bushes. Afternoon sunlight filtering through leaves. Light "
    "beige ground. The scene shows excitement and adventure."
)

def main():
    pipe = Flux2KleinPipeline.from_pretrained(MODEL_ID, torch_dtype=torch.bfloat16, low_cpu_mem_usage=True)
    pipe.enable_model_cpu_offload()  # T4's usable VRAM is tight relative to klein's footprint

    image = pipe(
        prompt=PROMPT, height=1024, width=1024,
        num_inference_steps=4, guidance_scale=1.0,
        generator=torch.Generator(device="cuda").manual_seed(42),
    ).images[0]

    image.save("output_klein4b.png")
    print("Saved: output_klein4b.png")

if __name__ == "__main__":
    main()

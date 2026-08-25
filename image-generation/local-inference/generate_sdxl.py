"""
Generate images using SDXL 1.0 (Stability AI) — local model with negative prompt support.
Model: https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0
License: CreativeML Open RAIL++-M. VRAM: ~8-12GB.
Add a cel-shading/90s-anime LoRA (uncomment load_lora_weights) for a stronger period style match.
"""

import torch
from diffusers import StableDiffusionXLPipeline, EulerAncestralDiscreteScheduler

MODEL_ID = "stabilityai/stable-diffusion-xl-base-1.0"

PROMPT = (
    "1990s hand-drawn animated film style, clean ink outlines, cel shading, traditional 2D "
    "animation, jungle garden setting, light beige dirt ground, afternoon sunlight through "
    "leaves, dappled light, Tinku the cat, small sleek gray fur, pointed ears, sharp green "
    "eyes, long graceful tail, sitting on green grass, Monu the dog, golden brown fur, floppy "
    "ears, bright loyal eyes, wagging tail, digging in soil, both characters visible, "
    "adventure, exploration, jungle plants, garden foliage, warm color palette, painterly "
    "background, high detail linework"
)
NEGATIVE_PROMPT = (
    "photorealistic, 3D render, CGI, blurry, deformed, extra limbs, extra tails, low detail, "
    "modern digital art, watercolor, sketch, unfinished lines, dark lighting, night scene, "
    "text, watermark, signature"
)

def main():
    pipe = StableDiffusionXLPipeline.from_pretrained(MODEL_ID, torch_dtype=torch.float16, use_safetensors=True)
    pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(pipe.scheduler.config)
    pipe.to("cuda")

    image = pipe(
        prompt=PROMPT, negative_prompt=NEGATIVE_PROMPT,
        height=1024, width=1024, num_inference_steps=30, guidance_scale=7.0,
        generator=torch.Generator(device="cuda").manual_seed(42),
    ).images[0]

    image.save("output_sdxl.png")
    print("Saved: output_sdxl.png")

if __name__ == "__main__":
    main()

# Image Generation Model Testing — Internship Project

Evaluating open-source text-to-image models (alternatives to FLUX.1-dev) for generating
consistent-character children's story illustrations in a 1990s hand-drawn cel-shaded style,
per mentor's request.

## Folder structure

```
image-generation/
├── hosted-api/          # Run without a local GPU, via Hugging Face's Inference API
├── local-inference/      # Run the actual model weights locally (Colab/Kaggle T4 GPU)
├── consistency-tests/    # Multi-scene story generation with fixed-seed consistency testing
└── benchmarks/           # Load time / generation time / VRAM comparisons across precisions
```

## What was tested

**Models:** FLUX.2 [klein] 4B (primary, per mentor's request), FLUX.1-schnell (comparison),
SDXL 1.0 (script provided, not benchmarked in depth).

**Environment:** Local machine had no GPU, so all local-inference and benchmark work runs on
Colab/Kaggle free-tier Tesla T4 (16GB).

## Key findings

- **FLUX.2 klein 4B** is not currently supported for hosted (API) text-to-image — Hugging
  Face's Inference Providers only expose it for image-to-image. It must be run locally to get
  actual klein output.
- **FLUX.1-schnell** needs ~24GB VRAM at full precision — does not fit T4 16GB as-is. Requires
  4-bit (NF4) quantization to run locally on this GPU class.
- **Klein 4B** fits T4 comfortably (~13GB) without quantization, though T4's usable VRAM
  (~14.5 GiB, not the full 16GB nameplate figure) is tight enough that `enable_model_cpu_offload()`
  is used defensively rather than loading fully onto GPU.
- **Character consistency**: plain independent text-to-image calls (even with an identical,
  verbatim-repeated character description and a fixed seed across all scenes in a story) do
  not fully guarantee visual consistency scene to scene. This is expected model behavior, not
  a bug — each generation is independent. Consistency was visibly better on animal characters
  (Chiku's story) than on human characters (Ananya's story), where face shape and skin tone
  showed more drift.
- **Path to better consistency** (not yet implemented, scoped for a possible next step):
  FLUX.2 klein has genuine built-in multi-reference image conditioning per Black Forest Labs'
  documentation — feeding an already-generated scene back in as a reference for the next scene
  is the model's actual intended mechanism for consistency, rather than a prompt-engineering
  workaround.

## How to run

All notebooks are built for Google Colab or Kaggle Notebooks (both provide free T4 GPU access).

1. Upload the `.ipynb` file (Colab: File > Upload notebook; Kaggle: Code > New Notebook >
   File > Import Notebook)
2. Set the GPU accelerator to **T4** before running anything
3. Get a free Hugging Face **Read** token at https://huggingface.co/settings/tokens
4. For gated models (FLUX.1-schnell, and possibly klein depending on account), visit the
   model's Hugging Face page while logged in and accept the license once
5. Run cells top to bottom; the `login()` cell will prompt for the token

## File-by-file notes

| File | Purpose |
|---|---|
| `hosted-api/generate_hosted.py` | No-GPU fallback via HF Inference API. Uses FLUX.1-schnell (klein not supported here). |
| `local-inference/generate_flux2_klein.py` | Standalone script, klein 4B, local weights. |
| `local-inference/generate_sdxl.py` | Standalone script, SDXL 1.0, with LoRA hook for style matching. |
| `local-inference/benchmark_flux2_klein.ipynb` | Klein 4B on T4: load time, generation time, peak VRAM. |
| `local-inference/benchmark_flux1_schnell.ipynb` | Schnell on T4 with NF4 quantization: same metrics. |
| `consistency-tests/consistency_test_template.ipynb` | Runs a full 6-scene story with fixed seed, outputs a comparison grid. Currently set to the Chiku/Pinku story; swap the `scenes` list for Nischay's or Ananya's story to reuse. |
| `benchmarks/klein_precision_sweep.ipynb` | Klein 4B at full precision vs 8-bit vs 4-bit, back to back, with memory cleanup between runs — full trade-off comparison. |

## Known limitations / open items

- Precision sweep's 8-bit/4-bit quantization uses diffusers' `PipelineQuantizationConfig` with
  `components_to_quantize=["transformer"]` — this pattern is documented by diffusers but hasn't
  been independently verified against klein 4B's exact internal component names in a live run.
  If it errors, the component list may need adjusting.
- Reference-image conditioning for stronger character consistency is scoped but not yet built.
- Batch generation (multiple scenes per forward pass) was discussed as the realistic scope for
  "parallel pipelines" on a single T4 — true multi-GPU parallelism isn't available on free-tier
  Colab/Kaggle (one GPU per session).

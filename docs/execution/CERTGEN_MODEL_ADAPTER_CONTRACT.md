# CertGen Model Adapter Contract

The typed interface is `load`, `validate_config`, `generate_smoke`, `generate_batch`, `unload`, and `capabilities`. Capabilities explicitly cover batching, generator lists, class/prompt conditioning, guidance, scheduler/resolution override, mixed precision, CPU/GPU loading, lightweight concurrency, and known limitations.

Validated routes exist for unconditional DDPM, text-to-image diffusion, and class-conditional diffusion. Every call maps `batch_size`, `seeds`, `num_inference_steps`, `scheduler`, `guidance_scale`, `width`, `height`, `prompts`, `class_ids`, `precision`, and `output_type`. The worker records requested configuration, applied configuration, differences, adapter name, pipeline class, and scheduler class; it fails if a claim-relevant field cannot be applied or verified.

CFM/flow-matching remains explicitly unsupported until real loading, batching, generator, scheduler, and sampler semantics are known and preflighted. Repository loadability alone is not adapter validation.

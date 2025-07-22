import os
import base64
from io import BytesIO
from PIL import Image

import torch
from diffusers import (
    StableDiffusionXLPipeline,
    StableDiffusionXLImg2ImgPipeline,
    StableDiffusionXLInpaintPipeline,
    AutoencoderKL,
)
from diffusers.utils import load_image

from diffusers import (
    PNDMScheduler,
    LMSDiscreteScheduler,
    DDIMScheduler,
    EulerDiscreteScheduler,
    DPMSolverMultistepScheduler,
    EulerAncestralDiscreteScheduler,
    DPMSolverSinglestepScheduler,
)

import runpod
from runpod.serverless.utils import rp_upload, rp_cleanup
from runpod.serverless.utils.rp_validator import validate

from schemas import INPUT_SCHEMA

torch.cuda.empty_cache()

def decode_base64_image(data_uri):
    """
    Decodes a base64 image string (data URI) into a PIL Image.
    """
    if "," in data_uri:
        header, encoded = data_uri.split(",", 1)
    else:
        encoded = data_uri
    image_data = base64.b64decode(encoded)
    return Image.open(BytesIO(image_data))

class ModelHandler:
    def __init__(self):
        self.base = None
        self.refiner = None
        self.inpaint = None
        self.load_models()

    def load_base(self):
        vae = AutoencoderKL.from_pretrained(
            "madebyollin/sdxl-vae-fp16-fix",
            torch_dtype=torch.float16,
            local_files_only=True,
        )
        base_pipe = StableDiffusionXLPipeline.from_pretrained(
            "stabilityai/stable-diffusion-xl-base-1.0",
            vae=vae,
            torch_dtype=torch.float16,
            variant="fp16",
            use_safetensors=True,
            add_watermarker=False,
            local_files_only=True,
        ).to("cuda")
        base_pipe.enable_xformers_memory_efficient_attention()
        base_pipe.enable_model_cpu_offload()
        return base_pipe

    def load_refiner(self):
        vae = AutoencoderKL.from_pretrained(
            "madebyollin/sdxl-vae-fp16-fix",
            torch_dtype=torch.float16,
            local_files_only=True,
        )
        refiner_pipe = StableDiffusionXLImg2ImgPipeline.from_pretrained(
            "stabilityai/stable-diffusion-xl-refiner-1.0",
            vae=vae,
            torch_dtype=torch.float16,
            variant="fp16",
            use_safetensors=True,
            add_watermarker=False,
            local_files_only=True,
        ).to("cuda")
        refiner_pipe.enable_xformers_memory_efficient_attention()
        refiner_pipe.enable_model_cpu_offload()
        return refiner_pipe

    def load_inpaint(self):
        vae = AutoencoderKL.from_pretrained(
            "madebyollin/sdxl-vae-fp16-fix",
            torch_dtype=torch.float16,
            local_files_only=True,
        )
        inpaint_pipe = StableDiffusionXLInpaintPipeline.from_pretrained(
            "diffusers/stable-diffusion-xl-1.0-inpainting-0.1",
            vae=vae,
            torch_dtype=torch.float16,
            variant="fp16",
            use_safetensors=True,
            add_watermarker=False,
            local_files_only=True,
        ).to("cuda")
        inpaint_pipe.enable_xformers_memory_efficient_attention()
        inpaint_pipe.enable_model_cpu_offload()
        return inpaint_pipe

    def load_models(self):
        self.base = self.load_base()
        self.refiner = self.load_refiner()
        self.inpaint = self.load_inpaint()

MODELS = ModelHandler()

def _save_and_upload_images(images, job_id):
    os.makedirs(f"/{job_id}", exist_ok=True)
    image_urls = []
    for index, image in enumerate(images):
        image_path = os.path.join(f"/{job_id}", f"{index}.png")
        image.save(image_path)

        if os.environ.get("BUCKET_ENDPOINT_URL", False):
            image_url = rp_upload.upload_image(job_id, image_path)
            image_urls.append(image_url)
        else:
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode("utf-8")
                image_urls.append(f"data:image/png;base64,{image_data}")

    rp_cleanup.clean([f"/{job_id}"])
    return image_urls

def make_scheduler(name, config):
    return {
        "PNDM": PNDMScheduler.from_config(config),
        "KLMS": LMSDiscreteScheduler.from_config(config),
        "DDIM": DDIMScheduler.from_config(config),
        "K_EULER": EulerDiscreteScheduler.from_config(config),
        "K_EULER_ANCESTRAL": EulerAncestralDiscreteScheduler.from_config(config),
        "DPMSolverMultistep": DPMSolverMultistepScheduler.from_config(config),
        "DPMSolverSinglestep": DPMSolverSinglestepScheduler.from_config(config),
    }[name]

@torch.inference_mode()
def generate_image(job):
    """
    Generate an image from text, image, or with inpainting using SDXL
    """
    import json, pprint

    print("[generate_image] RAW job dict:")
    try:
        print(json.dumps(job, indent=2, default=str), flush=True)
    except Exception:
        pprint.pprint(job, depth=4, compact=False)

    job_input = job["input"]

    try:
        validated_input = validate(job_input, INPUT_SCHEMA)
    except Exception as err:
        import traceback
        print("[generate_image] validate(...) raised an exception:", err, flush=True)
        traceback.print_exc()
        raise

    if "errors" in validated_input:
        return {"error": validated_input["errors"]}
    job_input = validated_input["validated_input"]

    # Check if video was requested (temporary message)
    task_type = job_input.get("task_type", "text2img")
    if task_type == "text2video":
        return {
            "error": "Video generation temporarily disabled due to RunPod registry issues. SDXL image generation is available.",
            "info": "Wan2.1-T2V will be re-enabled once RunPod resolves their upload infrastructure."
        }

    starting_image = job_input.get("image_url")
    mask_url = job_input.get("mask_url")

    if job_input["seed"] is None:
        job_input["seed"] = int.from_bytes(os.urandom(2), "big")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    generator = torch.Generator(device).manual_seed(job_input["seed"])

    MODELS.base.scheduler = make_scheduler(
        job_input["scheduler"], MODELS.base.scheduler.config
    )

    output = None

    if starting_image and mask_url:
        print("[generate_image] Mode: Inpainting", flush=True)
        if starting_image.startswith("data:"):
            init_image = decode_base64_image(starting_image).convert("RGB")
        else:
            init_image = load_image(starting_image).convert("RGB")
        if mask_url.startswith("data:"):
            mask_image = decode_base64_image(mask_url).convert("L")
        else:
            mask_image = load_image(mask_url).convert("L")

        try:
            inpaint_result = MODELS.inpaint(
                prompt=job_input["prompt"],
                image=init_image,
                mask_image=mask_image,
                negative_prompt=job_input.get("negative_prompt"),
                height=job_input["height"],
                width=job_input["width"],
                num_inference_steps=job_input["num_inference_steps"],
                guidance_scale=job_input["guidance_scale"],
                num_images_per_prompt=job_input["num_images"],
                generator=generator,
            )
            output = inpaint_result.images
        except Exception as err:
            print(f"[ERROR] Error in inpainting pipeline: {err}", flush=True)
            return {
                "error": f"Inpainting error: {err}",
                "refresh_worker": True,
            }

    elif starting_image:
        print("[generate_image] Mode: Img2Img (Refiner)", flush=True)
        init_image = load_image(starting_image).convert("RGB")
        try:
            refiner_result = MODELS.refiner(
                prompt=job_input["prompt"],
                num_inference_steps=job_input["refiner_inference_steps"],
                strength=job_input["strength"],
                image=init_image,
                generator=generator,
            )
            output = refiner_result.images
        except Exception as err:
            print(f"[ERROR] Error in refiner pipeline: {err}", flush=True)
            return {
                "error": f"Img2Img/refiner error: {err}",
                "refresh_worker": True,
            }

    else:
        print("[generate_image] Mode: Text2Img", flush=True)
        try:
            base_result = MODELS.base(
                prompt=job_input["prompt"],
                negative_prompt=job_input["negative_prompt"],
                height=job_input["height"],
                width=job_input["width"],
                num_inference_steps=job_input["num_inference_steps"],
                guidance_scale=job_input["guidance_scale"],
                denoising_end=job_input["high_noise_frac"],
                output_type="latent",
                num_images_per_prompt=job_input["num_images"],
                generator=generator,
            )
            image = base_result.images

            if hasattr(image, 'dtype') and hasattr(image, 'to'):
                image = image.to(dtype=torch.float16)
            elif isinstance(image, list) and len(image) > 0 and hasattr(image[0], 'dtype'):
                image = [img.to(dtype=torch.float16) for img in image]
            
            refiner_result = MODELS.refiner(
                prompt=job_input["prompt"],
                num_inference_steps=job_input["refiner_inference_steps"],
                strength=job_input["strength"],
                image=image,
                num_images_per_prompt=job_input["num_images"],
                generator=generator,
            )
            output = refiner_result.images
        except Exception as err:
            print(f"[ERROR] Error in generation pipeline: {err}", flush=True)
            return {
                "error": f"Generation error: {err}",
                "refresh_worker": True,
            }

    image_urls = _save_and_upload_images(output, job["id"])

    results = {
        "images": image_urls,
        "image_url": image_urls[0],
        "seed": job_input["seed"],
    }

    if starting_image:
        results["refresh_worker"] = True

    return results

runpod.serverless.start({"handler": generate_image})

import os
import base64

import torch
from diffusers import (
    StableDiffusionXLPipeline,
    StableDiffusionXLImg2ImgPipeline,
    AutoPipelineForInpainting,
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


class ModelHandler:
    def __init__(self):
        self.base = None
        self.refiner = None
        self.inpaint = None            # <-- NEW
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

    def load_inpaint(self):  # <-- NEW
        vae = AutoencoderKL.from_pretrained(
            "madebyollin/sdxl-vae-fp16-fix",
            torch_dtype=torch.float16,
            local_files_only=True,
        )
        inpaint_pipe = AutoPipelineForInpainting.from_pretrained(
            "diffusers/stable-diffusion-xl-1.0-inpainting-0.1",  # <-- CHANGE if you use another inpaint model
            torch_dtype=torch.float16,
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
        self.inpaint = self.load_inpaint()  # <-- NEW


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
    Generate an image from text, image, or with inpainting using your Model
    """
    import json, pprint

    print("[generate_image] RAW job dict:")
    try:
        print(json.dumps(job, indent=2, default=str), flush=True)
    except Exception:
        pprint.pprint(job, depth=4, compact=False)

    job_input = job["input"]

    print("[generate_image] job['input'] payload:")
    try:
        print(json.dumps(job_input, indent=2, default=str), flush=True)
    except Exception:
        pprint.pprint(job_input, depth=4, compact=False)

    try:
        validated_input = validate(job_input, INPUT_SCHEMA)
    except Exception as err:
        import traceback
        print("[generate_image] validate(...) raised an exception:", err, flush=True)
        traceback.print_exc()
        raise

    print("[generate_image] validate(...) returned:")
    try:
        print(json.dumps(validated_input, indent=2, default=str), flush=True)
    except Exception:
        pprint.pprint(validated_input, depth=4, compact=False)

    if "errors" in validated_input:
        return {"error": validated_input["errors"]}
    job_input = validated_input["validated_input"]

    starting_image = job_input.get("image_url")
    mask_url = job_input.get("mask_url")  # <-- NEW

    if job_input["seed"] is None:
        job_input["seed"] = int.from_bytes(os.urandom(2), "big")

    # Create generator with proper device handling
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    generator = torch.Generator(device).manual_seed(job_input["seed"])

    MODELS.base.scheduler = make_scheduler(
        job_input["scheduler"], MODELS.base.scheduler.config
    )

    # ----------- NEW LOGIC: INPAINTING, IMAGE2IMAGE, TEXT2IMAGE -----------
    output = None

    if starting_image and mask_url:
        # ---- INPAINTING ----
        print("[generate_image] Mode: Inpainting", flush=True)
        init_image = load_image(starting_image).convert("RGB")
        mask_image = load_image(mask_url).convert("RGB")

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
        # ---- IMAGE TO IMAGE ----
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
        # ---- TEXT TO IMAGE ----
        print("[generate_image] Mode: Text2Img", flush=True)
        try:
            # Generate latent image using base pipeline
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

            # Debug: Log tensor info
            if hasattr(image, 'dtype'):
                print(f"[DEBUG] Base output dtype: {image.dtype}, shape: {image.shape}", flush=True)
            elif isinstance(image, list) and len(image) > 0:
                print(f"[DEBUG] Base output list, first item dtype: {image[0].dtype}, shape: {image[0].shape}", flush=True)

            # Ensure latent images have correct dtype for refiner
            if hasattr(image, 'dtype') and hasattr(image, 'to'):
                image = image.to(dtype=torch.float16)
            elif isinstance(image, list) and len(image) > 0 and hasattr(image[0], 'dtype'):
                image = [img.to(dtype=torch.float16) for img in image]
            
            # Refine the image
            refiner_result = MODELS.refiner(
                prompt=job_input["prompt"],
                num_inference_steps=job_input["refiner_inference_steps"],
                strength=job_input["strength"],
                image=image,
                num_images_per_prompt=job_input["num_images"],
                generator=generator,
            )
            output = refiner_result.images
        except RuntimeError as err:
            print(f"[ERROR] RuntimeError in generation pipeline: {err}", flush=True)
            return {
                "error": f"RuntimeError: {err}, Stack Trace: {err.__traceback__}",
                "refresh_worker": True,
            }
        except Exception as err:
            print(f"[ERROR] Unexpected error in generation pipeline: {err}", flush=True)
            return {
                "error": f"Unexpected error: {err}",
                "refresh_worker": True,
            }

    image_urls = _save_and_upload_images(output, job["id"])

    results = {
        "images": image_urls,
        "image_url": image_urls[0],
        "seed": job_input["seed"],
    }

    # For consistency: refresh worker if starting_image (img2img/inpaint), as before
    if starting_image:
        results["refresh_worker"] = True

    return results


runpod.serverless.start({"handler": generate_image})
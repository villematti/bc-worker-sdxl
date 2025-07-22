import os
import base64
from io import BytesIO
from PIL import Image

import torch
from diffusers import (
    StableDiffusionXLPipeline,
    StableDiffusionXLImg2ImgPipeline,
    StableDiffusionXLInpaintPipeline,  # Use specific SDXL inpaint pipeline
    AutoencoderKL,
    AutoencoderKLWan,  # For Wan2.1 VAE
    WanPipeline,       # For Wan2.1 T2V
)
from diffusers.utils import load_image, export_to_video

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

# ---- Add this function after your imports ----
def decode_base64_image(data_uri):
    """
    Decodes a base64 image string (data URI) into a PIL Image.
    """

    # Remove the data URL prefix if present
    if "," in data_uri:
        header, encoded = data_uri.split(",", 1)
    else:
        encoded = data_uri
    image_data = base64.b64decode(encoded)
    return Image.open(BytesIO(image_data))
# ---------------------------------------------


class ModelHandler:
    def __init__(self):
        self.base = None
        self.refiner = None
        self.inpaint = None            # <-- SDXL inpaint
        self.wan_t2v = None           # <-- NEW: Wan2.1 T2V
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
        inpaint_pipe = StableDiffusionXLInpaintPipeline.from_pretrained(
            "diffusers/stable-diffusion-xl-1.0-inpainting-0.1",  # <-- CHANGED to SDXL inpainting
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

    def load_wan_t2v(self):  # <-- NEW
        """Load Wan2.1-T2V-14B pipeline optimized for RunPod's 48GB VRAM"""
        print("Loading Wan2.1-T2V-14B pipeline...")
        
        model_id = "Wan-AI/Wan2.1-T2V-14B-Diffusers"
        
        # Load VAE separately for better control
        vae = AutoencoderKLWan.from_pretrained(
            model_id,
            subfolder="vae",
            torch_dtype=torch.float32,  # Keep VAE as float32 for stability
            local_files_only=True,
        )
        
        # Load main pipeline with 14B optimizations
        wan_pipe = WanPipeline.from_pretrained(
            model_id,
            vae=vae,
            torch_dtype=torch.bfloat16,  # Use bfloat16 for 14B model
            use_safetensors=True,
            local_files_only=True,
        ).to("cuda")
        
        # Enable optimizations for 48GB VRAM (less aggressive than 6GB)
        wan_pipe.enable_attention_slicing()
        
        # Enable xformers if available
        try:
            wan_pipe.enable_xformers_memory_efficient_attention()
            print("  ✅ XFormers attention enabled for Wan2.1")
        except:
            print("  ⚠️ XFormers not available for Wan2.1, using default attention")
        
        print("✅ Wan2.1-T2V-14B pipeline loaded successfully!")
        return wan_pipe

    def load_models(self):
        self.base = self.load_base()
        self.refiner = self.load_refiner()
        self.inpaint = self.load_inpaint()  # <-- SDXL inpaint
        self.wan_t2v = self.load_wan_t2v()  # <-- NEW: Wan2.1 T2V


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


def _save_and_upload_video(video_frames, job_id, fps=15):
    """Save and upload video file"""
    os.makedirs(f"/{job_id}", exist_ok=True)
    video_path = os.path.join(f"/{job_id}", "video.mp4")
    
    # Export video using diffusers utility
    export_to_video(video_frames, video_path, fps=fps)
    
    if os.environ.get("BUCKET_ENDPOINT_URL", False):
        # Upload video file
        video_url = rp_upload.upload_file(job_id, video_path)
    else:
        # Return base64 encoded video for local testing
        with open(video_path, "rb") as video_file:
            video_data = base64.b64encode(video_file.read()).decode("utf-8")
            video_url = f"data:video/mp4;base64,{video_data}"
    
    rp_cleanup.clean([f"/{job_id}"])
    return video_url


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

    # ----------- NEW LOGIC: TEXT2VIDEO, INPAINTING, IMAGE2IMAGE, TEXT2IMAGE -----------
    output = None
    
    # Check if this is a text-to-video request
    task_type = job_input.get("task_type", "text2img")
    
    if task_type == "text2video":
        print("[generate_image] Mode: Text-to-Video (Wan2.1-T2V-14B)", flush=True)
        
        try:
            # Video generation parameters
            video_params = {
                "height": job_input.get("video_height", 480),
                "width": job_input.get("video_width", 832),
                "num_frames": job_input.get("num_frames", 81),
                "guidance_scale": job_input.get("video_guidance_scale", 5.0),
            }
            
            # Validate resolution combinations for 14B model
            if video_params["height"] == 720 and video_params["width"] != 1280:
                video_params["width"] = 1280
            elif video_params["height"] == 480 and video_params["width"] != 832:
                video_params["width"] = 832
            
            print(f"  📏 Video size: {video_params['width']}x{video_params['height']}")
            print(f"  🎞️ Frames: {video_params['num_frames']}")
            print(f"  📝 Prompt: {job_input['prompt']}")
            
            # Enhanced negative prompt for video generation
            video_negative_prompt = job_input.get("negative_prompt", "")
            if not video_negative_prompt:
                video_negative_prompt = ("Bright tones, overexposed, static, blurred details, subtitles, style, works, "
                                       "paintings, images, static, overall gray, worst quality, low quality, JPEG compression "
                                       "residue, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn faces, "
                                       "deformed, disfigured, misshapen limbs, fused fingers, still picture, messy background, "
                                       "three legs, many people in the background, walking backwards")
            
            # Generate video using Wan2.1-T2V-14B
            with torch.inference_mode():
                video_result = MODELS.wan_t2v(
                    prompt=job_input["prompt"],
                    negative_prompt=video_negative_prompt,
                    **video_params
                )
                
            # Get video frames
            video_frames = video_result.frames[0]
            
            # Upload video
            fps = job_input.get("fps", 15)
            video_url = _save_and_upload_video(video_frames, job["id"], fps=fps)
            
            print(f"✅ Video generated successfully!")
            print(f"📁 Video URL: {video_url}")
            print(f"🎞️ Video info: {len(video_frames)} frames at {video_params['width']}x{video_params['height']}")
            
            # Return video result
            return {
                "video_url": video_url,
                "video_info": {
                    "frames": len(video_frames),
                    "width": video_params["width"],
                    "height": video_params["height"],
                    "fps": fps,
                    "duration_seconds": len(video_frames) / fps
                },
                "seed": job_input["seed"],
            }
            
        except torch.cuda.OutOfMemoryError as e:
            print(f"❌ CUDA Out of Memory during video generation: {e}")
            return {
                "error": f"Video generation failed - Out of GPU memory: {e}",
                "refresh_worker": True,
            }
        except Exception as e:
            print(f"❌ Error during video generation: {e}")
            import traceback
            traceback.print_exc()
            return {
                "error": f"Video generation error: {e}",
                "refresh_worker": True,
            }

    # Continue with existing image generation logic
    if starting_image and mask_url:
        print("[generate_image] Mode: Inpainting", flush=True)
        # Decode starting image
        if starting_image.startswith("data:"):
            init_image = decode_base64_image(starting_image).convert("RGB")
        else:
            init_image = load_image(starting_image).convert("RGB")
        # Decode mask image
        if mask_url.startswith("data:"):
            mask_image = decode_base64_image(mask_url).convert("L")
        else:
            mask_image = load_image(mask_url).convert("L")
        # ---- INPAINTING ----
        print("[generate_image] Mode: Inpainting", flush=True)

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
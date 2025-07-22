import os
import base64
from io import BytesIO
from PIL import Image
import uuid

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
from cloud_storage import (
    cloud_storage, 
    save_and_upload_images_cloud, 
    save_and_upload_video_cloud
)

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
        """Load Wan2.1-T2V-1.3B pipeline optimized for RunPod's 48GB VRAM"""
        
        # Check if Wan2.1 models are available (using 1.3B model)
        wan_model_path = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"
        try:
            # Try to check if the model directory exists
            from huggingface_hub import repo_exists
            if not repo_exists(wan_model_path):
                print("⚠️ Wan2.1 model not found, skipping video functionality")
                return None
        except:
            pass
            
        try:
            print("Loading Wan2.1-T2V-1.3B pipeline...")
            
            model_id = wan_model_path
            
            # Load VAE separately for better control
            vae = AutoencoderKLWan.from_pretrained(
                model_id,
                subfolder="vae",
                torch_dtype=torch.float32,  # Keep VAE as float32 for stability
                local_files_only=True,
            )
            
            # Load main pipeline with official 1.3B settings
            wan_pipe = WanPipeline.from_pretrained(
                model_id,
                vae=vae,
                torch_dtype=torch.bfloat16,  # Use bfloat16 for 1.3B model
                use_safetensors=True,
                local_files_only=True,
            ).to("cuda")
            
            # Enable optimizations for memory efficiency (following official recommendations)
            wan_pipe.enable_attention_slicing()
            
            # Try to enable model CPU offloading for memory efficiency (like --offload_model True)
            try:
                wan_pipe.enable_model_cpu_offload()
                print("  ✅ Model CPU offloading enabled for memory efficiency")
            except:
                print("  ⚠️ Model CPU offloading not available, using regular CUDA")
            
            # Enable xformers if available
            try:
                wan_pipe.enable_xformers_memory_efficient_attention()
                print("  ✅ XFormers attention enabled for Wan2.1")
            except:
                print("  ⚠️ XFormers not available for Wan2.1, using default attention")
            
            print("✅ Wan2.1-T2V-1.3B pipeline loaded successfully!")
            return wan_pipe
            
        except Exception as e:
            print(f"⚠️ Failed to load Wan2.1 pipeline: {e}")
            print("🔄 Continuing with SDXL-only functionality")
            return None

    def load_models(self):
        # Try to load SDXL models (for image generation)
        try:
            print("Loading SDXL models...")
            self.base = self.load_base()
            self.refiner = self.load_refiner()
            self.inpaint = self.load_inpaint()
            print("✅ SDXL models loaded successfully")
        except Exception as e:
            print(f"⚠️ SDXL models not available: {e}")
            print("🎬 Video-only mode: SDXL image generation will be disabled")
            self.base = None
            self.refiner = None
            self.inpaint = None
        
        # Load Wan2.1 for video generation
        self.wan_t2v = self.load_wan_t2v()


MODELS = ModelHandler()


def _save_and_upload_images(images, job_id, user_id=None, file_uid=None, use_cloud_storage=False):
    """Save and upload images with optional cloud storage"""
    
    # Use cloud storage if enabled and metadata provided
    if use_cloud_storage and user_id and file_uid:
        print(f"📤 Uploading {len(images)} images to cloud storage for user {user_id}")
        try:
            return save_and_upload_images_cloud(images, job_id, user_id, file_uid)
        except Exception as e:
            print(f"⚠️ Cloud storage failed, falling back to base64: {e}")
    
    # Original base64/bucket upload logic (fallback)
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


def _save_and_upload_video(video_frames, job_id, fps=15, user_id=None, file_uid=None, use_cloud_storage=False):
    """Save and upload video with optional cloud storage"""
    
    # Use cloud storage if enabled and metadata provided
    if use_cloud_storage and user_id and file_uid:
        print(f"📤 Uploading video to cloud storage for user {user_id}")
        try:
            return save_and_upload_video_cloud(video_frames, job_id, user_id, file_uid, fps)
        except Exception as e:
            print(f"⚠️ Cloud storage failed, falling back to base64: {e}")
    
    # Original base64 logic (fallback)
    os.makedirs(f"/{job_id}", exist_ok=True)
    video_path = os.path.join(f"/{job_id}", "video.mp4")
    
    # Export video using diffusers utility
    export_to_video(video_frames, video_path, fps=fps)
    
    # Always return base64 encoded video (consistent with images)
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

    # ----------- CLOUD STORAGE AND DATABASE SETUP -----------
    user_id = job_input.get("user_id")
    file_uid = job_input.get("file_uid") 
    use_cloud_storage = job_input.get("use_cloud_storage", False)
    
    # Generate file_uid if not provided but cloud storage is requested
    if use_cloud_storage and not file_uid:
        file_uid = str(uuid.uuid4())
        print(f"🆔 Generated file_uid: {file_uid}")
    
    # Create initial generation request in database
    if use_cloud_storage and user_id and file_uid:
        print(f"📝 Creating generation request for user {user_id}, file {file_uid}")
        cloud_storage.create_generation_request(user_id, file_uid, {
            'task_type': task_type,
            'prompt': job_input.get('prompt', ''),
            'parameters': {k: v for k, v in job_input.items() if k not in ['user_id', 'file_uid']},
            'job_id': job["id"]
        })

    # ----------- NEW LOGIC: TEXT2VIDEO, INPAINTING, IMAGE2IMAGE, TEXT2IMAGE -----------
    output = None
    
    # Check if this is a text-to-video request
    task_type = job_input.get("task_type", "text2img")
    
    if task_type == "text2video":
        # Check if Wan2.1 is available
        if MODELS.wan_t2v is None:
            return {
                "error": "Video generation not available - Wan2.1 model not loaded",
                "info": "Set DOWNLOAD_WAN2_MODEL=true environment variable during build to enable video generation"
            }
            
        print("[generate_image] Mode: Text-to-Video (Wan2.1-T2V-1.3B)", flush=True)
        print(f"[generate_image] Wan2.1 model loaded: {MODELS.wan_t2v is not None}", flush=True)
        print(f"[generate_image] Original request params: num_frames={job_input.get('num_frames')}, guidance={job_input.get('video_guidance_scale')}", flush=True)
        
        try:
            # Video generation parameters - using official 1.3B model defaults
            video_params = {
                "height": job_input.get("video_height", 480),
                "width": job_input.get("video_width", 832),  # Official default for 1.3B
                "num_frames": job_input.get("num_frames", 81),  # Official default for 1.3B
                "guidance_scale": job_input.get("video_guidance_scale", 5.0),  # Official default for 1.3B
            }
            
            # Clamp parameters for 1.3B model compatibility
            if video_params["num_frames"] > 81:  # Max frames for 1.3B model
                print(f"  ⚠️ Reducing frames from {video_params['num_frames']} to 81 for 1.3B model compatibility")
                video_params["num_frames"] = 81
            elif video_params["num_frames"] < 16:
                video_params["num_frames"] = 16
                
            if video_params["guidance_scale"] > 10.0:  # Clamp guidance for 1.3B
                print(f"  ⚠️ Reducing guidance from {video_params['guidance_scale']} to 10.0 for 1.3B model")
                video_params["guidance_scale"] = 10.0
            
            # Validate resolution combinations for 1.3B model
            if video_params["height"] == 720 and video_params["width"] != 1280:
                video_params["width"] = 1280
            elif video_params["height"] == 480 and video_params["width"] not in [832]:
                video_params["width"] = 832  # Official default for 1.3B model
            
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
            
            # Generate video using Wan2.1-T2V-1.3B
            print(f"[generate_image] Final video params: {video_params}", flush=True)
            print(f"[generate_image] Video negative prompt: {video_negative_prompt[:100]}...", flush=True)
            
            with torch.inference_mode():
                print("[generate_image] Starting video generation...", flush=True)
                video_result = MODELS.wan_t2v(
                    prompt=job_input["prompt"],
                    negative_prompt=video_negative_prompt,
                    **video_params
                )
                print("[generate_image] Video generation completed!", flush=True)
                
            # Get video frames
            video_frames = video_result.frames[0]
            
            # Upload video with cloud storage support
            fps = job_input.get("fps", 15)  # Official default for 1.3B model
            video_url = _save_and_upload_video(
                video_frames, 
                job["id"], 
                fps=fps,
                user_id=user_id,
                file_uid=file_uid,
                use_cloud_storage=use_cloud_storage
            )
            
            print(f"✅ Video generated successfully!")
            print(f"📁 Video URL: {video_url}")
            print(f"🎞️ Video info: {len(video_frames)} frames at {video_params['width']}x{video_params['height']}")
            
            # Prepare complete generation data
            generation_data = {
                "videos": [video_url],  # Array format like images
                "video_url": video_url,  # Single video like image_url
                "video_info": {
                    "frames": len(video_frames),
                    "width": video_params["width"],
                    "height": video_params["height"],
                    "fps": fps,
                    "duration_seconds": len(video_frames) / fps
                },
                "seed": job_input["seed"],
                "task_type": "text2video",
                "generation_time": None,  # Could add timing if needed
                "file_uid": file_uid,
                "user_id": user_id
            }
            
            # Update database with completion status
            if use_cloud_storage and user_id and file_uid:
                success = cloud_storage.update_generation_status(user_id, file_uid, generation_data)
                if success:
                    print(f"✅ Database updated for user {user_id}, file {file_uid}")
                else:
                    print(f"⚠️ Failed to update database for user {user_id}, file {file_uid}")
            
            # Return video result
            return generation_data
            
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

    # Upload images with cloud storage support
    image_urls = _save_and_upload_images(
        output, 
        job["id"],
        user_id=user_id,
        file_uid=file_uid, 
        use_cloud_storage=use_cloud_storage
    )

    # Prepare complete generation data
    generation_data = {
        "images": image_urls,
        "image_url": image_urls[0],
        "seed": job_input["seed"],
        "task_type": task_type,
        "generation_time": None,  # Could add timing if needed
        "file_uid": file_uid,
        "user_id": user_id
    }

    # Update database with completion status
    if use_cloud_storage and user_id and file_uid:
        success = cloud_storage.update_generation_status(user_id, file_uid, generation_data)
        if success:
            print(f"✅ Database updated for user {user_id}, file {file_uid}")
        else:
            print(f"⚠️ Failed to update database for user {user_id}, file {file_uid}")

    results = generation_data

    # For consistency: refresh worker if starting_image (img2img/inpaint), as before
    if starting_image:
        results["refresh_worker"] = True

    return results


runpod.serverless.start({"handler": generate_image})
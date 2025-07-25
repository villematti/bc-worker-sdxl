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
        # Load from local RunPod volume (corrected paths)
        local_base_path = "/runpod-volume/sdxl-vae-fp16-fixstable-diffusion-xl-base-1.0"
        local_vae_path = "/runpod-volume/sdxl-vae-fp16-fix"
        
        print(f"📁 Loading SDXL Base from: {local_base_path}")
        print(f"📁 Loading VAE from: {local_vae_path}")
        
        vae = AutoencoderKL.from_pretrained(
            local_vae_path,
            torch_dtype=torch.float16,
            local_files_only=True,
        )
        base_pipe = StableDiffusionXLPipeline.from_pretrained(
            local_base_path,
            vae=vae,
            torch_dtype=torch.float16,
            variant="fp16",
            use_safetensors=True,
            add_watermarker=False,
            local_files_only=True,
        ).to("cuda")
        base_pipe.enable_xformers_memory_efficient_attention()
        base_pipe.enable_model_cpu_offload()
        print("✅ SDXL Base loaded from local storage")
        return base_pipe

    def load_refiner(self):
        # Load from local RunPod volume
        local_refiner_path = "/runpod-volume/stable-diffusion-xl-refiner-1.0"
        local_vae_path = "/runpod-volume/sdxl-vae-fp16-fix"
        
        print(f"📁 Loading SDXL Refiner from: {local_refiner_path}")
        print(f"📁 Loading VAE from: {local_vae_path}")
        
        vae = AutoencoderKL.from_pretrained(
            local_vae_path,
            torch_dtype=torch.float16,
            local_files_only=True,
        )
        refiner_pipe = StableDiffusionXLImg2ImgPipeline.from_pretrained(
            local_refiner_path,
            vae=vae,
            torch_dtype=torch.float16,
            variant="fp16",
            use_safetensors=True,
            add_watermarker=False,
            local_files_only=True,
        ).to("cuda")
        refiner_pipe.enable_xformers_memory_efficient_attention()
        refiner_pipe.enable_model_cpu_offload()
        print("✅ SDXL Refiner loaded from local storage")
        return refiner_pipe

    def load_inpaint(self):  # <-- NEW
        # Load from local RunPod volume
        local_inpaint_path = "/runpod-volume/stable-diffusion-xl-1.0-inpainting-0.1"
        local_vae_path = "/runpod-volume/sdxl-vae-fp16-fix"
        
        print(f"📁 Loading SDXL Inpaint from: {local_inpaint_path}")
        print(f"📁 Loading VAE from: {local_vae_path}")
        
        vae = AutoencoderKL.from_pretrained(
            local_vae_path,
            torch_dtype=torch.float16,
            local_files_only=True,
        )
        inpaint_pipe = StableDiffusionXLInpaintPipeline.from_pretrained(
            local_inpaint_path,
            vae=vae,
            torch_dtype=torch.float16,
            variant="fp16",
            use_safetensors=True,
            add_watermarker=False,
            local_files_only=True,
        ).to("cuda")
        inpaint_pipe.enable_xformers_memory_efficient_attention()
        inpaint_pipe.enable_model_cpu_offload()
        print("✅ SDXL Inpaint loaded from local storage")
        return inpaint_pipe

    def load_wan_t2v(self):  # <-- NEW
        """Load Wan2.1-T2V-14B pipeline optimized for RunPod's 48GB VRAM"""
        
        local_wan_path = "/runpod-volume/Wan2.1-T2V-14B-Diffusers"
        
        try:
            print("Loading Wan2.1-T2V-14B pipeline...")
            print(f"  📁 Local path: {local_wan_path}")
            
            if not os.path.exists(local_wan_path):
                print(f"❌ Local path not found: {local_wan_path}")
                return None
            
            print(f"📁 Found local Wan2.1-14B at: {local_wan_path}")
            
            # Load VAE from local path only
            wan_vae = AutoencoderKLWan.from_pretrained(
                local_wan_path,
                subfolder="vae",
                torch_dtype=torch.float32,
                local_files_only=True,  # Force local loading only
            )
            print("  ✅ VAE loaded successfully")
            
            # Load pipeline from local path only
            wan_t2v = WanPipeline.from_pretrained(
                local_wan_path,
                vae=wan_vae,
                torch_dtype=torch.bfloat16,
                use_safetensors=True,
                local_files_only=True,  # Force local loading only
            ).to("cuda")
            print("  ✅ Main pipeline loaded successfully")
            
            # Enable optimizations for memory efficiency (following official recommendations)
            wan_t2v.enable_attention_slicing()
            print("  ✅ Attention slicing enabled")
            
            # Try to enable model CPU offloading for memory efficiency (like --offload_model True)
            try:
                wan_t2v.enable_model_cpu_offload()
                print("  ✅ Model CPU offloading enabled for memory efficiency")
            except Exception as offload_error:
                print(f"  ⚠️ Model CPU offloading not available: {offload_error}")
            
            # Enable xformers if available
            try:
                wan_t2v.enable_xformers_memory_efficient_attention()
                print("  ✅ XFormers attention enabled for Wan2.1")
            except Exception as xformers_error:
                print(f"  ⚠️ XFormers not available: {xformers_error}")
            
            print("✅ Wan2.1-T2V-14B pipeline loaded successfully!")
            return wan_t2v
            
        except Exception as e:
            print(f"❌ Failed to load Wan2.1-14B pipeline: {e}")
            print(f"   Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
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
            print(f"🔧 [DEBUG] Calling save_and_upload_images_cloud with user_id={user_id}, file_uid={file_uid}")
            result = save_and_upload_images_cloud(images, job_id, user_id, file_uid)
            print(f"✅ [DEBUG] Cloud upload successful: {result}")
            return result
        except Exception as e:
            print(f"❌ [DEBUG] Cloud storage failed with exception: {type(e).__name__}: {e}")
            print(f"⚠️ Cloud storage failed, falling back to base64: {e}")
    else:
        print(f"🔧 [DEBUG] Not using cloud storage: use_cloud_storage={use_cloud_storage}, user_id={user_id}, file_uid={file_uid}")
    
    # Original base64/bucket upload logic (fallback)
    print(f"📱 [DEBUG] Using fallback for images")
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
            print(f"🔧 [DEBUG] Calling save_and_upload_video_cloud with user_id={user_id}, file_uid={file_uid}")
            result = save_and_upload_video_cloud(video_frames, job_id, user_id, file_uid, fps)
            print(f"✅ [DEBUG] Cloud upload successful: {result}")
            return result
        except Exception as e:
            print(f"❌ [DEBUG] Cloud storage failed with exception: {type(e).__name__}: {e}")
            print(f"⚠️ Cloud storage failed, falling back to base64: {e}")
    else:
        print(f"🔧 [DEBUG] Not using cloud storage: use_cloud_storage={use_cloud_storage}, user_id={user_id}, file_uid={file_uid}")
    
    # Original base64 logic (fallback)
    print(f"📱 [DEBUG] Using base64 fallback for video")
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


def test_firebase_debug(job_input):
    """Debug Firebase functionality in RunPod environment"""
    
    print("🔧 [RUNPOD DEBUG] Starting Firebase debug test...")
    
    # Test 1: Environment variables
    print("\n🔧 [TEST 1] Environment Variables:")
    firebase_key = os.environ.get("FIREBASE_SERVICE_ACCOUNT_KEY")
    firebase_bucket = os.environ.get("FIREBASE_STORAGE_BUCKET")
    
    print(f"FIREBASE_SERVICE_ACCOUNT_KEY present: {bool(firebase_key)}")
    print(f"FIREBASE_STORAGE_BUCKET: {firebase_bucket}")
    
    if firebase_key:
        try:
            import json
            key_data = json.loads(firebase_key)
            print(f"✅ JSON key valid, project: {key_data.get('project_id')}")
        except Exception as e:
            print(f"❌ JSON key invalid: {e}")
            return {"error": "Invalid Firebase JSON key"}
    
    # Test 2: Firebase imports and initialization
    print("\n🔧 [TEST 2] Firebase Imports and Initialization:")
    try:
        import firebase_admin
        from firebase_admin import credentials, storage, firestore
        print(f"✅ Firebase admin version: {firebase_admin.__version__}")
    except ImportError as e:
        print(f"❌ Firebase import failed: {e}")
        return {"error": "Firebase admin not available"}
    
    # Test 3: Cloud storage initialization
    print("\n🔧 [TEST 3] Cloud Storage Initialization:")
    try:
        from cloud_storage import cloud_storage
        print(f"✅ Storage type: {cloud_storage.storage_type}")
        print(f"✅ Storage bucket: {type(cloud_storage.storage_bucket)}")
        print(f"✅ Firestore DB: {type(cloud_storage.firestore_db)}")
        
        if cloud_storage.storage_type != "firebase":
            return {"error": f"Expected firebase storage, got: {cloud_storage.storage_type}"}
            
    except Exception as e:
        print(f"❌ Cloud storage init failed: {e}")
        import traceback
        traceback.print_exc()
        return {"error": f"Cloud storage initialization failed: {str(e)}"}
    
    # Test 4: Network connectivity
    print("\n🔧 [TEST 4] Network Connectivity:")
    try:
        import requests
        response = requests.get('https://firebase.googleapis.com', timeout=10)
        print(f"✅ Firebase API reachable: {response.status_code}")
    except Exception as e:
        print(f"❌ Network connectivity issue: {e}")
        return {"error": f"Network connectivity failed: {str(e)}"}
    
    # Test 5: Simple upload test
    print("\n🔧 [TEST 5] Simple Upload Test:")
    try:
        from PIL import Image
        from io import BytesIO
        
        # Create tiny test image
        test_image = Image.new('RGB', (5, 5), color='green')
        img_buffer = BytesIO()
        test_image.save(img_buffer, format='PNG')
        img_bytes = img_buffer.getvalue()
        
        print(f"✅ Created test image: {len(img_bytes)} bytes")
        
        # Try direct upload
        test_url = cloud_storage.upload_file(
            file_data=img_bytes,
            filename="runpod_test.png",
            content_type="image/png",
            user_id="runpod-debug",
            file_uid="debug-test-001"
        )
        
        print(f"✅ Upload successful: {test_url}")
        
        if test_url.startswith("https://"):
            print("✅ Real Firebase URL returned")
            success = True
        else:
            print("⚠️ Fallback URL returned (Firebase upload failed)")
            success = False
            
    except Exception as e:
        print(f"❌ Upload test failed: {e}")
        import traceback
        traceback.print_exc()
        return {"error": f"Upload test failed: {str(e)}"}
    
    # Test 6: Threading test
    print("\n🔧 [TEST 6] Threading Test:")
    import threading
    print(f"✅ Active threads: {threading.active_count()}")
    
    def test_background_task():
        print("✅ Background thread executed successfully")
        
    try:
        thread = threading.Thread(target=test_background_task, daemon=True)
        thread.start()
        thread.join(timeout=5)  # Wait up to 5 seconds
        
        if thread.is_alive():
            print("⚠️ Background thread still running")
        else:
            print("✅ Background thread completed")
            
    except Exception as e:
        print(f"❌ Threading test failed: {e}")
    
    result = {
        "status": "debug_complete",
        "firebase_initialized": cloud_storage.storage_type == "firebase",
        "upload_successful": success,
        "test_url": test_url if 'test_url' in locals() else None,
        "environment_ok": bool(firebase_key and firebase_bucket),
        "message": "Firebase debug test completed - check logs for details"
    }
    
    print(f"\n🔧 [RUNPOD DEBUG] Final result: {result}")
    return result


@torch.inference_mode()
def generate_image(job):
    """
    Async handler: Validate input and return 200 immediately, then process in background
    """
    import json, pprint
    import threading

    print("[generate_image] RAW job dict:")
    try:
        print(json.dumps(job, indent=2, default=str), flush=True)
    except Exception:
        pprint.pprint(job, depth=4, compact=False)

    job_input = job["input"]

    # Check for Firebase debug test
    if job_input.get("test_firebase_debug"):
        return test_firebase_debug(job_input)

    print("[generate_image] job['input'] payload:")
    try:
        print(json.dumps(job_input, indent=2, default=str), flush=True)
    except Exception:
        pprint.pprint(job_input, depth=4, compact=False)

    # Validate input with proper schema selection
    try:
        # Determine task type first
        task_type = job_input.get('task_type', 'text2img')
        
        # Auto-detect task type based on parameters
        if job_input.get('image_url') and job_input.get('mask_url'):
            task_type = 'inpaint'
            print("[generate_image] Auto-detected task type: inpaint (image_url + mask_url)")
        elif job_input.get('image_url') and not job_input.get('mask_url'):
            task_type = 'img2img'
            print("[generate_image] Auto-detected task type: img2img (image_url only)")
        elif job_input.get('num_frames') and job_input.get('num_frames') > 0:
            task_type = 'text2video'
            print("[generate_image] Auto-detected task type: text2video (num_frames specified)")
        else:
            task_type = 'text2img'
            print("[generate_image] Auto-detected task type: text2img (default)")
        
        print(f"[generate_image] Final task type: {task_type}")
        
        # Use the legacy schema for now (but with proper validation)
        validated_input = validate(job_input, INPUT_SCHEMA)
        
    except Exception as err:
        import traceback
        print("[generate_image] validate(...) raised an exception:", err, flush=True)
        traceback.print_exc()
        return {"error": f"Validation failed: {err}", "status": "failed"}

    print("[generate_image] validate(...) returned:")
    try:
        print(json.dumps(validated_input, indent=2, default=str), flush=True)
    except Exception:
        pprint.pprint(validated_input, depth=4, compact=False)

    if "errors" in validated_input:
        return {"error": validated_input["errors"], "status": "failed"}
    
    job_input = validated_input["validated_input"]
    
    # Extract async processing parameters
    user_id = job_input.get("user_id")
    file_uid = job_input.get("file_uid") 
    use_cloud_storage = job_input.get("use_cloud_storage", False)
    
    # Validate required async parameters
    if use_cloud_storage and (not user_id or not file_uid):
        return {
            "error": "user_id and file_uid are required for cloud storage", 
            "status": "failed"
        }
    
    # Update Firestore status to "processing" immediately
    if use_cloud_storage and user_id and file_uid:
        # Import firestore here to avoid circular import issues
        from firebase_admin import firestore
        
        # Determine media type from job input - check for explicit video request
        num_frames = job_input.get("num_frames")
        is_video_request = num_frames is not None and num_frames > 0
        media_type = "videos" if is_video_request else "images"
        
        processing_data = {
            "status": "processing",
            "started_at": firestore.SERVER_TIMESTAMP,
            "task_type": "text2video" if is_video_request else "text2image"
        }
        
        success = cloud_storage.update_generation_status(user_id, file_uid, processing_data, media_type)
        if success:
            print(f"✅ Status updated to 'processing' for {user_id}/{file_uid}")
        else:
            print(f"⚠️ Failed to update status to 'processing'")
    
    # Start background processing thread
    def background_process():
        try:
            print(f"🔄 Starting background processing for {user_id}/{file_uid}")
            _process_generation_task(job, job_input)
        except Exception as e:
            print(f"❌ Background processing failed: {e}")
            import traceback
            traceback.print_exc()
            
            # Update Firestore with comprehensive error status
            if use_cloud_storage and user_id and file_uid:
                num_frames = job_input.get("num_frames")
                is_video_request = num_frames is not None and num_frames > 0
                media_type = "videos" if is_video_request else "images"
                error_data = {
                    "generated": False,
                    "error": True,
                    "status": "failed", 
                    "error_message": str(e),
                    "error_type": type(e).__name__,
                    "failed_at": firestore.SERVER_TIMESTAMP,
                    "modified": firestore.SERVER_TIMESTAMP
                }
                success = cloud_storage.update_generation_status(user_id, file_uid, error_data, media_type)
                if success:
                    print(f"✅ Error status updated in Firestore for {user_id}/{file_uid}")
                else:
                    print(f"❌ Failed to update error status in Firestore for {user_id}/{file_uid}")
            else:
                print("⚠️ Cannot update error status - missing cloud storage parameters")
    
    # Start background thread
    thread = threading.Thread(target=background_process, daemon=True)
    thread.start()
    
    # Return immediately with 200 OK
    return {
        "status": "accepted",
        "message": "Generation task accepted and processing",
        "user_id": user_id,
        "file_uid": file_uid,
        "task_type": "text2video" if job_input.get("num_frames") else "text2image"
    }


def _process_generation_task(job, job_input):
    """
    Background processing function - handles the actual generation
    """
    # Import firestore here to avoid circular import issues
    from firebase_admin import firestore

    starting_image = job_input.get("image_url")
    mask_url = job_input.get("mask_url")

    if job_input["seed"] is None:
        job_input["seed"] = int.from_bytes(os.urandom(2), "big")

    # Create generator with proper device handling
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    generator = torch.Generator(device).manual_seed(job_input["seed"])

    MODELS.base.scheduler = make_scheduler(
        job_input["scheduler"], MODELS.base.scheduler.config
    )

    # Extract cloud storage parameters
    user_id = job_input.get("user_id")
    file_uid = job_input.get("file_uid")
    use_cloud_storage = job_input.get("use_cloud_storage", False)
    
    # Determine task type properly - NO MORE GUESSING!
    task_type = job_input.get('task_type', 'text2img')
    
    # Auto-detect task type based on parameters (override if needed)
    if job_input.get('image_url') and job_input.get('mask_url'):
        task_type = 'inpaint'
    elif job_input.get('image_url') and not job_input.get('mask_url'):
        task_type = 'img2img'
    elif job_input.get('num_frames') and job_input.get('num_frames') > 0:
        task_type = 'text2video'
    else:
        task_type = 'text2img'
    
    print(f"[Background] FINAL TASK TYPE: {task_type}")
    
    # Validate parameters for the specific task type
    if task_type == 'text2video':
        # Video generation - validate video parameters
        if not job_input.get('num_frames'):
            raise ValueError("num_frames is required for video generation")
        print(f"[Background] Video parameters: {job_input.get('num_frames')} frames, {job_input.get('video_width', 832)}x{job_input.get('video_height', 480)}")
    else:
        # Image generation - validate no video parameters are present
        video_params = ['num_frames', 'video_height', 'video_width', 'video_guidance_scale', 'fps']
        present_video_params = [p for p in video_params if job_input.get(p) is not None]
        if present_video_params:
            raise ValueError(f"Video parameters {present_video_params} not allowed for {task_type} requests")
        print(f"[Background] Image parameters: {job_input.get('width', 1024)}x{job_input.get('height', 1024)}")

    # Route to appropriate pipeline
    if task_type == 'text2video':  # Video generation
        print("[Background] Mode: Text-to-Video (Wan2.1-T2V-1.3B)", flush=True)
        
        # Check if Wan2.1 is available
        if MODELS.wan_t2v is None:
            error_msg = "Video generation not available - Wan2.1 model not loaded"
            print(f"❌ {error_msg}")
            
            # Update Firestore with comprehensive error
            if use_cloud_storage and user_id and file_uid:
                error_data = {
                    "generated": False,
                    "error": True,
                    "status": "failed",
                    "error_message": error_msg,
                    "error_type": "ModelNotAvailable",
                    "failed_at": firestore.SERVER_TIMESTAMP,
                    "modified": firestore.SERVER_TIMESTAMP
                }
                cloud_storage.update_generation_status(user_id, file_uid, error_data, "videos")
            return
            
        try:
            # Video generation parameters
            video_params = {
                "height": job_input.get("video_height", 480),
                "width": job_input.get("video_width", 832),
                "num_frames": job_input.get("num_frames", 81),
                "guidance_scale": job_input.get("video_guidance_scale", 5.0),
            }
            
            # Clamp parameters for 1.3B model compatibility
            if video_params["num_frames"] > 81:
                video_params["num_frames"] = 81
            elif video_params["num_frames"] < 16:
                video_params["num_frames"] = 16
                
            if video_params["guidance_scale"] > 10.0:
                video_params["guidance_scale"] = 10.0
            
            # Enhanced negative prompt for video generation
            video_negative_prompt = job_input.get("negative_prompt", "")
            if not video_negative_prompt:
                video_negative_prompt = ("Bright tones, overexposed, static, blurred details, subtitles, style, works, "
                                       "paintings, images, static, overall gray, worst quality, low quality, JPEG compression "
                                       "residue, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn faces, "
                                       "deformed, disfigured, misshapen limbs, fused fingers, still picture, messy background, "
                                       "three legs, many people in the background, walking backwards")
            
            print(f"[Background] Starting video generation with params: {video_params}")
            
            with torch.inference_mode():
                video_result = MODELS.wan_t2v(
                    prompt=job_input["prompt"],
                    negative_prompt=video_negative_prompt,
                    **video_params
                )
                
            # Get video frames
            video_frames = video_result.frames[0]
            
            # Upload video with cloud storage support
            fps = job_input.get("fps", 15)
            video_url = _save_and_upload_video(
                video_frames, 
                job["id"], 
                fps=fps,
                user_id=user_id,
                file_uid=file_uid,
                use_cloud_storage=use_cloud_storage
            )
            
            print(f"✅ Video generated successfully: {video_url}")
            
            # Prepare complete generation data for Firestore
            generation_data = {
                "generated": True,
                "error": False,
                "videos": [video_url],
                "video_url": video_url,
                "video_info": {
                    "frames": len(video_frames),
                    "width": video_params["width"],
                    "height": video_params["height"],
                    "fps": fps,
                    "duration_seconds": len(video_frames) / fps
                },
                "seed": job_input["seed"],
                "task_type": "text2video",
                "status": "completed",
                "completed_at": firestore.SERVER_TIMESTAMP,
                "modified": firestore.SERVER_TIMESTAMP,
                "file_uid": file_uid,
                "user_id": user_id
            }
            
            # Update database with completion status
            if use_cloud_storage and user_id and file_uid:
                success = cloud_storage.update_generation_status(user_id, file_uid, generation_data, "videos")
                if success:
                    print(f"✅ Database updated for user {user_id}, file {file_uid}")
                else:
                    print(f"⚠️ Failed to update database for user {user_id}, file {file_uid}")
            
            return  # Video processing complete
            
        except torch.cuda.OutOfMemoryError as e:
            error_msg = f"CUDA Out of Memory during video generation: {e}"
            print(f"❌ {error_msg}")
            
            if use_cloud_storage and user_id and file_uid:
                error_data = {
                    "generated": False,
                    "error": True,
                    "status": "failed",
                    "error_message": error_msg,
                    "error_type": "OutOfMemoryError",
                    "failed_at": firestore.SERVER_TIMESTAMP,
                    "modified": firestore.SERVER_TIMESTAMP
                }
                cloud_storage.update_generation_status(user_id, file_uid, error_data, "videos")
            return
            
        except Exception as e:
            error_msg = f"Error during video generation: {e}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            
            if use_cloud_storage and user_id and file_uid:
                error_data = {
                    "generated": False,
                    "error": True,
                    "status": "failed",
                    "error_message": error_msg,
                    "error_type": type(e).__name__,
                    "failed_at": firestore.SERVER_TIMESTAMP,
                    "modified": firestore.SERVER_TIMESTAMP
                }
                cloud_storage.update_generation_status(user_id, file_uid, error_data, "videos")
            return

    # Continue with image generation logic (SDXL pipelines)
    print(f"[Background] Mode: {task_type.upper()} (SDXL)", flush=True)
    
    try:
        output = None
        
        if task_type == 'inpaint':
            print("[Background] Pipeline: SDXL Inpaint", flush=True)
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

            inpaint_result = MODELS.inpaint(
                prompt=job_input["prompt"],
                image=init_image,
                mask_image=mask_image,
                negative_prompt=job_input.get("negative_prompt"),
                height=job_input["height"],
                width=job_input["width"],
                num_inference_steps=job_input["num_inference_steps"],
                guidance_scale=job_input["guidance_scale"],
                generator=generator,
            )
            output = inpaint_result.images

        elif task_type == 'img2img':
            print("[Background] Pipeline: SDXL Refiner (Img2Img)", flush=True)
            init_image = load_image(starting_image).convert("RGB")
            
            refiner_result = MODELS.refiner(
                prompt=job_input["prompt"],
                num_inference_steps=job_input["refiner_inference_steps"],
                strength=job_input["strength"],
                image=init_image,
                generator=generator,
            )
            output = refiner_result.images

        else:  # task_type == 'text2img'
            print("[Background] Pipeline: SDXL Base + Refiner (Text2Img)", flush=True)
            
            # Generate latent image using base pipeline
            base_result = MODELS.base(
                prompt=job_input["prompt"],
                negative_prompt=job_input.get("negative_prompt"),
                height=job_input["height"],
                width=job_input["width"],
                num_inference_steps=job_input["num_inference_steps"],
                guidance_scale=job_input["guidance_scale"],
                denoising_end=job_input["high_noise_frac"],
                output_type="latent",
                generator=generator,
            )
            image = base_result.images

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
                generator=generator,
            )
            output = refiner_result.images

        # Upload images with cloud storage support
        image_urls = _save_and_upload_images(
            output, 
            job["id"],
            user_id=user_id,
            file_uid=file_uid, 
            use_cloud_storage=use_cloud_storage
        )

        # Prepare complete generation data for Firestore
        generation_data = {
            "generated": True,
            "error": False,
            "images": image_urls,
            "image_url": image_urls[0],
            "seed": job_input["seed"],
            "task_type": task_type,
            "status": "completed",
            "completed_at": firestore.SERVER_TIMESTAMP,
            "modified": firestore.SERVER_TIMESTAMP,
            "file_uid": file_uid,
            "user_id": user_id
        }

        # Update database with completion status
        if use_cloud_storage and user_id and file_uid:
            success = cloud_storage.update_generation_status(user_id, file_uid, generation_data, "images")
            if success:
                print(f"✅ Database updated for user {user_id}, file {file_uid}")
            else:
                print(f"⚠️ Failed to update database for user {user_id}, file {file_uid}")

        print(f"✅ Image generation completed: {len(image_urls)} images")

    except torch.cuda.OutOfMemoryError as e:
        error_msg = f"CUDA Out of Memory during image generation: {e}"
        print(f"❌ {error_msg}")
        
        if use_cloud_storage and user_id and file_uid:
            error_data = {
                "generated": False,
                "error": True,
                "status": "failed",
                "error_message": error_msg,
                "error_type": "OutOfMemoryError",
                "failed_at": firestore.SERVER_TIMESTAMP,
                "modified": firestore.SERVER_TIMESTAMP
            }
            cloud_storage.update_generation_status(user_id, file_uid, error_data, "images")
            
    except Exception as e:
        error_msg = f"Error during image generation: {e}"
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        
        if use_cloud_storage and user_id and file_uid:
            error_data = {
                "generated": False,
                "error": True,
                "status": "failed",
                "error_message": error_msg,
                "error_type": type(e).__name__,
                "failed_at": firestore.SERVER_TIMESTAMP,
                "modified": firestore.SERVER_TIMESTAMP
            }
            cloud_storage.update_generation_status(user_id, file_uid, error_data, "images")


# Helper functions (keep existing implementations)
def make_scheduler(name, config):
    """Create scheduler from name and config"""
    return {
        "PNDM": PNDMScheduler.from_config(config),
        "KLMS": LMSDiscreteScheduler.from_config(config),
        "DDIM": DDIMScheduler.from_config(config),
        "K_EULER": EulerDiscreteScheduler.from_config(config),
        "DPMSolverMultistep": DPMSolverMultistepScheduler.from_config(config),
        "K_EULER_ANCESTRAL": EulerAncestralDiscreteScheduler.from_config(config),
        "DPMSolverSinglestep": DPMSolverSinglestepScheduler.from_config(config),
    }[name]


# Keep the existing _save_and_upload_images and _save_and_upload_video functions...

runpod.serverless.start({"handler": generate_image})
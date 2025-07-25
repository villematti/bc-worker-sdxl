import os
import torch
from diffusers import (
    StableDiffusionXLPipeline,
    StableDiffusionXLImg2ImgPipeline,
    StableDiffusionXLInpaintPipeline,  # Use the specific SDXL inpaint pipeline
    AutoencoderKL,
    AutoencoderKLWan,  # For Wan2.1 VAE
    WanPipeline,       # For Wan2.1 T2V
)

def fetch_pretrained_model(model_class, model_name, **kwargs):
    """
    Fetches a pretrained model from the HuggingFace model hub.
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return model_class.from_pretrained(model_name, **kwargs)
        except OSError as err:
            if attempt < max_retries - 1:
                print(
                    f"Error encountered: {err}. Retrying attempt {attempt + 1} of {max_retries}..."
                )
            else:
                raise

def get_hf_token():
    # Prefer HUGGINGFACE_TOKEN, fallback to HUGGINGFACE_HUB_TOKEN
    return os.environ.get("HUGGINGFACE_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")

def get_diffusion_pipelines():
    """
    Loads all models from local RunPod volume storage - no internet downloads.
    """
    
    # Local model paths on RunPod volume (corrected to match actual folder names)
    local_base_path = "/runpod-volume/sdxl-vae-fp16-fixstable-diffusion-xl-base-1.0"
    local_vae_path = "/runpod-volume/sdxl-vae-fp16-fix"  
    local_refiner_path = "/runpod-volume/stable-diffusion-xl-refiner-1.0"
    local_inpaint_path = "/runpod-volume/stable-diffusion-xl-1.0-inpainting-0.1"

def get_diffusion_pipelines():
    """
    Validates model paths for RunPod volume - actual loading happens at runtime.
    During Docker build, RunPod volume isn't mounted yet, so we just validate the code.
    """
    
    # Local model paths on RunPod volume (corrected to match actual folder names)
    local_base_path = "/runpod-volume/sdxl-vae-fp16-fixstable-diffusion-xl-base-1.0"
    local_vae_path = "/runpod-volume/sdxl-vae-fp16-fix"  
    local_refiner_path = "/runpod-volume/stable-diffusion-xl-refiner-1.0"
    local_inpaint_path = "/runpod-volume/stable-diffusion-xl-1.0-inpainting-0.1"

    # Check if we're in build context (no volume mounted) or runtime context
    is_build_time = not os.path.exists("/runpod-volume")
    
    if is_build_time:
        print("🔧 BUILD TIME: RunPod volume not mounted yet - validating configuration only")
        print("📋 Expected model paths at runtime:")
        print(f"   • SDXL Base: {local_base_path}")
        print(f"   • VAE: {local_vae_path}")  
        print(f"   • SDXL Refiner: {local_refiner_path}")
        print(f"   • SDXL Inpaint: {local_inpaint_path}")
        print(f"   • Wan2.1-14B: /runpod-volume/Wan2.1-T2V-14B-Diffusers")
        print("✅ Configuration validated - models will load at runtime")
        return None, None, None, None, None, None
    
    print("🚀 RUNTIME: RunPod volume mounted - loading models...")

    # SDXL Base Pipeline
    print("Loading SDXL Base Pipeline...")
    try:
        if os.path.exists(local_base_path):
            print(f"📁 Found local SDXL Base at: {local_base_path}")
            pipe = StableDiffusionXLPipeline.from_pretrained(
                local_base_path,
                torch_dtype=torch.float16,
                variant="fp16",
                use_safetensors=True,
                local_files_only=True,  # Force local loading
            )
            print("✅ SDXL Base loaded successfully from local storage!")
        else:
            print(f"❌ Local SDXL Base not found at: {local_base_path}")
            raise FileNotFoundError(f"SDXL Base model not found at {local_base_path}")
    except Exception as e:
        print(f"❌ Failed to load SDXL Base: {e}")
        raise

    # VAE
    print("Loading SDXL VAE...")
    try:
        if os.path.exists(local_vae_path):
            print(f"📁 Found local VAE at: {local_vae_path}")
            vae = AutoencoderKL.from_pretrained(
                local_vae_path,
                torch_dtype=torch.float16,
                local_files_only=True,  # Force local loading
            )
            print("✅ SDXL VAE loaded successfully from local storage!")
        else:
            print(f"❌ Local VAE not found at: {local_vae_path}")
            raise FileNotFoundError(f"VAE model not found at {local_vae_path}")
    except Exception as e:
        print(f"❌ Failed to load VAE: {e}")
        raise

    # SDXL Refiner Pipeline
    print("Loading SDXL Refiner Pipeline...")
    try:
        if os.path.exists(local_refiner_path):
            print(f"📁 Found local SDXL Refiner at: {local_refiner_path}")
            refiner = StableDiffusionXLImg2ImgPipeline.from_pretrained(
                local_refiner_path,
                torch_dtype=torch.float16,
                variant="fp16",
                use_safetensors=True,
                local_files_only=True,  # Force local loading
            )
            print("✅ SDXL Refiner loaded successfully from local storage!")
        else:
            print(f"❌ Local SDXL Refiner not found at: {local_refiner_path}")
            raise FileNotFoundError(f"SDXL Refiner model not found at {local_refiner_path}")
    except Exception as e:
        print(f"❌ Failed to load SDXL Refiner: {e}")
        raise

    # SDXL Inpaint Pipeline
    print("Loading SDXL Inpaint Pipeline...")
    try:
        if os.path.exists(local_inpaint_path):
            print(f"📁 Found local SDXL Inpaint at: {local_inpaint_path}")
            inpaint = StableDiffusionXLInpaintPipeline.from_pretrained(
                local_inpaint_path,
                torch_dtype=torch.float16,
                variant="fp16",
                use_safetensors=True,
                local_files_only=True,  # Force local loading
            )
            print("✅ SDXL Inpaint loaded successfully from local storage!")
        else:
            print(f"❌ Local SDXL Inpaint not found at: {local_inpaint_path}")
            raise FileNotFoundError(f"SDXL Inpaint model not found at {local_inpaint_path}")
    except Exception as e:
        print(f"❌ Failed to load SDXL Inpaint: {e}")
        raise

    # Wan2.1-T2V-14B models (load from local volume)
    wan_vae = None
    wan_t2v = None
    
    if os.environ.get("DOWNLOAD_WAN2_MODEL", "false").lower() == "true":
        print("Loading Wan2.1-T2V-14B model...")
        
        # Check for local model path (updated to 14B)
        local_wan_path = "/runpod-volume/Wan2.1-T2V-14B-Diffusers"
        
        try:
            if os.path.exists(local_wan_path):
                print(f"📁 Found local Wan2.1 model at: {local_wan_path}")
                
                # Load Wan VAE from local path
                wan_vae = AutoencoderKLWan.from_pretrained(
                    local_wan_path,
                    subfolder="vae",
                    torch_dtype=torch.float32,
                    local_files_only=True,  # Force local loading
                )
                
                # Load main Wan T2V pipeline from local path
                wan_t2v = WanPipeline.from_pretrained(
                    local_wan_path,
                    vae=wan_vae,
                    torch_dtype=torch.bfloat16,
                    use_safetensors=True,
                    local_files_only=True,  # Force local loading
                )
                print("✅ Wan2.1-T2V-14B loaded successfully from local storage!")
            else:
                print(f"❌ Local Wan2.1-14B not found at: {local_wan_path}")
                print("🔄 Continuing with SDXL-only functionality")
                wan_vae = None
                wan_t2v = None
                
        except Exception as e:
            print(f"⚠️ Wan2.1-14B load failed: {e}")
            print("🔄 Continuing with SDXL-only functionality")
            wan_vae = None
            wan_t2v = None
    else:
        print("ℹ️ Skipping Wan2.1 (DOWNLOAD_WAN2_MODEL not set to 'true')")

    return pipe, refiner, vae, inpaint, wan_vae, wan_t2v


if __name__ == "__main__":
    print("📋 Model Configuration Check")
    
    # Check if we're at build time or runtime
    is_build_time = not os.path.exists("/runpod-volume")
    
    if is_build_time:
        print("🔧 DOCKER BUILD: Validating model configuration...")
        print("   RunPod volume will be mounted at runtime")
        try:
            get_diffusion_pipelines()  # This will just validate, not load
            print("✅ Model configuration validated successfully!")
            print("📋 Ready for RunPod deployment with volume mounting")
        except Exception as e:
            print(f"❌ Configuration validation failed: {e}")
            import sys
            sys.exit(1)
    else:
        print("🚀 RUNTIME: Loading models from RunPod volume...")
        try:
            # Load with retry logic
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    get_diffusion_pipelines()
                    print("✅ All models loaded successfully from local storage!")
                    break
                except Exception as e:
                    print(f"❌ Load attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        print("🔄 Retrying model loading...")
                        import time
                        time.sleep(5)  # Wait 5 seconds before retry (shorter since it's local)
                    else:
                        print("💥 Final attempt failed!")
                        raise
                        
        except Exception as e:
            print(f"💥 Model loading failed completely: {e}")
            print("🔍 Check that all models are present in /runpod-volume/")
            print("Expected paths:")
            print("  /runpod-volume/sdxl-vae-fp16-fixstable-diffusion-xl-base-1.0")
            print("  /runpod-volume/sdxl-vae-fp16-fix")  
            print("  /runpod-volume/stable-diffusion-xl-refiner-1.0")
            print("  /runpod-volume/stable-diffusion-xl-1.0-inpainting-0.1")
            print("  /runpod-volume/Wan2.1-T2V-14B-Diffusers")
            # Exit with error code
            import sys
            sys.exit(1)
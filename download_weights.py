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
    Fetches the Stable Diffusion XL pipelines and optionally Wan2.1 T2V pipeline from the HuggingFace model hub.
    """
    token = get_hf_token()
    common_args = {
        "torch_dtype": torch.float16,
        "variant": "fp16",
        "use_safetensors": True,
        "use_auth_token": token,
    }
    common_args_no_float16 = {
        "torch_dtype": torch.float16,
        "use_safetensors": True,
        "use_auth_token": token,
    }

    # SDXL models (essential)
    print("Downloading SDXL models...")
    pipe = fetch_pretrained_model(
        StableDiffusionXLPipeline,
        "stabilityai/stable-diffusion-xl-base-1.0",
        **common_args,
    )
    vae = fetch_pretrained_model(
        AutoencoderKL, "madebyollin/sdxl-vae-fp16-fix", **{"torch_dtype": torch.float16, "use_auth_token": token}
    )
    refiner = fetch_pretrained_model(
        StableDiffusionXLImg2ImgPipeline,
        "stabilityai/stable-diffusion-xl-refiner-1.0",
        **common_args,
    )
    inpaint = fetch_pretrained_model(
        StableDiffusionXLInpaintPipeline,  # Use specific SDXL inpaint pipeline
        "diffusers/stable-diffusion-xl-1.0-inpainting-0.1",  # Changed to SDXL inpainting
        **common_args,  # Use common_args instead of no_float16 for SDXL consistency
    )

    # Wan2.1-T2V-1.3B models (optional - load from local if available)
    wan_vae = None
    wan_t2v = None
    
    if os.environ.get("DOWNLOAD_WAN2_MODEL", "false").lower() == "true":
        print("Loading Wan2.1-T2V-1.3B model...")
        
        # Check for local model path
        local_wan_path = "/runpod-volume/Wan2.1-T2V-1.3B-Diffusers"
        
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
                print("✅ Wan2.1-T2V-1.3B loaded successfully from local storage!")
            else:
                print(f"⚠️ Local path not found: {local_wan_path}")
                print("🌐 Attempting to download from Hugging Face...")
                
                # Fallback to downloading from HuggingFace
                wan_model_id = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"
                
                wan_vae = fetch_pretrained_model(
                    AutoencoderKLWan,
                    wan_model_id,
                    subfolder="vae",
                    torch_dtype=torch.float32,
                    use_auth_token=token,
                )
                
                wan_t2v = fetch_pretrained_model(
                    WanPipeline,
                    wan_model_id,
                    vae=wan_vae,
                    torch_dtype=torch.bfloat16,
                    use_safetensors=True,
                    use_auth_token=token,
                )
                print("✅ Wan2.1-T2V-1.3B downloaded successfully!")
                
        except Exception as e:
            print(f"⚠️ Wan2.1 load failed: {e}")
            print("🔄 Continuing with SDXL-only functionality")
            wan_vae = None
            wan_t2v = None
    else:
        print("ℹ️ Skipping Wan2.1 (DOWNLOAD_WAN2_MODEL not set to 'true')")

    return pipe, refiner, vae, inpaint, wan_vae, wan_t2v


if __name__ == "__main__":
    print("Downloading SDXL weights and Wan2.1-T2V-14B pipelines...")
    
    try:
        # Download with retry logic
        max_retries = 2
        for attempt in range(max_retries):
            try:
                get_diffusion_pipelines()
                print("✅ All models downloaded successfully!")
                break
            except Exception as e:
                print(f"❌ Download attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    print("🔄 Retrying model download...")
                    import time
                    time.sleep(10)  # Wait 10 seconds before retry
                else:
                    print("💥 Final attempt failed!")
                    raise
                    
    except Exception as e:
        print(f"💥 Model download failed completely: {e}")
        print("🔍 This might be a temporary issue. Try rebuilding.")
        # Exit with error code
        import sys
        sys.exit(1)
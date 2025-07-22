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

    # Wan2.1-T2V-14B models (optional - only if environment variable is set)
    wan_vae = None
    wan_t2v = None
    
    if os.environ.get("DOWNLOAD_WAN2_MODEL", "false").lower() == "true":
        print("Downloading Wan2.1-T2V-1.3B model components...")
        try:
            # Use the smaller 1.3B model instead of 14B
            wan_model_id = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"
            
            # Download Wan VAE separately for better control
            wan_vae = fetch_pretrained_model(
                AutoencoderKLWan,
                wan_model_id,
                subfolder="vae",
                torch_dtype=torch.float32,  # Keep VAE as float32 for stability
                use_auth_token=token,
            )
            
            # Download main Wan T2V pipeline (1.3B version)
            wan_t2v = fetch_pretrained_model(
                WanPipeline,
                wan_model_id,
                vae=wan_vae,
                torch_dtype=torch.bfloat16,  # Use bfloat16 for 1.3B model
                use_safetensors=True,
                use_auth_token=token,
            )
            print("✅ Wan2.1-T2V-1.3B downloaded successfully!")
        except Exception as e:
            print(f"⚠️ Wan2.1 download failed: {e}")
            print("🔄 Continuing with SDXL-only functionality")
            wan_vae = None
            wan_t2v = None
    else:
        print("ℹ️ Skipping Wan2.1 download (DOWNLOAD_WAN2_MODEL not set to 'true')")

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
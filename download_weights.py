import os
import torch
from diffusers import (
    StableDiffusionXLPipeline,
    StableDiffusionXLImg2ImgPipeline,
    StableDiffusionXLInpaintPipeline,  # Use the specific SDXL inpaint pipeline
    AutoencoderKL,
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
    Fetches the Stable Diffusion XL pipelines from the HuggingFace model hub.
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

    return pipe, refiner, vae, inpaint


if __name__ == "__main__":
    print("Downloading SDXL weights and pipelines...")
    get_diffusion_pipelines()
    print("All done!")
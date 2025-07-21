# Faster Model Download Script
# Downloads models with better retry logic and progress tracking

import os
from huggingface_hub import snapshot_download
import torch

def download_with_retry(repo_id, max_retries=5):
    """Download with better retry logic"""
    for attempt in range(max_retries):
        try:
            print(f"\n📥 Downloading {repo_id} (attempt {attempt + 1}/{max_retries})")
            
            path = snapshot_download(
                repo_id=repo_id,
                cache_dir=None,  # Use default cache
                resume_download=True,  # Resume if interrupted
                local_files_only=False,
                timeout=300,  # 5 minute timeout per file
            )
            print(f"✅ Successfully downloaded {repo_id}")
            return path
            
        except Exception as e:
            print(f"❌ Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print(f"⏳ Retrying in 5 seconds...")
                import time
                time.sleep(5)
            else:
                print(f"💥 Failed to download {repo_id} after {max_retries} attempts")
                raise

def main():
    print("🚀 Starting faster SDXL model downloads...")
    
    models = [
        "stabilityai/stable-diffusion-xl-base-1.0",
        "stabilityai/stable-diffusion-xl-refiner-1.0", 
        "diffusers/stable-diffusion-xl-1.0-inpainting-0.1",  # New SDXL inpainting
        "madebyollin/sdxl-vae-fp16-fix"
    ]
    
    for model in models:
        try:
            download_with_retry(model)
        except Exception as e:
            print(f"🔥 Critical error downloading {model}: {e}")
            continue
    
    print("\n🎉 All downloads completed!")

if __name__ == "__main__":
    main()

# Git LFS Download Method (Often Faster)
# Uses git to download models, which can be more reliable

import os
import subprocess

def git_clone_model(repo_id, local_path=None):
    """Clone model using git (often faster than HTTP)"""
    if local_path is None:
        local_path = repo_id.replace("/", "--")
    
    cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
    full_path = os.path.join(cache_dir, f"models--{local_path}")
    
    if os.path.exists(full_path):
        print(f"✅ {repo_id} already exists, skipping")
        return full_path
    
    print(f"📦 Git cloning {repo_id}...")
    
    try:
        # Clone with git
        subprocess.run([
            "git", "clone", 
            f"https://huggingface.co/{repo_id}", 
            full_path
        ], check=True, capture_output=True, text=True)
        
        print(f"✅ Successfully cloned {repo_id}")
        return full_path
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Git clone failed for {repo_id}: {e}")
        return None

def main():
    print("🌐 Downloading SDXL models via Git LFS...")
    
    models = [
        ("stabilityai/stable-diffusion-xl-base-1.0", "stabilityai--stable-diffusion-xl-base-1.0"),
        ("stabilityai/stable-diffusion-xl-refiner-1.0", "stabilityai--stable-diffusion-xl-refiner-1.0"),
        ("diffusers/stable-diffusion-xl-1.0-inpainting-0.1", "diffusers--stable-diffusion-xl-1.0-inpainting-0.1"),
        ("madebyollin/sdxl-vae-fp16-fix", "madebyollin--sdxl-vae-fp16-fix")
    ]
    
    for repo_id, local_name in models:
        git_clone_model(repo_id, local_name)
    
    print("\n🎉 Git downloads completed!")

if __name__ == "__main__":
    main()

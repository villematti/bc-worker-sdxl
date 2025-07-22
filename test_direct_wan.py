#!/usr/bin/env python3
"""
Direct test of Wan2.1-T2V-1.3B model without SDXL dependencies
"""

def test_wan_direct():
    print("🧪 Testing Wan2.1-T2V-1.3B model directly...")
    
    try:
        print("📦 Loading imports...")
        import torch
        from diffusers import AutoencoderKLWan, WanPipeline
        from diffusers.utils import export_to_video
        print("✅ Imports successful")
        
        print(f"🎮 CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"🔥 GPU: {torch.cuda.get_device_name(0)}")
        
        print("📥 Loading Wan2.1-T2V-1.3B model...")
        model_id = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"
        
        # Load VAE
        print("  📦 Loading VAE...")
        vae = AutoencoderKLWan.from_pretrained(
            model_id,
            subfolder="vae",
            torch_dtype=torch.float32,
            local_files_only=True,
        )
        print("  ✅ VAE loaded")
        
        # Load pipeline
        print("  📦 Loading pipeline...")
        pipe = WanPipeline.from_pretrained(
            model_id,
            vae=vae,
            torch_dtype=torch.bfloat16,
            use_safetensors=True,
            local_files_only=True,
        ).to("cuda")
        print("  ✅ Pipeline loaded")
        
        # Enable optimizations
        pipe.enable_attention_slicing()
        print("  ✅ Optimizations enabled")
        
        # Test generation
        print("🎬 Generating test video...")
        prompt = "A cat walking on grass"
        negative_prompt = "blurry, low quality, static"
        
        with torch.inference_mode():
            output = pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                height=480,
                width=832,
                num_frames=25,  # Reduced for testing
                guidance_scale=5.0,
                num_inference_steps=10,  # Reduced for testing
            ).frames[0]
        
        print(f"✅ Video generated! {len(output)} frames")
        
        # Save video
        print("💾 Saving video...")
        export_to_video(output, "test_output.mp4", fps=15)
        print("✅ Video saved as test_output.mp4")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_wan_direct()
    if success:
        print("\n🎉 SUCCESS: Wan2.1-T2V-1.3B model works locally!")
    else:
        print("\n💥 FAILED: Check the error above")

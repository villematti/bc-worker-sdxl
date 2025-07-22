#!/usr/bin/env python3
"""
Test script for Wan2.1 Text-to-Video generation
Optimized for low VRAM (6GB) with fallback strategies
Uses the 1.3B T2V model instead of the 14B I2V model
"""

import os
import torch
import gc
from diffusers.utils import export_to_video
from PIL import Image
import numpy as np

def check_vram():
    """Check available VRAM"""
    if torch.cuda.is_available():
        total_vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
        reserved_vram = torch.cuda.memory_reserved(0) / 1024**3
        allocated_vram = torch.cuda.memory_allocated(0) / 1024**3
        free_vram = total_vram - reserved_vram
        
        print(f"🎮 GPU: {torch.cuda.get_device_name(0)}")
        print(f"📊 Total VRAM: {total_vram:.1f}GB")
        print(f"📊 Reserved: {reserved_vram:.1f}GB")
        print(f"📊 Allocated: {allocated_vram:.1f}GB") 
        print(f"📊 Available: {free_vram:.1f}GB")
        
        return total_vram, free_vram
    else:
        print("❌ No CUDA GPU available")
        return 0, 0

def optimize_memory():
    """Optimize memory settings for low VRAM"""
    # Clear cache
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        gc.collect()
    
    # Set memory allocation settings
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128'
    
    print("🧹 Memory optimized")

def test_wan_video_generation():
    """Test Wan2.1 T2V with memory optimizations"""
    
    print("🎬 Starting Wan2.1 Text-to-Video Test")
    print("=" * 50)
    
    # Check system
    total_vram, free_vram = check_vram()
    
    if total_vram < 4:
        print("❌ Insufficient VRAM for Wan2.1 (need at least 4GB)")
        return False
    
    # Optimize memory
    optimize_memory()
    
    try:
        print("\n📦 Loading Wan2.1 components...")
        
        # Import here to avoid early memory allocation
        from diffusers import AutoencoderKLWan, WanPipeline
        
        model_id = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"
        
        # Memory optimization settings
        low_vram_settings = {
            "torch_dtype": torch.bfloat16,  # Use bfloat16 for better compatibility
            "use_safetensors": True,
        }
        
        print("🔧 Loading VAE...")
        vae = AutoencoderKLWan.from_pretrained(
            model_id, 
            subfolder="vae", 
            torch_dtype=torch.float32,  # Keep VAE as float32 for stability
            low_cpu_mem_usage=True
        )
        
        print("🔧 Loading main T2V pipeline...")
        pipe = WanPipeline.from_pretrained(
            model_id, 
            vae=vae, 
            **low_vram_settings,
            low_cpu_mem_usage=True
        )
        
        # Memory optimizations for low VRAM
        if total_vram < 8:
            print("⚡ Applying low VRAM optimizations...")
            
            # Enable CPU offloading
            pipe.enable_model_cpu_offload()
            
            # Enable attention slicing
            pipe.enable_attention_slicing()
            
            # Enable VAE slicing
            if hasattr(pipe, 'enable_vae_slicing'):
                pipe.enable_vae_slicing()
            
            # Enable memory efficient attention
            if hasattr(pipe, 'enable_xformers_memory_efficient_attention'):
                try:
                    pipe.enable_xformers_memory_efficient_attention()
                    print("  ✅ XFormers attention enabled")
                except:
                    print("  ⚠️ XFormers not available, using default attention")
        else:
            pipe.to("cuda")
        
        print("✅ Pipeline loaded successfully!")
        
        # Test prompt - simpler for T2V
        print("\n🎬 Preparing for video generation...")
        
        # Test prompts
        prompt = "A cat walking on grass, realistic, high quality"
        negative_prompt = "Bright tones, overexposed, static, blurred details, subtitles, style, works, paintings, images, static, overall gray, worst quality, low quality, JPEG compression residue, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn faces, deformed, disfigured, misshapen limbs, fused fingers, still picture, messy background, three legs, many people in the background, walking backwards"
        
        # Video parameters optimized for 6GB VRAM
        video_params = {
            "height": 320,  # Smaller than default 480 for 6GB VRAM
            "width": 576,   # Maintain aspect ratio (480p scaled down)
            "num_frames": 25 if total_vram < 8 else 49,  # Fewer frames for low VRAM
            "guidance_scale": 6.0,  # As recommended for 1.3B model
        }
        
        print(f"  📝 Prompt: {prompt}")
        print(f"  📏 Size: {video_params['width']}x{video_params['height']}")
        print(f"  🎞️ Frames: {video_params['num_frames']}")
        
        print(f"\n🎬 Generating text-to-video...")
        
        # Clear memory before generation
        optimize_memory()
        
        # Generate video
        with torch.inference_mode():
            output = pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                **video_params
            ).frames[0]
        
        # Export video
        output_path = "test_wan_t2v_output.mp4"
        export_to_video(output, output_path, fps=15)
        
        print(f"✅ Video generated successfully!")
        print(f"📁 Output saved to: {output_path}")
        print(f"🎞️ Video info: {len(output)} frames at {video_params['width']}x{video_params['height']}")
        
        return True
        
    except torch.cuda.OutOfMemoryError as e:
        print(f"❌ CUDA Out of Memory: {e}")
        print("💡 Try:")
        print("  - Closing other GPU applications")
        print("  - Reducing num_frames or resolution")
        print("  - Using CPU-only mode (very slow)")
        return False
        
    except Exception as e:
        print(f"❌ Error during generation: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up
        optimize_memory()

def test_requirements():
    """Test if required packages are installed"""
    print("🔍 Checking requirements...")
    
    try:
        import diffusers
        print(f"✅ diffusers: {diffusers.__version__}")
    except ImportError:
        print("❌ diffusers not installed")
        return False
    
    try:
        import transformers
        print(f"✅ transformers: {transformers.__version__}")
    except ImportError:
        print("❌ transformers not installed")
        return False
    
    try:
        from diffusers import AutoencoderKLWan, WanPipeline
        print("✅ Wan T2V components available")
    except ImportError:
        print("❌ Wan T2V components not available - diffusers version may be too old")
        print("💡 Try: pip install --upgrade diffusers")
        return False
    
    return True

if __name__ == "__main__":
    print("🎬 Wan2.1 Local Test Script")
    print("=" * 50)
    
    # Check requirements
    if not test_requirements():
        print("\n❌ Requirements check failed")
        exit(1)
    
    # Set HuggingFace token if available
    hf_token = os.environ.get("HUGGINGFACE_TOKEN")
    if hf_token:
        print(f"🔑 Using HuggingFace token: {hf_token[:8]}...")
    else:
        print("⚠️ No HuggingFace token found in HUGGINGFACE_TOKEN")
        print("💡 Some models may require authentication")
    
    print("\n" + "=" * 50)
    
    # Run test
    success = test_wan_video_generation()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Test completed successfully!")
        print("💡 You can now integrate Wan2.1 into your SDXL worker")
    else:
        print("❌ Test failed - see errors above")
        print("💡 Consider testing on your 48GB RunPod instance instead")

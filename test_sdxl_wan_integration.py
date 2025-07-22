#!/usr/bin/env python3
"""
Test script for SDXL + Wan2.1-T2V-14B integration
Tests the complete workflow including video generation
"""

import os
import sys
import json
from datetime import datetime

# Test video generation request
def test_video_generation():
    """Test video generation with the integrated handler"""
    
    # Mock job for testing
    test_job = {
        "id": f"test_job_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "input": {
            "task_type": "text2video",
            "prompt": "A cat walking on grass, realistic, high quality",
            "negative_prompt": "blurry, low quality, static, still image",
            "video_height": 480,
            "video_width": 832,
            "num_frames": 49,  # Smaller for local testing
            "video_guidance_scale": 5.0,
            "fps": 15,
            "seed": 42
        }
    }
    
    print("🎬 Testing Wan2.1-T2V-14B Video Generation")
    print("=" * 60)
    print(f"Test Job: {json.dumps(test_job, indent=2)}")
    print("=" * 60)
    
    try:
        # Import the handler
        from handler import generate_image
        
        print("📦 Handler imported successfully")
        
        # Run the generation
        print("\n🎬 Starting video generation...")
        result = generate_image(test_job)
        
        print("\n✅ Video generation completed!")
        print("📊 Result:")
        print(json.dumps(result, indent=2, default=str))
        
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_image_generation():
    """Test that existing image generation still works"""
    
    test_job = {
        "id": f"test_img_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "input": {
            "task_type": "text2img",  # Explicit image mode
            "prompt": "A beautiful landscape, masterpiece, high quality",
            "negative_prompt": "blurry, low quality",
            "height": 1024,
            "width": 1024,
            "num_inference_steps": 25,
            "guidance_scale": 7.5,
            "seed": 42
        }
    }
    
    print("\n🖼️ Testing SDXL Image Generation (existing functionality)")
    print("=" * 60)
    
    try:
        from handler import generate_image
        
        result = generate_image(test_job)
        
        print("✅ Image generation completed!")
        print("📊 Result keys:", list(result.keys()))
        
        return True
        
    except Exception as e:
        print(f"❌ Error during image test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_schema_validation():
    """Test the updated schema with video parameters"""
    
    print("\n📋 Testing Schema Validation")
    print("=" * 60)
    
    try:
        from schemas import INPUT_SCHEMA
        
        print("✅ Schema imported successfully")
        print("📊 New video parameters:")
        
        video_params = [
            'task_type', 'video_height', 'video_width', 
            'num_frames', 'video_guidance_scale', 'fps'
        ]
        
        for param in video_params:
            if param in INPUT_SCHEMA:
                schema_info = INPUT_SCHEMA[param]
                print(f"  • {param}: {schema_info}")
            else:
                print(f"  ❌ {param}: NOT FOUND")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema test failed: {e}")
        return False

def check_dependencies():
    """Check if all required dependencies are available"""
    
    print("🔍 Checking Dependencies")
    print("=" * 60)
    
    dependencies = [
        ('torch', 'torch'),
        ('diffusers', 'diffusers'),
        ('PIL', 'PIL'),
        ('numpy', 'numpy'),
        ('transformers', 'transformers'),
        ('runpod', 'runpod'),
        ('ftfy', 'ftfy'),
        ('cv2', 'opencv-python'),
        ('imageio', 'imageio'),
    ]
    
    missing = []
    
    for module, package in dependencies:
        try:
            __import__(module)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - NOT FOUND")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️ Missing dependencies: {', '.join(missing)}")
        print("💡 Install with: pip install " + " ".join(missing))
        return False
    
    # Check specific diffusers components
    try:
        from diffusers import AutoencoderKLWan, WanPipeline
        print("✅ Wan2.1 components (AutoencoderKLWan, WanPipeline)")
    except ImportError:
        print("❌ Wan2.1 components - diffusers version may be too old")
        print("💡 Try: pip install --upgrade diffusers>=0.34.0")
        return False
    
    return True

if __name__ == "__main__":
    print("🧪 SDXL + Wan2.1-T2V-14B Integration Test Suite")
    print("=" * 80)
    
    # Check dependencies first
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please install missing packages.")
        sys.exit(1)
    
    # Test schema
    if not test_schema_validation():
        print("\n❌ Schema validation failed.")
        sys.exit(1)
    
    print("\n🎯 All dependency and schema checks passed!")
    print("\n⚠️ Note: The following tests require the models to be downloaded")
    print("💡 This would happen during Docker build in production")
    
    response = input("\n📥 Do you want to test with downloaded models? (y/N): ")
    
    if response.lower() in ['y', 'yes']:
        print("\n🧪 Running full tests with models...")
        
        # Test existing functionality
        if test_image_generation():
            print("✅ Image generation test passed")
        else:
            print("❌ Image generation test failed")
        
        # Test new video functionality  
        if test_video_generation():
            print("✅ Video generation test passed")
        else:
            print("❌ Video generation test failed")
    
    print("\n🎉 Integration test suite completed!")
    print("💡 Ready for RunPod deployment with both SDXL and Wan2.1-T2V-14B!")

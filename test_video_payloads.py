#!/usr/bin/env python3
"""
Simple test script for video generation endpoint
For testing the integration without full model downloads
"""

import json

def test_video_payload():
    """Test video generation payload structure"""
    
    # Example video generation request
    video_request = {
        "input": {
            "task_type": "text2video",
            "prompt": "A majestic eagle soaring through mountain peaks, cinematic, high quality, 4k",
            "negative_prompt": "blurry, low quality, static, still image, artifacts",
            
            # Video-specific parameters for 14B model
            "video_height": 480,        # 480P optimized for 1.3B model
            "video_width": 832,         # 832x480 resolution
            "num_frames": 81,           # Default for 14B model
            "video_guidance_scale": 5.0, # Recommended for 14B
            "fps": 15,                  # Standard frame rate
            
            # Standard parameters
            "seed": 12345,
        }
    }
    
    print("🎬 Wan2.1-T2V-14B Video Generation Request")
    print("=" * 60)
    print(json.dumps(video_request, indent=2))
    print("=" * 60)
    
    # Example for 480P (smaller, faster)
    video_request_480p = {
        "input": {
            "task_type": "text2video",
            "prompt": "A cat playing with a ball of yarn, cute, realistic",
            "video_height": 480,        # 480P for faster generation
            "video_width": 832,         # 832x480 resolution  
            "num_frames": 49,           # Fewer frames for faster generation
            "video_guidance_scale": 5.0,
            "fps": 15,
            "seed": 67890,
        }
    }
    
    print("\n🎬 Alternative 480P Request (faster generation)")
    print("=" * 60)
    print(json.dumps(video_request_480p, indent=2))
    print("=" * 60)
    
    # Image generation request (existing functionality)
    image_request = {
        "input": {
            "task_type": "text2img",    # Explicitly specify image mode
            "prompt": "A beautiful sunset over the ocean, masterpiece",
            "negative_prompt": "blurry, low quality",
            "height": 1024,
            "width": 1024,
            "num_inference_steps": 25,
            "guidance_scale": 7.5,
            "seed": 11111,
        }
    }
    
    print("\n🖼️ SDXL Image Generation Request (existing)")
    print("=" * 60)
    print(json.dumps(image_request, indent=2))
    print("=" * 60)
    
    print("\n💡 Usage Notes:")
    print("📊 Video Generation:")
    print("  • task_type: 'text2video' triggers Wan2.1-T2V-14B")
    print("  • Supports 480P (832x480) and 720P (1280x720)")
    print("  • 14B model provides higher quality than 1.3B")
    print("  • With 48GB RunPod VRAM, can handle full 81 frames at 720P")
    print("  • Returns video_url and video_info")
    
    print("\n🖼️ Image Generation:")
    print("  • task_type: 'text2img', 'img2img', or 'inpaint'")
    print("  • Uses existing SDXL pipelines")
    print("  • Backwards compatible with all existing requests")
    
    print("\n🚀 Ready for RunPod deployment!")

if __name__ == "__main__":
    test_video_payload()

#!/usr/bin/env python3
"""
Test script for Wan2.1-T2V-1.3B integration with SDXL worker
Optimized for smaller model size and faster deployment
"""

import json
import time

# Test payloads optimized for 1.3B model
test_payloads = {
    "quick_video_1_3b": {
        "task_type": "text2video",
        "prompt": "A cat playing with a ball of yarn, fluffy and cute",
        "negative_prompt": "blurry, distorted, ugly",
        "video_height": 480,
        "video_width": 704,  # Optimal for 1.3B
        "num_frames": 25,    # Reduced for efficiency
        "video_guidance_scale": 6.0,  # Lower guidance for 1.3B
        "fps": 8,
        "num_inference_steps": 20,  # Faster generation
        "seed": 42
    },
    
    "standard_video_1_3b": {
        "task_type": "text2video",
        "prompt": "A beautiful sunset over mountains, golden hour lighting, cinematic",
        "negative_prompt": "blurry, low quality, distorted, ugly, bad anatomy",
        "video_height": 480,
        "video_width": 832,  # Alternative resolution
        "num_frames": 49,    # Medium length
        "video_guidance_scale": 7.0,
        "fps": 12,
        "num_inference_steps": 25,
        "seed": 12345
    },
    
    "high_quality_video_1_3b": {
        "task_type": "text2video", 
        "prompt": "A dragon flying through clouds, majestic and powerful, fantasy art style",
        "negative_prompt": "blurry, low quality, distorted, ugly, bad anatomy, static",
        "video_height": 480,
        "video_width": 832,  # Optimal resolution for 1.3B model
        "num_frames": 25,     # Keep frames reasonable for 720p
        "video_guidance_scale": 8.0,
        "fps": 15,
        "num_inference_steps": 30,
        "seed": 99999
    }
}

def run_local_test(payload_name, payload):
    """Test payload locally using handler.py"""
    print(f"\n🧪 Testing {payload_name}:")
    print(f"   Resolution: {payload['video_width']}x{payload['video_height']}")
    print(f"   Frames: {payload['num_frames']} @ {payload['fps']}fps")
    print(f"   Guidance: {payload['video_guidance_scale']}")
    print(f"   Prompt: {payload['prompt'][:50]}...")
    
    try:
        # Import handler
        from handler import handler
        
        # Create job input
        job_input = {"job_input": payload}
        
        start_time = time.time()
        result = handler(job_input)
        end_time = time.time()
        
        if result and "status" in result:
            if result["status"] == "COMPLETED":
                duration = end_time - start_time
                print(f"   ✅ SUCCESS in {duration:.1f}s")
                
                # Check output
                if "output" in result and result["output"]:
                    print(f"   📁 Output: {len(result['output'])} files generated")
                else:
                    print(f"   ⚠️ No output files")
                    
            else:
                print(f"   ❌ FAILED: {result.get('error', 'Unknown error')}")
        else:
            print(f"   ❌ FAILED: Invalid response")
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")

def create_runpod_payload(payload_name, payload):
    """Create payload file for RunPod testing"""
    filename = f"test_{payload_name}.json"
    
    with open(filename, 'w') as f:
        json.dump(payload, f, indent=2)
    
    print(f"📄 Created {filename} for RunPod testing")

def main():
    print("🎬 Wan2.1-T2V-1.3B Model Test Suite")
    print("=" * 50)
    
    print("\n📋 Test Configurations:")
    for name, payload in test_payloads.items():
        print(f"  • {name}: {payload['video_width']}x{payload['video_height']} @ {payload['num_frames']}f")
    
    # Create test payload files
    print("\n📁 Creating test files...")
    for name, payload in test_payloads.items():
        create_runpod_payload(name, payload)
    
    # Ask user if they want to run local tests
    print("\n🤔 Do you want to run local tests? (y/n)")
    response = input().strip().lower()
    
    if response == 'y':
        print("\n🚀 Running local tests...")
        for name, payload in test_payloads.items():
            run_local_test(name, payload)
    
    print("\n📖 1.3B Model Optimizations Applied:")
    print("   • Reduced default frames: 81 → 25")
    print("   • Optimized resolution: 832x480 → 704x480")
    print("   • Lower guidance scale: 7.5 → 6.0")
    print("   • Model size: ~23GB → ~8GB")
    print("   • Expected Docker image: ~33GB → ~14GB")
    
    print("\n🎯 RunPod Deployment Benefits:")
    print("   • Faster upload times (14GB vs 33GB)")
    print("   • Quicker cold starts")
    print("   • Lower memory pressure")
    print("   • Still supports 720p generation")

if __name__ == "__main__":
    main()

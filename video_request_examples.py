#!/usr/bin/env python3
"""
Video Generation Request Examples
Complete examples for using the SDXL + Wan2.1-T2V-14B worker
"""

import json
import requests

# Your RunPod endpoint URL (replace with your actual endpoint)
RUNPOD_ENDPOINT = "https://api.runpod.ai/v2/your-endpoint-id/runsync"
RUNPOD_API_KEY = "your-runpod-api-key"

def create_video_request_720p():
    """High quality 720P video generation request"""
    
    request_payload = {
        "input": {
            # Video mode trigger
            "task_type": "text2video",
            
            # Main prompt
            "prompt": "A majestic eagle soaring through snow-capped mountain peaks, cinematic shot, golden hour lighting, high quality, 4k",
            
            # Negative prompt (optional but recommended)
            "negative_prompt": "blurry, low quality, static, still image, artifacts, distorted, ugly, deformed",
            
            # Video resolution parameters
            "video_height": 480,      # 480P optimized for 1.3B model
            "video_width": 832,       # Optimal width for 1.3B model
            
            # Video generation parameters
            "num_frames": 81,         # ~5 second video at 15fps
            "video_guidance_scale": 5.0,  # Recommended for 14B model
            "fps": 15,                # Frame rate
            
            # Optional seed for reproducibility
            "seed": 42
        }
    }
    
    return request_payload

def create_video_request_480p():
    """Faster 480P video generation request"""
    
    request_payload = {
        "input": {
            "task_type": "text2video",
            
            "prompt": "A cute cat playing with a ball of yarn in a cozy living room, warm lighting, realistic",
            "negative_prompt": "blurry, low quality, static, still image",
            
            # 480P for faster generation
            "video_height": 480,
            "video_width": 832,       # Automatically set to 832 for 480P
            
            # Fewer frames for faster generation
            "num_frames": 49,         # ~3 second video
            "video_guidance_scale": 5.0,
            "fps": 15,
            
            "seed": 12345
        }
    }
    
    return request_payload

def create_video_request_custom():
    """Custom video with all parameters specified"""
    
    request_payload = {
        "input": {
            "task_type": "text2video",
            
            # Detailed prompt for better results
            "prompt": "A peaceful waterfall cascading down moss-covered rocks in a lush forest, sunbeams filtering through the canopy, birds flying, nature documentary style, ultra high quality",
            
            # Comprehensive negative prompt
            "negative_prompt": "static, still image, photograph, painting, artwork, blurry, low quality, distorted, deformed, ugly, artifacts, compression, pixelated, grainy, dark, underexposed, overexposed",
            
            # Video parameters
            "video_height": 480,      # Optimal quality for 1.3B model
            "video_width": 832,
            "num_frames": 65,         # ~4.3 second video
            "video_guidance_scale": 6.0,  # Slightly higher guidance
            "fps": 15,
            
            # Reproducible generation
            "seed": 999
        }
    }
    
    return request_payload

def send_video_request(payload):
    """Send request to RunPod endpoint"""
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {RUNPOD_API_KEY}"
    }
    
    print("🎬 Sending video generation request...")
    print(f"📊 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(RUNPOD_ENDPOINT, json=payload, headers=headers)
        result = response.json()
        
        print("✅ Request completed!")
        print(f"📊 Response: {json.dumps(result, indent=2)}")
        
        return result
        
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

# Example using curl command
def generate_curl_examples():
    """Generate curl command examples"""
    
    print("🌐 cURL Examples for Video Generation")
    print("=" * 60)
    
    # 720P example
    payload_720p = create_video_request_720p()
    print("\n📹 High Quality 720P Video:")
    print(f"""
curl -X POST "{RUNPOD_ENDPOINT}" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer {RUNPOD_API_KEY}" \\
  -d '{json.dumps(payload_720p)}'
""")
    
    # 480P example  
    payload_480p = create_video_request_480p()
    print("\n⚡ Fast 480P Video:")
    print(f"""
curl -X POST "{RUNPOD_ENDPOINT}" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer {RUNPOD_API_KEY}" \\
  -d '{json.dumps(payload_480p)}'
""")

if __name__ == "__main__":
    print("🎬 Video Generation Request Examples")
    print("=" * 60)
    
    # Show different request types
    print("\n📹 720P High Quality Request:")
    print(json.dumps(create_video_request_720p(), indent=2))
    
    print("\n⚡ 480P Fast Request:")
    print(json.dumps(create_video_request_480p(), indent=2))
    
    print("\n🎨 Custom Request:")
    print(json.dumps(create_video_request_custom(), indent=2))
    
    # Show curl examples
    generate_curl_examples()
    
    print("\n💡 Key Points:")
    print("• task_type: 'text2video' triggers video generation")
    print("• video_height/video_width: Resolution (480P - 832x480 only for 1.3B model)")
    print("• num_frames: 16-121 frames (more = longer video)")
    print("• video_guidance_scale: 5.0 recommended for 14B model")
    print("• fps: Frame rate (10-30, default 15)")
    print("• Response includes video_url and video_info")

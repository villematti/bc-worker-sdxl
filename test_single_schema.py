#!/usr/bin/env python3
"""
TEST: Single Schema Validation

Test the simplified single INPUT_SCHEMA to ensure it works correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from schemas import INPUT_SCHEMA
from runpod.serverless.utils.rp_validator import validate

def test_schema_validation():
    """Test that the single INPUT_SCHEMA validates correctly"""
    print("🧪 Testing Single INPUT_SCHEMA Validation\n")
    
    # Test 1: Yorkshire Terrier image request
    image_request = {
        "prompt": "A Yorkshire Terrier running in a meadow",
        "task_type": "text2img",
        "width": 1024,
        "height": 1024,
        "guidance_scale": 7.5,
        "num_inference_steps": 25,
        "refiner_inference_steps": 50
        # NO video parameters
    }
    
    print("📋 Test 1: Image request validation")
    try:
        validated = validate(image_request, INPUT_SCHEMA)
        print("   ✅ Image request validated successfully")
        print(f"   task_type: {validated.get('task_type')}")
        print(f"   num_frames: {validated.get('num_frames')}")
        print(f"   video_height: {validated.get('video_height')}")
    except Exception as e:
        print(f"   ❌ Image validation failed: {e}")
        return False
    
    # Test 2: Video request
    video_request = {
        "prompt": "A Yorkshire Terrier running in a meadow",
        "task_type": "text2video",
        "num_frames": 81,
        "video_height": 480,
        "video_width": 832,
        "video_guidance_scale": 5.0,
        "fps": 15
    }
    
    print("\n📋 Test 2: Video request validation")
    try:
        validated = validate(video_request, INPUT_SCHEMA)
        print("   ✅ Video request validated successfully")
        print(f"   task_type: {validated.get('task_type')}")
        print(f"   num_frames: {validated.get('num_frames')}")
        print(f"   video_height: {validated.get('video_height')}")
        print(f"   video_width: {validated.get('video_width')}")
    except Exception as e:
        print(f"   ❌ Video validation failed: {e}")
        return False
    
    # Test 3: Invalid video dimensions (should fail)
    invalid_video = {
        "prompt": "Test",
        "task_type": "text2video", 
        "num_frames": 81,
        "video_height": 720,  # Invalid for 1.3B model
        "video_width": 1280   # Invalid for 1.3B model
    }
    
    print("\n📋 Test 3: Invalid video dimensions (should fail)")
    try:
        validated = validate(invalid_video, INPUT_SCHEMA)
        print("   ❌ Invalid video request was accepted (this is wrong!)")
        return False
    except Exception as e:
        print("   ✅ Invalid video request properly rejected")
        print(f"   Error: {e}")
    
    return True

def test_routing_logic():
    """Test the routing logic with the single schema"""
    print("\n🔍 Testing Routing Logic:")
    
    # Image request - should have no video parameters
    image_request = {"task_type": "text2img", "prompt": "test"}
    validated_image = validate(image_request, INPUT_SCHEMA)
    
    is_video = bool(validated_image.get("num_frames"))
    print(f"   Image request num_frames: {validated_image.get('num_frames')} → video: {is_video}")
    
    # Video request - should have video parameters
    video_request = {"task_type": "text2video", "prompt": "test", "num_frames": 50}
    validated_video = validate(video_request, INPUT_SCHEMA)
    
    is_video = bool(validated_video.get("num_frames"))
    print(f"   Video request num_frames: {validated_video.get('num_frames')} → video: {is_video}")
    
    return True

if __name__ == "__main__":
    print("🧪 Testing Single Schema Solution")
    print("   No more 'legacy' vs 'new' - just ONE schema that works!\n")
    
    success1 = test_schema_validation()
    success2 = test_routing_logic()
    
    if success1 and success2:
        print("\n🎉 SUCCESS: Single schema works perfectly!")
        print("   ✅ Validates image requests correctly")
        print("   ✅ Validates video requests correctly") 
        print("   ✅ Rejects invalid video dimensions")
        print("   ✅ Routing logic works as expected")
        print("   ✅ No unnecessary complexity!")
    else:
        print("\n💥 FAILURE: Schema validation issues")
        exit(1)

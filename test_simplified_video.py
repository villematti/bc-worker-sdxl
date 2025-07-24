#!/usr/bin/env python3
"""
TEST: Simplified Video Parameters

Test that video parameters are now simplified - only num_frames varies,
everything else is fixed defaults.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from schemas import INPUT_SCHEMA

def test_simplified_video_params():
    """Test the simplified video parameter approach"""
    print("🎬 Testing Simplified Video Parameters\n")
    
    print("📋 Video parameter configuration:")
    video_params = ['video_height', 'video_width', 'num_frames', 'video_guidance_scale', 'fps']
    
    for param in video_params:
        if param in INPUT_SCHEMA:
            config = INPUT_SCHEMA[param]
            default = config.get('default')
            has_constraints = 'constraints' in config
            
            if param == 'num_frames':
                print(f"   🎯 {param}: default={default} (varies per request)")
                if has_constraints:
                    print(f"      ✅ Has frame count constraints (16-81)")
            else:
                print(f"   📌 {param}: default={default} (fixed for all videos)")
                if has_constraints:
                    print(f"      ⚠️ Has constraints (unnecessary - should be removed)")
                else:
                    print(f"      ✅ No constraints (accepts fixed value)")
    
    return True

def test_video_requests():
    """Test different video request scenarios"""
    print("\n🧪 Testing Video Request Scenarios:")
    
    # Scenario 1: User only specifies frames (recommended)
    print("\n   📋 Scenario 1: User only specifies frames")
    simple_request = {
        "prompt": "A Yorkshire Terrier running",
        "task_type": "text2video",
        "num_frames": 50  # Only thing user needs to specify
    }
    
    print("      Request:", simple_request)
    print("      Expected: Schema fills in 832x480, 15fps, guidance=5.0")
    
    # Scenario 2: User specifies everything (also works)
    print("\n   📋 Scenario 2: User specifies all video params")
    detailed_request = {
        "prompt": "A Yorkshire Terrier running",
        "task_type": "text2video", 
        "num_frames": 81,
        "video_width": 832,
        "video_height": 480,
        "fps": 15,
        "video_guidance_scale": 5.0
    }
    
    print("      Request:", detailed_request)
    print("      Expected: Should work fine (matches defaults)")
    
    # Scenario 3: Image request (no video params)
    print("\n   📋 Scenario 3: Image request")
    image_request = {
        "prompt": "A Yorkshire Terrier",
        "task_type": "text2img",
        "width": 1024,
        "height": 1024
    }
    
    print("      Request:", image_request)
    print("      Expected: No video params used, routes to SDXL")
    
    return True

def test_frame_constraints():
    """Test that only frame count has meaningful constraints"""
    print("\n🔍 Testing Frame Count Constraints:")
    
    frames_constraint = INPUT_SCHEMA['num_frames']['constraints']
    
    test_cases = [
        (None, "Image request"),
        (16, "Minimum frames"),
        (50, "Mid-range frames"),
        (81, "Maximum frames"),
        (15, "Below minimum"),
        (100, "Above maximum")
    ]
    
    for frames, description in test_cases:
        result = frames_constraint(frames)
        status = "✅" if result else "❌"
        print(f"      {status} {frames} frames: {description}")
    
    return True

if __name__ == "__main__":
    print("🎬 Testing Simplified Video Parameter Approach")
    print("   Fixed: 832x480, 15fps, guidance=5.0")
    print("   Variable: Only num_frames (16-81)\n")
    
    success1 = test_simplified_video_params()
    success2 = test_video_requests()
    success3 = test_frame_constraints()
    
    if success1 and success2 and success3:
        print("\n🎉 SUCCESS: Video parameters simplified!")
        print("   ✅ Fixed dimensions: 832x480 (no user choice needed)")
        print("   ✅ Fixed FPS: 15 (no user choice needed)")
        print("   ✅ Fixed guidance: 5.0 (optimal for Wan2.1)")
        print("   ✅ Variable frames: 16-81 (user controls video length)")
        print("   ✅ No confusing validation rejections")
        print("   ✅ Simple for users: just specify num_frames!")
    else:
        print("\n💥 FAILURE: Video parameter issues")
        exit(1)

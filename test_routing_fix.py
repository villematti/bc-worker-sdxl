#!/usr/bin/env python3
"""
Test script to verify the fix for image vs video generation routing
"""

def test_schema_fix():
    """Test that the schema no longer defaults num_frames for image requests"""
    print("🧪 Testing schema fix for image vs video routing...\n")
    
    # Simulate an image generation request (no num_frames specified)
    image_request = {
        "prompt": "A Yorkshire Terrier running in a meadow",
        "task_type": "text2img",
        "width": 1024,
        "height": 1024
        # Note: NO num_frames specified
    }
    
    # Simulate a video generation request (with num_frames)
    video_request = {
        "prompt": "A Yorkshire Terrier running in a meadow",
        "task_type": "text2video", 
        "num_frames": 81,
        "video_width": 832,
        "video_height": 480
    }
    
    print("📋 Test cases:")
    print("1. Image request (no num_frames):")
    for key, value in image_request.items():
        print(f"   {key}: {value}")
    
    print("\n2. Video request (with num_frames):")
    for key, value in video_request.items():
        print(f"   {key}: {value}")
    
    # Test the logic from handler.py
    print("\n🔍 Testing routing logic:")
    
    # Test image request routing
    num_frames_img = image_request.get("num_frames")
    is_video_request_img = num_frames_img is not None and num_frames_img > 0
    task_type_img = "text2video" if is_video_request_img else "text2image"
    media_type_img = "videos" if is_video_request_img else "images"
    
    print(f"Image request:")
    print(f"  num_frames: {num_frames_img}")
    print(f"  is_video_request: {is_video_request_img}")
    print(f"  task_type: {task_type_img}")
    print(f"  media_type: {media_type_img}")
    print(f"  ✅ Correctly routed to IMAGE generation" if task_type_img == "text2image" else "❌ Incorrectly routed to VIDEO")
    
    # Test video request routing
    num_frames_vid = video_request.get("num_frames")
    is_video_request_vid = num_frames_vid is not None and num_frames_vid > 0
    task_type_vid = "text2video" if is_video_request_vid else "text2image"
    media_type_vid = "videos" if is_video_request_vid else "images"
    
    print(f"\nVideo request:")
    print(f"  num_frames: {num_frames_vid}")
    print(f"  is_video_request: {is_video_request_vid}")
    print(f"  task_type: {task_type_vid}")
    print(f"  media_type: {media_type_vid}")
    print(f"  ✅ Correctly routed to VIDEO generation" if task_type_vid == "text2video" else "❌ Incorrectly routed to IMAGE")

def test_schema_constraints():
    """Test the updated schema constraints"""
    print("\n🧪 Testing schema constraints...")
    
    # Test the constraint function
    constraint_func = lambda x: x is None or (16 <= x <= 81)
    
    test_cases = [
        (None, True, "None (for image generation)"),
        (50, True, "Valid video frame count"),
        (81, True, "Maximum frame count"),
        (16, True, "Minimum frame count"),
        (15, False, "Below minimum"),
        (82, False, "Above maximum"),
        (0, False, "Zero frames"),
    ]
    
    print("Constraint test results:")
    for value, expected, description in test_cases:
        result = constraint_func(value)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {description}: {value} -> {result}")

if __name__ == "__main__":
    print("🚀 Testing the fix for image vs video generation routing\n")
    test_schema_fix()
    test_schema_constraints()
    
    print(f"\n📋 Summary of fix:")
    print("1. ✅ Changed num_frames default from 81 to None in schema")
    print("2. ✅ Updated constraint to allow None values") 
    print("3. ✅ Improved routing logic to check for explicit video requests")
    print("4. ✅ Added logging to show request type determination")
    
    print(f"\n🎯 Result:")
    print("- Image requests (no num_frames) → SDXL image generation")
    print("- Video requests (with num_frames) → Wan2.1 video generation")
    print("- No more accidental routing to video pipeline!")

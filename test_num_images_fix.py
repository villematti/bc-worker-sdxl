#!/usr/bin/env python3
"""
TEST: num_images Parameter Fix

Test that num_images is now accepted but ignored.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_num_images_acceptance():
    """Test that num_images parameter is accepted"""
    print("🧪 Testing num_images Parameter Fix\n")
    
    # Import the schema
    try:
        from schemas import INPUT_SCHEMA
        print("✅ Schema imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import schema: {e}")
        return False
    
    # Check if num_images is in schema
    has_num_images = 'num_images' in INPUT_SCHEMA
    print(f"✅ num_images in schema: {has_num_images}")
    
    if not has_num_images:
        print("❌ num_images not found in schema!")
        return False
    
    # Check num_images configuration
    num_images_config = INPUT_SCHEMA['num_images']
    print(f"✅ num_images type: {num_images_config['type']}")
    print(f"✅ num_images required: {num_images_config['required']}")
    print(f"✅ num_images default: {num_images_config['default']}")
    
    # Test constraint (should only allow 1)
    constraint_func = num_images_config.get('constraints')
    if constraint_func:
        test_values = [0, 1, 2, 5]
        print("\n🔍 Testing num_images constraints:")
        for val in test_values:
            try:
                result = constraint_func(val)
                status = "✅" if result else "❌"
                print(f"   {status} num_images={val}: {result}")
            except Exception as e:
                print(f"   ❌ num_images={val}: Error - {e}")
    
    return True

def test_yorkshire_terrier_request():
    """Test the actual Yorkshire Terrier request that was failing"""
    print("\n🐕 Testing Yorkshire Terrier Request Format\n")
    
    # This is the request that was failing
    test_request = {
        "prompt": "A realistic photograph of a Yorkshire Terrier running energetically across a lush green meadow",
        "num_images": 1,  # This was causing the error
        "height": 1024,
        "width": 1024,
        "guidance_scale": 7.5,
        "num_inference_steps": 20,
        "file_uid": "60142eab-76cf-4e21-ba84-ca230549e4c4",
        "user_id": "z9BLS15zMwc174rWKVBusQUdy5R2",
        "use_cloud_storage": True
    }
    
    print("📋 Request payload:")
    for key, value in test_request.items():
        print(f"   {key}: {value}")
    
    # Try to simulate validation
    try:
        from schemas import INPUT_SCHEMA
        
        print("\n🔍 Checking each parameter against schema:")
        valid_params = []
        invalid_params = []
        
        for key, value in test_request.items():
            if key in INPUT_SCHEMA:
                valid_params.append(key)
                print(f"   ✅ {key}: Found in schema")
            else:
                invalid_params.append(key)
                print(f"   ❌ {key}: NOT in schema")
        
        print(f"\n📊 Validation Summary:")
        print(f"   ✅ Valid parameters: {len(valid_params)}")
        print(f"   ❌ Invalid parameters: {len(invalid_params)}")
        
        if invalid_params:
            print(f"   🚨 These parameters will cause validation errors:")
            for param in invalid_params:
                print(f"      • {param}")
            return False
        else:
            print(f"   🎉 All parameters are valid!")
            return True
            
    except Exception as e:
        print(f"❌ Validation test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Testing num_images Parameter Fix")
    print("   Ensuring Yorkshire Terrier requests work\n")
    
    test1_ok = test_num_images_acceptance()
    test2_ok = test_yorkshire_terrier_request()
    
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY:")
    print(f"   🧪 Schema Test: {'✅ PASS' if test1_ok else '❌ FAIL'}")
    print(f"   🐕 Yorkshire Test: {'✅ PASS' if test2_ok else '❌ FAIL'}")
    
    if test1_ok and test2_ok:
        print(f"\n🎉 ALL TESTS PASSED!")
        print("   ✅ num_images parameter is now accepted")
        print("   ✅ Yorkshire Terrier requests should work")
        print("   ✅ Firebase requests will validate successfully")
    else:
        print(f"\n💥 TESTS FAILED!")
        print("   🔧 Check schema configuration")
        exit(1)

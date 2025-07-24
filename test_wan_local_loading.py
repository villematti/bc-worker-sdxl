#!/usr/bin/env python3
"""
Test script to verify Wan2.1 local loading functionality
"""
import os
import sys

def test_local_loading():
    """Test the local loading logic"""
    print("🧪 Testing Wan2.1 local loading logic...")
    
    # Set environment variable
    os.environ["DOWNLOAD_WAN2_MODEL"] = "true"
    print(f"✅ Set DOWNLOAD_WAN2_MODEL = {os.environ.get('DOWNLOAD_WAN2_MODEL')}")
    
    # Test path checking
    local_path = "/runpod-volume/Wan2.1-T2V-1.3B-Diffusers"
    print(f"🔍 Checking local path: {local_path}")
    
    if os.path.exists(local_path):
        print("✅ Local Wan2.1 model found - will use local loading")
        
        # Check for required subfolders
        required_folders = ["vae", "transformer", "scheduler", "text_encoder", "tokenizer", "feature_extractor"]
        missing_folders = []
        
        for folder in required_folders:
            folder_path = os.path.join(local_path, folder)
            if os.path.exists(folder_path):
                print(f"  ✅ Found: {folder}/")
            else:
                print(f"  ❌ Missing: {folder}/")
                missing_folders.append(folder)
        
        if missing_folders:
            print(f"⚠️ Warning: Missing folders: {missing_folders}")
        else:
            print("✅ All required model folders found!")
            
    else:
        print("❌ Local model not found - will download from HuggingFace")
        print("📁 Expected structure:")
        print(f"   {local_path}/")
        print("   ├── model_index.json")
        print("   ├── vae/")
        print("   ├── transformer/")
        print("   ├── scheduler/")
        print("   ├── text_encoder/")
        print("   ├── tokenizer/")
        print("   └── feature_extractor/")

def test_import_logic():
    """Test that our imports work correctly"""
    print("\n🧪 Testing import functionality...")
    
    try:
        # Test download_weights imports
        print("📦 Testing download_weights.py imports...")
        from download_weights import get_diffusion_pipelines
        print("  ✅ download_weights imports successful")
        
        # Test handler imports  
        print("📦 Testing handler.py imports...")
        from handler import load_wan_from_local_or_hub
        print("  ✅ handler imports successful")
        
        print("✅ All imports working correctly!")
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Starting Wan2.1 local loading tests...\n")
    
    # Test imports first
    if not test_import_logic():
        print("💥 Import tests failed - stopping")
        sys.exit(1)
    
    # Test local loading logic
    test_local_loading()
    
    print("\n✅ Test completed!")
    print("\n📋 Summary of changes made:")
    print("1. ✅ Updated download_weights.py to check local path first")
    print("2. ✅ Updated handler.py with helper function and new loading logic")
    print("3. ✅ Enabled DOWNLOAD_WAN2_MODEL=true in Dockerfile")
    print("4. ✅ Added fallback to HuggingFace if local model not found")
    print("5. ✅ Used local_files_only=True for local loading")
    
    print("\n🔧 Next steps:")
    print("1. Ensure your RunPod volume has the model at: /runpod-volume/Wan2.1-T2V-1.3B-Diffusers")
    print("2. Build and deploy your container")
    print("3. Test with a video generation request")

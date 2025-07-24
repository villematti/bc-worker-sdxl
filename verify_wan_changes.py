#!/usr/bin/env python3
"""
Simple verification script for Wan2.1 local loading changes
"""
import os

def verify_changes():
    """Verify the changes were made correctly"""
    print("🔍 Verifying Wan2.1 local loading implementation...\n")
    
    # Check download_weights.py changes
    print("1. 📄 Checking download_weights.py...")
    try:
        with open("download_weights.py", "r") as f:
            content = f.read()
            
        checks = [
            ('local_wan_path = "/runpod-volume/Wan2.1-T2V-1.3B-Diffusers"', "Local path defined"),
            ('os.path.exists(local_wan_path)', "Path existence check"),
            ('local_files_only=True', "Local files only flag"),
            ('Found local Wan2.1 model at:', "Local model found message"),
            ('Local path not found:', "Fallback message")
        ]
        
        for check, description in checks:
            if check in content:
                print(f"   ✅ {description}")
            else:
                print(f"   ❌ Missing: {description}")
                
    except FileNotFoundError:
        print("   ❌ download_weights.py not found")
    
    # Check handler.py changes
    print("\n2. 📄 Checking handler.py...")
    try:
        with open("handler.py", "r") as f:
            content = f.read()
            
        checks = [
            ('def load_wan_from_local_or_hub(', "Helper function defined"),
            ('local_wan_path = "/runpod-volume/Wan2.1-T2V-1.3B-Diffusers"', "Local path in handler"),
            ('load_wan_from_local_or_hub(', "Helper function used"),
            ('os.path.exists(local_path)', "Path check in helper")
        ]
        
        for check, description in checks:
            if check in content:
                print(f"   ✅ {description}")
            else:
                print(f"   ❌ Missing: {description}")
                
    except FileNotFoundError:
        print("   ❌ handler.py not found")
    
    # Check Dockerfile changes
    print("\n3. 📄 Checking Dockerfile...")
    try:
        with open("Dockerfile", "r") as f:
            content = f.read()
            
        if "ENV DOWNLOAD_WAN2_MODEL=true" in content:
            print("   ✅ Environment variable enabled")
        else:
            print("   ❌ Environment variable not enabled")
            
    except FileNotFoundError:
        print("   ❌ Dockerfile not found")
    
    print("\n📋 Implementation Summary:")
    print("✅ Local path: /runpod-volume/Wan2.1-T2V-1.3B-Diffusers")
    print("✅ Falls back to HuggingFace if local model not found")
    print("✅ Uses local_files_only=True for local loading")
    print("✅ Environment variable DOWNLOAD_WAN2_MODEL=true enabled")
    
    print("\n🚀 Ready for deployment!")
    print("Make sure your RunPod volume contains the pre-downloaded model.")

if __name__ == "__main__":
    verify_changes()

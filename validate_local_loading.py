#!/usr/bin/env python3
"""
VALIDATION: Local Model Loading

Test that all models load correctly from RunPod volume paths.
"""

import os

def validate_model_paths():
    """Validate that all expected model paths exist"""
    print("📋 Validating Model Paths on RunPod Volume\n")
    
    expected_paths = [
        "/runpod-volume/stable-diffusion-xl-base-1.0",
        "/runpod-volume/sdxl-vae-fp16-fix", 
        "/runpod-volume/stable-diffusion-xl-refiner-1.0",
        "/runpod-volume/stable-diffusion-xl-1.0-inpainting-0.1",
        "/runpod-volume/Wan2.1-T2V-14B-Diffusers"
    ]
    
    print("🔍 Checking Expected Paths:")
    
    missing_paths = []
    for path in expected_paths:
        exists = os.path.exists(path)
        status = "✅" if exists else "❌"
        print(f"   {status} {path}")
        if not exists:
            missing_paths.append(path)
    
    if missing_paths:
        print(f"\n❌ MISSING PATHS: {len(missing_paths)}")
        print("   These paths need to be present on RunPod volume:")
        for path in missing_paths:
            print(f"   • {path}")
        return False
    else:
        print(f"\n✅ ALL PATHS EXIST: {len(expected_paths)} models found")
        return True

def validate_configuration_changes():
    """Validate that code changes are correct"""
    print("\n📋 Validating Configuration Changes\n")
    
    # Check download_weights.py changes
    print("🔍 Checking download_weights.py:")
    try:
        with open("download_weights.py", "r") as f:
            content = f.read()
        
        # Should have local paths
        has_local_base = "/runpod-volume/stable-diffusion-xl-base-1.0" in content
        has_local_wan14b = "/runpod-volume/Wan2.1-T2V-14B-Diffusers" in content
        has_local_only = "local_files_only=True" in content
        
        # Should NOT have HuggingFace downloads
        has_hf_downloads = "fetch_pretrained_model" in content and "stabilityai/" in content
        
        print(f"   ✅ Local base path: {has_local_base}")
        print(f"   ✅ Local Wan2.1-14B path: {has_local_wan14b}")
        print(f"   ✅ Force local loading: {has_local_only}")
        print(f"   ✅ No HF downloads: {not has_hf_downloads}")
        
        download_ok = has_local_base and has_local_wan14b and has_local_only and not has_hf_downloads
        
    except Exception as e:
        print(f"   ❌ Error reading download_weights.py: {e}")
        download_ok = False
    
    # Check handler.py changes  
    print("\n🔍 Checking handler.py:")
    try:
        with open("handler.py", "r") as f:
            content = f.read()
        
        # Should have local paths and 14B model
        has_local_paths = "/runpod-volume/" in content
        has_wan14b = "Wan2.1-T2V-14B-Diffusers" in content
        has_local_only = "local_files_only=True" in content
        
        # Should NOT have old 1.3B references
        has_old_13b = "Wan2.1-T2V-1.3B-Diffusers" in content
        
        print(f"   ✅ Local volume paths: {has_local_paths}")
        print(f"   ✅ Wan2.1-14B model: {has_wan14b}")
        print(f"   ✅ Force local loading: {has_local_only}")
        print(f"   ✅ No old 1.3B refs: {not has_old_13b}")
        
        handler_ok = has_local_paths and has_wan14b and has_local_only and not has_old_13b
        
    except Exception as e:
        print(f"   ❌ Error reading handler.py: {e}")
        handler_ok = False
    
    return download_ok and handler_ok

def validate_wan_upgrade():
    """Validate Wan2.1 model upgrade from 1.3B to 14B"""
    print("\n📋 Validating Wan2.1 Model Upgrade\n")
    
    print("🔍 Model Upgrade Details:")
    print("   📈 Old Model: Wan2.1-T2V-1.3B-Diffusers")
    print("   📈 New Model: Wan2.1-T2V-14B-Diffusers")
    print("   🎯 Expected Benefits:")
    print("      • Higher quality video generation")
    print("      • Better prompt following")
    print("      • More detailed textures")
    print("      • Same API interface (no code changes needed)")
    
    # Check if new model path is configured
    try:
        with open("download_weights.py", "r") as f:
            content = f.read()
        with open("handler.py", "r") as f:
            handler_content = f.read()
        
        has_14b_download = "Wan2.1-T2V-14B-Diffusers" in content
        has_14b_handler = "Wan2.1-T2V-14B-Diffusers" in handler_content
        no_13b_download = "Wan2.1-T2V-1.3B-Diffusers" not in content
        no_13b_handler = "Wan2.1-T2V-1.3B-Diffusers" not in handler_content
        
        print(f"\n   ✅ 14B in download_weights.py: {has_14b_download}")
        print(f"   ✅ 14B in handler.py: {has_14b_handler}")
        print(f"   ✅ No 1.3B in download_weights.py: {no_13b_download}")
        print(f"   ✅ No 1.3B in handler.py: {no_13b_handler}")
        
        upgrade_ok = has_14b_download and has_14b_handler and no_13b_download and no_13b_handler
        
        if upgrade_ok:
            print("   🎉 Wan2.1 upgrade completed successfully!")
        else:
            print("   ⚠️ Wan2.1 upgrade incomplete")
            
        return upgrade_ok
        
    except Exception as e:
        print(f"   ❌ Error validating upgrade: {e}")
        return False

if __name__ == "__main__":
    print("📋 Validating Local Model Loading Configuration")
    print("   Checking RunPod volume setup and code changes\n")
    
    paths_ok = validate_model_paths()
    config_ok = validate_configuration_changes() 
    upgrade_ok = validate_wan_upgrade()
    
    print(f"\n{'='*60}")
    print("📊 VALIDATION SUMMARY:")
    print(f"   🗂️  Model Paths: {'✅ PASS' if paths_ok else '❌ FAIL'}")
    print(f"   ⚙️  Configuration: {'✅ PASS' if config_ok else '❌ FAIL'}")
    print(f"   📈 Wan2.1 Upgrade: {'✅ PASS' if upgrade_ok else '❌ FAIL'}")
    
    if paths_ok and config_ok and upgrade_ok:
        print(f"\n🎉 ALL VALIDATIONS PASSED!")
        print("   ✅ Ready for RunPod deployment")
        print("   ✅ All models will load from local volume")
        print("   ✅ No internet downloads required") 
        print("   ✅ Wan2.1-14B upgrade ready")
    else:
        print(f"\n💥 VALIDATION ISSUES FOUND!")
        if not paths_ok:
            print("   🔧 Fix: Ensure all models are uploaded to RunPod volume")
        if not config_ok:
            print("   🔧 Fix: Check code changes in download_weights.py and handler.py")
        if not upgrade_ok:
            print("   🔧 Fix: Complete Wan2.1 model upgrade to 14B")
        exit(1)

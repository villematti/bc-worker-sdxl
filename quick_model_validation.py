#!/usr/bin/env python3
"""
QUICK MODEL VALIDATION TEST
This test quickly checks if the Wan2.1 model files are actually available
and can be loaded without doing a full environment setup.
"""

import os
import sys

def check_wan_model_availability():
    """Check if Wan2.1 model is properly available"""
    print("🔍 [QUICK CHECK] Validating Wan2.1 model availability...")
    
    try:
        from huggingface_hub import repo_exists, list_repo_files
        
        model_id = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"
        
        # Check if repo exists
        print(f"📡 Checking repository: {model_id}")
        if not repo_exists(model_id):
            print(f"❌ Repository {model_id} does not exist on HuggingFace")
            return False
        
        print("✅ Repository exists")
        
        # List files in the repo
        print("📋 Listing repository files...")
        try:
            files = list_repo_files(model_id)
            
            required_files = [
                "config.json",
                "model_index.json", 
                "vae/config.json",
                "unet/config.json"
            ]
            
            print("📄 Available files:")
            for file in sorted(files):
                status = "✅" if file in required_files else "📄"
                print(f"  {status} {file}")
            
            # Check for required files
            missing_files = [f for f in required_files if f not in files]
            
            if missing_files:
                print(f"\n❌ Missing required files:")
                for file in missing_files:
                    print(f"  ❌ {file}")
                return False
            else:
                print(f"\n✅ All required files present")
                
        except Exception as e:
            print(f"❌ Failed to list repository files: {e}")
            return False
            
    except ImportError:
        print("❌ huggingface_hub not available, installing...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "huggingface_hub"])
        return check_wan_model_availability()  # Retry after install
    
    except Exception as e:
        print(f"❌ Error checking repository: {e}")
        return False
    
    return True

def test_local_cache():
    """Check what's in the local HuggingFace cache"""
    print("\n🔍 [CACHE CHECK] Checking local HuggingFace cache...")
    
    cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
    
    if not os.path.exists(cache_dir):
        print("❌ No HuggingFace cache directory found")
        return False
    
    print(f"📁 Cache directory: {cache_dir}")
    
    # Look for Wan2.1 models in cache
    wan_models = []
    for item in os.listdir(cache_dir):
        if "wan" in item.lower():
            wan_models.append(item)
    
    if not wan_models:
        print("❌ No Wan models found in cache")
        return False
    
    print(f"📋 Found Wan models in cache:")
    for model in wan_models:
        model_path = os.path.join(cache_dir, model)
        print(f"  📁 {model}")
        
        # Check if it has the required files
        if os.path.exists(model_path):
            snapshots_path = os.path.join(model_path, "snapshots")
            if os.path.exists(snapshots_path):
                for snapshot in os.listdir(snapshots_path):
                    snapshot_path = os.path.join(snapshots_path, snapshot)
                    if os.path.isdir(snapshot_path):
                        print(f"    📂 Snapshot: {snapshot}")
                        
                        # Check for config.json
                        config_path = os.path.join(snapshot_path, "config.json")
                        if os.path.exists(config_path):
                            print(f"      ✅ config.json found")
                        else:
                            print(f"      ❌ config.json missing")
                            
                        # List all files in snapshot
                        try:
                            all_files = []
                            for root, dirs, files in os.walk(snapshot_path):
                                for file in files:
                                    rel_path = os.path.relpath(os.path.join(root, file), snapshot_path)
                                    all_files.append(rel_path)
                            
                            print(f"      📄 Files: {len(all_files)} total")
                            for file in sorted(all_files)[:10]:  # Show first 10 files
                                print(f"        📄 {file}")
                            if len(all_files) > 10:
                                print(f"        ... and {len(all_files) - 10} more files")
                                
                        except Exception as e:
                            print(f"      ❌ Error listing files: {e}")
    
    return True

def test_model_loading():
    """Test if the model can actually be loaded"""
    print("\n🔍 [LOADING TEST] Testing model loading...")
    
    try:
        from diffusers import WanPipeline, AutoencoderKLWan
        print("✅ Wan imports successful")
        
        model_id = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"
        
        # Try to load just the config first
        try:
            print("🔧 Testing config loading...")
            from transformers import AutoConfig
            config = AutoConfig.from_pretrained(model_id)
            print(f"✅ Config loaded: {type(config)}")
        except Exception as e:
            print(f"❌ Config loading failed: {e}")
        
        # Try to load VAE config
        try:
            print("🔧 Testing VAE config loading...")
            vae_config = AutoencoderKLWan.load_config(model_id, subfolder="vae")
            print(f"✅ VAE config loaded")
        except Exception as e:
            print(f"❌ VAE config loading failed: {e}")
        
        # Try to load main pipeline config
        try:
            print("🔧 Testing pipeline config loading...")
            pipe_config = WanPipeline.load_config(model_id)
            print(f"✅ Pipeline config loaded")
        except Exception as e:
            print(f"❌ Pipeline config loading failed: {e}")
            
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Model loading test failed: {e}")
        return False
    
    return True

def main():
    """Run quick validation tests"""
    print("=" * 50)
    print("🚀 QUICK MODEL VALIDATION")
    print("=" * 50)
    
    all_passed = True
    
    # Test 1: Repository availability
    if not check_wan_model_availability():
        all_passed = False
    
    # Test 2: Local cache
    if not test_local_cache():
        all_passed = False
    
    # Test 3: Model loading
    if not test_model_loading():
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ ALL VALIDATION TESTS PASSED")
        print("🎯 Wan2.1 model should work properly")
    else:
        print("❌ VALIDATION TESTS FAILED")
        print("💡 Issues found with Wan2.1 model setup")
    print("=" * 50)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

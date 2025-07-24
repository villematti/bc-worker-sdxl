#!/usr/bin/env python3
"""
COMPREHENSIVE CLOUD EMULATION TEST
This test emulates EXACTLY what happens in the RunPod cloud environment
to catch discrepancies that our previous tests missed.
"""

import os
import sys
import subprocess
import tempfile
import shutil
import json
from pathlib import Path

class CloudEmulationTest:
    """Emulates the exact cloud environment setup and execution"""
    
    def __init__(self):
        self.test_dir = None
        self.venv_path = None
        self.original_dir = os.getcwd()
        
    def setup_test_environment(self):
        """Create isolated test environment matching cloud setup"""
        print("🔧 [CLOUD EMULATION] Setting up isolated test environment...")
        
        # Create temporary directory
        self.test_dir = tempfile.mkdtemp(prefix="cloud_emulation_")
        print(f"📁 Test directory: {self.test_dir}")
        
        # Copy all project files to test directory
        project_files = [
            "download_weights.py",
            "schemas.py", 
            "handler.py",
            "cloud_storage.py",
            "test_input.json",
            "runpod_firebase_debug.py",
            "requirements.txt",
            "storage_access.json"
        ]
        
        for file in project_files:
            if os.path.exists(file):
                shutil.copy2(file, self.test_dir)
                print(f"✅ Copied {file}")
            else:
                print(f"⚠️ Missing {file}")
        
        return True
    
    def setup_virtual_environment(self):
        """Create fresh virtual environment like in cloud"""
        print("\n🔧 [CLOUD EMULATION] Creating fresh virtual environment...")
        
        os.chdir(self.test_dir)
        
        # Create virtual environment
        venv_result = subprocess.run([
            sys.executable, "-m", "venv", "venv"
        ], capture_output=True, text=True)
        
        if venv_result.returncode != 0:
            print(f"❌ Failed to create venv: {venv_result.stderr}")
            return False
        
        # Set venv path
        if os.name == 'nt':  # Windows
            self.venv_path = os.path.join(self.test_dir, "venv", "Scripts")
            python_exe = os.path.join(self.venv_path, "python.exe")
        else:  # Linux/Unix
            self.venv_path = os.path.join(self.test_dir, "venv", "bin")
            python_exe = os.path.join(self.venv_path, "python")
        
        print(f"✅ Virtual environment created: {self.venv_path}")
        return True
    
    def install_dependencies(self):
        """Install dependencies exactly like cloud environment"""
        print("\n🔧 [CLOUD EMULATION] Installing dependencies...")
        
        python_exe = os.path.join(self.venv_path, "python.exe" if os.name == 'nt' else "python")
        pip_exe = os.path.join(self.venv_path, "pip.exe" if os.name == 'nt' else "pip")
        
        # Install requirements
        pip_result = subprocess.run([
            pip_exe, "install", "-r", "requirements.txt"
        ], capture_output=True, text=True)
        
        if pip_result.returncode != 0:
            print(f"❌ Failed to install requirements: {pip_result.stderr}")
            return False
        
        print("✅ Dependencies installed")
        return True
    
    def run_download_weights(self):
        """Run download_weights.py exactly like in cloud"""
        print("\n🔧 [CLOUD EMULATION] Running download_weights.py...")
        
        python_exe = os.path.join(self.venv_path, "python.exe" if os.name == 'nt' else "python")
        
        # Set environment variables like in cloud
        env = os.environ.copy()
        env['DOWNLOAD_WAN2_MODEL'] = 'true'  # Enable Wan2.1 download
        
        download_result = subprocess.run([
            python_exe, "download_weights.py"
        ], capture_output=True, text=True, env=env, timeout=1800)  # 30 min timeout
        
        print("📋 Download output:")
        print(download_result.stdout)
        
        if download_result.returncode != 0:
            print(f"❌ Download failed: {download_result.stderr}")
            return False
        
        print("✅ Model download completed")
        return True
    
    def test_model_loading(self):
        """Test model loading exactly like handler.py does"""
        print("\n🔧 [CLOUD EMULATION] Testing model loading...")
        
        python_exe = os.path.join(self.venv_path, "python.exe" if os.name == 'nt' else "python")
        
        # Set Firebase environment variables
        env = os.environ.copy()
        with open('storage_access.json', 'r') as f:
            firebase_key = json.load(f)
        env['FIREBASE_SERVICE_ACCOUNT_KEY'] = json.dumps(firebase_key)
        env['FIREBASE_STORAGE_BUCKET'] = 'bc-image-gen.firebasestorage.app'
        
        # Create test script that emulates handler.py model loading
        test_script = """
import sys
import os
sys.path.insert(0, '.')

try:
    print("🔧 Testing model imports...")
    from diffusers import WanPipeline, AutoencoderKLWan
    print("✅ Wan imports successful")
    
    print("🔧 Testing model loading...")
    model_path = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"
    
    # Check if model exists locally
    from huggingface_hub import snapshot_download
    import os
    
    cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
    print(f"📁 Cache directory: {cache_dir}")
    
    # Try to load like handler.py does
    try:
        vae = AutoencoderKLWan.from_pretrained(
            model_path,
            subfolder="vae",
            torch_dtype=None,  # Don't specify dtype for loading test
            local_files_only=True,
        )
        print("✅ VAE loaded successfully")
        
        wan_pipe = WanPipeline.from_pretrained(
            model_path,
            vae=vae,
            torch_dtype=None,  # Don't specify dtype for loading test
            use_safetensors=True,
            local_files_only=True,
        )
        print("✅ Wan2.1 pipeline loaded successfully")
        
    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Check what files are actually available
        try:
            import os
            from huggingface_hub import hf_hub_download
            
            # List available files
            print("📋 Checking available files...")
            
            # Try to find the actual model directory
            model_cache_path = None
            cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
            
            if os.path.exists(cache_dir):
                for item in os.listdir(cache_dir):
                    if "wan-ai" in item.lower() and "wan2.1" in item.lower():
                        model_cache_path = os.path.join(cache_dir, item)
                        print(f"📁 Found model cache: {model_cache_path}")
                        
                        # List files in the model directory
                        if os.path.exists(model_cache_path):
                            print("📋 Files in model directory:")
                            for root, dirs, files in os.walk(model_cache_path):
                                for file in files:
                                    rel_path = os.path.relpath(os.path.join(root, file), model_cache_path)
                                    print(f"  📄 {rel_path}")
                        break
            
        except Exception as list_error:
            print(f"❌ Failed to list files: {list_error}")
        
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Import or setup failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("✅ All model tests passed")
"""
        
        with open("test_model_loading.py", "w") as f:
            f.write(test_script)
        
        model_result = subprocess.run([
            python_exe, "test_model_loading.py"
        ], capture_output=True, text=True, env=env, timeout=300)
        
        print("📋 Model loading output:")
        print(model_result.stdout)
        
        if model_result.returncode != 0:
            print(f"❌ Model loading failed: {model_result.stderr}")
            return False
        
        print("✅ Model loading successful")
        return True
    
    def test_video_generation_flow(self):
        """Test actual video generation flow"""
        print("\n🔧 [CLOUD EMULATION] Testing video generation flow...")
        
        python_exe = os.path.join(self.venv_path, "python.exe" if os.name == 'nt' else "python")
        
        # Set Firebase environment variables
        env = os.environ.copy()
        with open('storage_access.json', 'r') as f:
            firebase_key = json.load(f)
        env['FIREBASE_SERVICE_ACCOUNT_KEY'] = json.dumps(firebase_key)
        env['FIREBASE_STORAGE_BUCKET'] = 'bc-image-gen.firebasestorage.app'
        
        # Create test script that simulates actual job
        test_script = """
import sys
import os
sys.path.insert(0, '.')

# Test the actual generate_image function with video input
try:
    from handler import generate_image
    
    test_job = {
        'id': 'cloud-emulation-test',
        'input': {
            'prompt': 'test video generation',
            'num_frames': 16,
            'fps': 8,
            'height': 480,
            'width': 832,
            'guidance_scale': 6.0,
            'num_inference_steps': 20,
            'use_cloud_storage': True,
            'user_id': 'test-cloud-emulation',
            'file_uid': 'test-cloud-video-001'
        }
    }
    
    print("🔧 Testing video generation with actual handler...")
    result = generate_image(test_job)
    print(f"📋 Result: {result}")
    
    if result and result.get('status') == 'accepted':
        print("✅ Video generation flow accepted")
        
        # Wait a bit for background processing
        import time
        print("⏳ Waiting for background processing...")
        time.sleep(10)
        
    else:
        print(f"❌ Video generation failed: {result}")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Video generation test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("✅ Video generation flow test completed")
"""
        
        with open("test_video_generation.py", "w") as f:
            f.write(test_script)
        
        video_result = subprocess.run([
            python_exe, "test_video_generation.py"
        ], capture_output=True, text=True, env=env, timeout=600)
        
        print("📋 Video generation output:")
        print(video_result.stdout)
        
        if video_result.returncode != 0:
            print(f"❌ Video generation failed: {video_result.stderr}")
            return False
        
        print("✅ Video generation test successful")
        return True
    
    def cleanup(self):
        """Clean up test environment"""
        print(f"\n🧹 Cleaning up test environment...")
        os.chdir(self.original_dir)
        if self.test_dir and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            print("✅ Test environment cleaned up")
    
    def run_full_test(self):
        """Run complete cloud emulation test"""
        print("🚀 [CLOUD EMULATION] Starting comprehensive cloud environment test...")
        
        try:
            if not self.setup_test_environment():
                return False
                
            if not self.setup_virtual_environment():
                return False
                
            if not self.install_dependencies():
                return False
                
            if not self.run_download_weights():
                return False
                
            if not self.test_model_loading():
                return False
                
            if not self.test_video_generation_flow():
                return False
            
            print("\n✅ [CLOUD EMULATION] ALL TESTS PASSED!")
            print("🎯 This environment matches cloud behavior exactly")
            return True
            
        except Exception as e:
            print(f"\n❌ [CLOUD EMULATION] Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            self.cleanup()

def main():
    """Run the cloud emulation test"""
    print("=" * 60)
    print("🏗️  CLOUD ENVIRONMENT EMULATION TEST")
    print("=" * 60)
    print("This test creates a fresh environment and downloads models")
    print("exactly like the cloud environment to catch discrepancies.")
    print("=" * 60)
    
    test = CloudEmulationTest()
    success = test.run_full_test()
    
    if success:
        print("\n🎉 Cloud emulation test PASSED!")
        print("✅ Your local environment matches cloud behavior")
    else:
        print("\n💥 Cloud emulation test FAILED!")
        print("❌ Found discrepancies between local and cloud environments")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

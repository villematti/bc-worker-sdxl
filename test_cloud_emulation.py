#!/usr/bin/env python3
"""
COMPREHENSIVE CLOUD EMULATION TEST SUITE
This test emulates the EXACT cloud environment to catch deployment issues locally
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import subprocess
import importlib.util

# Test configuration
TEST_RESULTS = []
FAILED_TESTS = []

def log_test(test_name, status, details=""):
    """Log test results"""
    TEST_RESULTS.append({
        "test": test_name,
        "status": status,
        "details": details
    })
    
    status_emoji = "✅" if status == "PASS" else "❌"
    print(f"{status_emoji} {test_name}: {details}")
    
    if status == "FAIL":
        FAILED_TESTS.append(test_name)

def test_huggingface_model_availability():
    """Test if Hugging Face models are actually accessible with all required files"""
    print("\n🔧 [TEST] Hugging Face Model Availability")
    
    models_to_test = [
        "stabilityai/stable-diffusion-xl-base-1.0",
        "stabilityai/stable-diffusion-xl-refiner-1.0", 
        "diffusers/stable-diffusion-xl-1.0-inpainting-0.1",
        "madebyollin/sdxl-vae-fp16-fix",
        "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"  # The problematic one
    ]
    
    try:
        from huggingface_hub import repo_exists, list_repo_files
        
        for model_id in models_to_test:
            try:
                # Check if repo exists
                if not repo_exists(model_id):
                    log_test(f"HF_MODEL_{model_id.replace('/', '_')}", "FAIL", f"Repository does not exist")
                    continue
                
                # List all files in the repo
                try:
                    files = list(list_repo_files(model_id))
                    
                    # Check for essential files
                    required_files = ["config.json"]
                    missing_files = [f for f in required_files if f not in files]
                    
                    if missing_files:
                        log_test(f"HF_MODEL_{model_id.replace('/', '_')}", "FAIL", 
                               f"Missing required files: {missing_files}")
                    else:
                        log_test(f"HF_MODEL_{model_id.replace('/', '_')}", "PASS", 
                               f"All required files present ({len(files)} total files)")
                        
                except Exception as e:
                    log_test(f"HF_MODEL_{model_id.replace('/', '_')}", "FAIL", 
                           f"Could not list files: {e}")
                    
            except Exception as e:
                log_test(f"HF_MODEL_{model_id.replace('/', '_')}", "FAIL", f"Error checking repo: {e}")
                
    except ImportError:
        log_test("HF_MODEL_CHECK", "FAIL", "huggingface_hub not available")

def test_download_weights_simulation():
    """Simulate the download_weights.py execution exactly as in Docker"""
    print("\n🔧 [TEST] Download Weights Simulation")
    
    try:
        # Import and run download_weights.py
        spec = importlib.util.spec_from_file_location("download_weights", "download_weights.py")
        download_module = importlib.util.module_from_spec(spec)
        
        # Capture any exceptions during download
        try:
            spec.loader.exec_module(download_module)
            log_test("DOWNLOAD_WEIGHTS", "PASS", "download_weights.py executed successfully")
        except Exception as e:
            log_test("DOWNLOAD_WEIGHTS", "FAIL", f"download_weights.py failed: {e}")
            
    except Exception as e:
        log_test("DOWNLOAD_WEIGHTS", "FAIL", f"Could not import download_weights.py: {e}")

def test_model_loading_exact_cloud_simulation():
    """Test model loading exactly as it happens in the cloud"""
    print("\n🔧 [TEST] Model Loading (Cloud Simulation)")
    
    try:
        # Import handler to test ModelHandler
        spec = importlib.util.spec_from_file_location("handler", "handler.py")
        handler_module = importlib.util.module_from_spec(spec)
        
        # Set environment to simulate cloud
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"  # Simulate single GPU
        
        try:
            spec.loader.exec_module(handler_module)
            
            # Test ModelHandler initialization
            try:
                model_handler = handler_module.ModelHandler()
                
                # Check each model component
                if model_handler.base is not None:
                    log_test("MODEL_SDXL_BASE", "PASS", "SDXL base model loaded")
                else:
                    log_test("MODEL_SDXL_BASE", "FAIL", "SDXL base model failed to load")
                    
                if model_handler.refiner is not None:
                    log_test("MODEL_SDXL_REFINER", "PASS", "SDXL refiner model loaded")
                else:
                    log_test("MODEL_SDXL_REFINER", "FAIL", "SDXL refiner model failed to load")
                    
                if model_handler.inpaint is not None:
                    log_test("MODEL_SDXL_INPAINT", "PASS", "SDXL inpaint model loaded")
                else:
                    log_test("MODEL_SDXL_INPAINT", "FAIL", "SDXL inpaint model failed to load")
                    
                # THE CRITICAL TEST - Wan2.1
                if model_handler.wan_t2v is not None:
                    log_test("MODEL_WAN2_T2V", "PASS", "Wan2.1 T2V model loaded successfully")
                else:
                    log_test("MODEL_WAN2_T2V", "FAIL", "Wan2.1 T2V model failed to load - VIDEO GENERATION WILL NOT WORK")
                    
            except Exception as e:
                log_test("MODEL_HANDLER_INIT", "FAIL", f"ModelHandler initialization failed: {e}")
                
        except Exception as e:
            log_test("HANDLER_IMPORT", "FAIL", f"Could not execute handler.py: {e}")
            
    except Exception as e:
        log_test("HANDLER_IMPORT", "FAIL", f"Could not import handler.py: {e}")

def test_cloud_storage_simulation():
    """Test cloud storage exactly as in production"""
    print("\n🔧 [TEST] Cloud Storage Simulation")
    
    # Set up real Firebase credentials
    try:
        with open('storage_access.json', 'r') as f:
            service_account_data = json.load(f)
        
        os.environ['FIREBASE_SERVICE_ACCOUNT_KEY'] = json.dumps(service_account_data)
        os.environ['FIREBASE_STORAGE_BUCKET'] = 'bc-image-gen.firebasestorage.app'
        
        # Force reload cloud_storage module
        if 'cloud_storage' in sys.modules:
            importlib.reload(sys.modules['cloud_storage'])
        
        from cloud_storage import cloud_storage
        
        if cloud_storage.storage_type == "firebase":
            log_test("FIREBASE_INIT", "PASS", "Firebase initialized successfully")
            
            # Test actual upload
            try:
                from PIL import Image
                from io import BytesIO
                
                test_image = Image.new('RGB', (10, 10), color='red')
                img_buffer = BytesIO()
                test_image.save(img_buffer, format='PNG')
                img_bytes = img_buffer.getvalue()
                
                test_url = cloud_storage.upload_file(
                    file_data=img_bytes,
                    filename="cloud_test.png",
                    content_type="image/png",
                    user_id="test-cloud-sim",
                    file_uid="test-upload-001"
                )
                
                if test_url.startswith("https://"):
                    log_test("FIREBASE_UPLOAD", "PASS", f"File uploaded successfully: {test_url}")
                else:
                    log_test("FIREBASE_UPLOAD", "FAIL", "Upload returned base64 fallback instead of Firebase URL")
                    
            except Exception as e:
                log_test("FIREBASE_UPLOAD", "FAIL", f"Upload test failed: {e}")
                
        else:
            log_test("FIREBASE_INIT", "FAIL", f"Firebase not initialized, type: {cloud_storage.storage_type}")
            
    except Exception as e:
        log_test("FIREBASE_INIT", "FAIL", f"Firebase initialization failed: {e}")

def test_full_generation_pipeline():
    """Test the complete generation pipeline with both image and video requests"""
    print("\n🔧 [TEST] Full Generation Pipeline")
    
    test_jobs = [
        {
            "name": "IMAGE_GENERATION",
            "input": {
                "prompt": "a red car",
                "use_cloud_storage": True,
                "user_id": "test-user-pipeline",
                "file_uid": "test-image-001",
                "num_inference_steps": 5,  # Fast test
                "guidance_scale": 7.5,
                "width": 512,
                "height": 512
            }
        },
        {
            "name": "VIDEO_GENERATION", 
            "input": {
                "prompt": "a red car driving",
                "use_cloud_storage": True,
                "user_id": "test-user-pipeline",
                "file_uid": "test-video-001",
                "num_frames": 16,  # This should trigger video generation
                "fps": 8,
                "video_height": 480,
                "video_width": 832
            }
        }
    ]
    
    try:
        # Import handler
        spec = importlib.util.spec_from_file_location("handler", "handler.py")
        handler_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(handler_module)
        
        for test_job in test_jobs:
            try:
                job = {
                    "id": f"test-job-{test_job['name'].lower()}",
                    "input": test_job["input"]
                }
                
                result = handler_module.generate_image(job)
                
                if "error" in result:
                    log_test(f"PIPELINE_{test_job['name']}", "FAIL", f"Generation failed: {result['error']}")
                elif result.get("status") == "accepted":
                    log_test(f"PIPELINE_{test_job['name']}", "PASS", "Generation accepted (async)")
                else:
                    log_test(f"PIPELINE_{test_job['name']}", "WARN", f"Unexpected result: {result}")
                    
            except Exception as e:
                log_test(f"PIPELINE_{test_job['name']}", "FAIL", f"Pipeline test failed: {e}")
                
    except Exception as e:
        log_test("PIPELINE_SETUP", "FAIL", f"Could not set up pipeline test: {e}")

def test_dependencies_exact_cloud():
    """Test all dependencies exactly as they would be in the cloud"""
    print("\n🔧 [TEST] Dependencies (Cloud Environment)")
    
    # Read requirements.txt
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read().strip().split('\n')
        
        # Filter out comments and empty lines
        packages = [line.strip() for line in requirements if line.strip() and not line.startswith('#')]
        
        for package in packages:
            try:
                # Parse package name (handle version specifiers)
                package_name = package.split('>=')[0].split('==')[0].split('<')[0].split('>')[0]
                
                # Try to import
                if package_name == 'firebase-admin':
                    import firebase_admin
                    log_test(f"DEP_{package_name.replace('-', '_').upper()}", "PASS", f"v{firebase_admin.__version__}")
                elif package_name == 'torch':
                    import torch
                    log_test(f"DEP_TORCH", "PASS", f"v{torch.__version__}, CUDA: {torch.cuda.is_available()}")
                elif package_name == 'diffusers':
                    import diffusers
                    log_test(f"DEP_DIFFUSERS", "PASS", f"v{diffusers.__version__}")
                elif package_name == 'transformers':
                    import transformers
                    log_test(f"DEP_TRANSFORMERS", "PASS", f"v{transformers.__version__}")
                else:
                    # Generic import test
                    __import__(package_name.replace('-', '_'))
                    log_test(f"DEP_{package_name.replace('-', '_').upper()}", "PASS", "Available")
                    
            except ImportError:
                log_test(f"DEP_{package_name.replace('-', '_').upper()}", "FAIL", "Not available")
            except Exception as e:
                log_test(f"DEP_{package_name.replace('-', '_').upper()}", "FAIL", f"Error: {e}")
                
    except Exception as e:
        log_test("DEPENDENCIES", "FAIL", f"Could not read requirements.txt: {e}")

def generate_test_report():
    """Generate comprehensive test report"""
    print("\n" + "="*80)
    print("🔍 COMPREHENSIVE CLOUD EMULATION TEST REPORT")
    print("="*80)
    
    total_tests = len(TEST_RESULTS)
    passed_tests = len([t for t in TEST_RESULTS if t["status"] == "PASS"])
    failed_tests = len([t for t in TEST_RESULTS if t["status"] == "FAIL"])
    
    print(f"📊 SUMMARY: {passed_tests}/{total_tests} tests passed")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    
    if FAILED_TESTS:
        print(f"\n🚨 CRITICAL FAILURES that would break production:")
        for test in FAILED_TESTS:
            matching_result = next(r for r in TEST_RESULTS if r["test"] == test)
            print(f"   • {test}: {matching_result['details']}")
        
        print(f"\n💡 These failures would cause the EXACT same issues you're seeing in RunPod!")
    else:
        print(f"\n🎉 ALL TESTS PASSED - Production deployment should work!")
    
    # Save detailed report
    with open('cloud_emulation_test_report.json', 'w') as f:
        json.dump({
            "summary": {
                "total": total_tests,
                "passed": passed_tests,
                "failed": failed_tests
            },
            "results": TEST_RESULTS,
            "critical_failures": FAILED_TESTS
        }, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: cloud_emulation_test_report.json")
    
    return failed_tests == 0

def main():
    """Run all cloud emulation tests"""
    print("🚀 STARTING COMPREHENSIVE CLOUD EMULATION TESTS")
    print("This will test EXACTLY what happens in your RunPod deployment")
    print("="*80)
    
    # Run all test suites
    test_dependencies_exact_cloud()
    test_huggingface_model_availability()
    test_download_weights_simulation()
    test_model_loading_exact_cloud_simulation()
    test_cloud_storage_simulation()
    test_full_generation_pipeline()
    
    # Generate report
    success = generate_test_report()
    
    if not success:
        print(f"\n🔥 CRITICAL: These tests revealed the EXACT issues you're seeing in production!")
        print(f"Fix these issues locally and re-run this test before deploying to RunPod.")
        sys.exit(1)
    else:
        print(f"\n✅ All tests passed! Your deployment should work correctly in RunPod.")
        sys.exit(0)

if __name__ == "__main__":
    main()

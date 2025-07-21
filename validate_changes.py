"""
Quick syntax and import validation script
Tests the code structure without downloading large models
"""

import sys
import importlib.util

def test_imports():
    """Test that all imports in our modules can be resolved"""
    print("🔍 Testing imports...")
    
    # Test schemas.py
    try:
        spec = importlib.util.spec_from_file_location("schemas", "schemas.py")
        schemas = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(schemas)
        print("✅ schemas.py imports successfully")
        
        # Validate schema structure
        assert hasattr(schemas, 'INPUT_SCHEMA')
        assert 'prompt' in schemas.INPUT_SCHEMA
        assert 'mask_url' in schemas.INPUT_SCHEMA  # Should be there for inpainting
        print("✅ INPUT_SCHEMA structure looks good")
        
    except Exception as e:
        print(f"❌ schemas.py failed: {e}")
        return False
    
    # Test that our handler.py has correct structure (without importing heavy dependencies)
    try:
        with open("handler.py", "r") as f:
            handler_content = f.read()
        
        # Check for key components
        required_components = [
            "diffusers/stable-diffusion-xl-1.0-inpainting-0.1",  # New model name
            "def load_inpaint",
            "def generate_image",
            "starting_image and mask_url",  # Inpainting check
            "StableDiffusionXLInpaintPipeline",  # Updated pipeline class
        ]
        
        for component in required_components:
            if component not in handler_content:
                print(f"❌ Missing required component in handler.py: {component}")
                return False
        
        print("✅ handler.py structure looks good")
        
    except Exception as e:
        print(f"❌ handler.py validation failed: {e}")
        return False
    
    # Test download_weights.py structure
    try:
        with open("download_weights.py", "r") as f:
            download_content = f.read()
        
        if "diffusers/stable-diffusion-xl-1.0-inpainting-0.1" not in download_content:
            print("❌ download_weights.py not updated with new model")
            return False
        
        if "kandinsky-community/kandinsky-2-2-decoder-inpaint" in download_content:
            print("⚠️ Warning: Old Kandinsky model still referenced in download_weights.py")
        
        print("✅ download_weights.py looks good")
        
    except Exception as e:
        print(f"❌ download_weights.py validation failed: {e}")
        return False
    
    return True

def test_model_compatibility():
    """Test model compatibility without actually loading models"""
    print("\n🧪 Testing model compatibility...")
    
    try:
        # Test that we can import diffusers and the pipeline we need
        from diffusers import StableDiffusionXLInpaintPipeline  # Updated import
        print("✅ StableDiffusionXLInpaintPipeline import successful")
        
        # Test basic torch functionality
        import torch
        print(f"✅ PyTorch {torch.__version__} available")
        print(f"✅ CUDA available: {torch.cuda.is_available()}")
        
        # Test PIL for image processing
        from PIL import Image, ImageDraw
        print("✅ PIL imports successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Run: pip install -r requirements-dev.txt")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def generate_test_inpaint_request():
    """Generate a test request for inpainting to validate the schema"""
    print("\n📝 Generating test inpainting request...")
    
    test_request = {
        "id": "test-123",
        "input": {
            "prompt": "a beautiful red rose",
            "negative_prompt": "blurry, low quality",
            "image_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
            "mask_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
            "height": 512,
            "width": 512,
            "num_inference_steps": 20,
            "guidance_scale": 7.5,
            "strength": 0.99,
            "seed": 42
        }
    }
    
    try:
        import json
        print("✅ Test inpainting request generated:")
        print(json.dumps(test_request, indent=2))
        return test_request
    except Exception as e:
        print(f"❌ Failed to generate test request: {e}")
        return None

if __name__ == "__main__":
    print("🚦 Running quick validation tests...\n")
    
    success = True
    
    # Test imports and structure
    if not test_imports():
        success = False
    
    # Test dependencies
    if not test_model_compatibility():
        success = False
    
    # Generate test request
    if not generate_test_inpaint_request():
        success = False
    
    print("\n" + "="*50)
    if success:
        print("🎉 All validation tests passed!")
        print("✅ Your code structure looks good")
        print("✅ Dependencies are properly installed")
        print("✅ Ready for full model testing")
        print("\nNext steps:")
        print("1. Download models: python download_weights.py")
        print("2. Run full test: python test_local.py")
    else:
        print("❌ Some validation tests failed")
        print("Please fix the issues above before proceeding")
        sys.exit(1)

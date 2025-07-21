"""
Local development and testing script for SDXL Worker
This allows you to test the model changes without deploying to RunPod
"""

import os
import sys
import json
import base64
from io import BytesIO
from PIL import Image

# Mock RunPod functions for local testing
class MockRunPod:
    class serverless:
        @staticmethod
        def start(config):
            print("Mock RunPod serverless started")
            handler = config["handler"]
            
            # Load test input
            with open("test_input.json", "r") as f:
                test_job = json.load(f)
            
            # Add a mock job ID
            test_job["id"] = "test-job-123"
            
            print("Running test job...")
            result = handler(test_job)
            print("Result:", json.dumps(result, indent=2, default=str))
            return result
    
    class utils:
        class rp_upload:
            @staticmethod
            def upload_image(job_id, image_path):
                # For local testing, just return the local path
                return f"file://{image_path}"
        
        class rp_cleanup:
            @staticmethod
            def clean(paths):
                print(f"Mock cleanup called for: {paths}")
        
        class rp_validator:
            @staticmethod
            def validate(input_data, schema):
                # Simple validation - just return the input
                return {"validated_input": input_data}

# Replace runpod import
sys.modules['runpod'] = MockRunPod()
sys.modules['runpod.serverless'] = MockRunPod.serverless
sys.modules['runpod.serverless.utils'] = MockRunPod.utils
sys.modules['runpod.serverless.utils.rp_upload'] = MockRunPod.utils.rp_upload
sys.modules['runpod.serverless.utils.rp_cleanup'] = MockRunPod.utils.rp_cleanup
sys.modules['runpod.serverless.utils.rp_validator'] = MockRunPod.utils.rp_validator

# Set environment variable to use local file output instead of S3
os.environ.pop("BUCKET_ENDPOINT_URL", None)

def test_inpainting():
    """Test inpainting functionality specifically"""
    
    # Create a simple test image and mask
    test_image = Image.new('RGB', (512, 512), color='red')
    test_mask = Image.new('L', (512, 512), color='black')
    
    # Add a white square in the mask (area to inpaint)
    from PIL import ImageDraw
    draw = ImageDraw.Draw(test_mask)
    draw.rectangle([200, 200, 300, 300], fill='white')
    
    # Save as base64
    def image_to_base64(img):
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
    
    # Create test job for inpainting
    test_job = {
        "id": "inpaint-test-123",
        "input": {
            "prompt": "a beautiful flower",
            "image_url": image_to_base64(test_image),
            "mask_url": image_to_base64(test_mask),
            "num_inference_steps": 5,  # Quick test
            "height": 512,
            "width": 512,
            "guidance_scale": 7.5,
            "seed": 42
        }
    }
    
    # Import and test
    try:
        from handler import generate_image
        result = generate_image(test_job)
        print("Inpainting test result:", json.dumps(result, indent=2, default=str))
        return result
    except Exception as e:
        print(f"Inpainting test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_text2img():
    """Test basic text-to-image functionality"""
    test_job = {
        "id": "text2img-test-123", 
        "input": {
            "prompt": "a simple red circle",
            "num_inference_steps": 5,  # Quick test
            "height": 512,
            "width": 512,
            "guidance_scale": 7.5,
            "seed": 42
        }
    }
    
    try:
        from handler import generate_image
        result = generate_image(test_job)
        print("Text2img test result:", json.dumps(result, indent=2, default=str))
        return result
    except Exception as e:
        print(f"Text2img test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("Starting local SDXL worker tests...")
    
    # Test basic functionality first
    print("\n=== Testing Text-to-Image ===")
    text2img_result = test_text2img()
    
    if text2img_result and "error" not in text2img_result:
        print("✅ Text-to-image test passed!")
        
        print("\n=== Testing Inpainting ===")
        inpaint_result = test_inpainting()
        
        if inpaint_result and "error" not in inpaint_result:
            print("✅ Inpainting test passed!")
            print("🎉 All tests passed! Ready to deploy.")
        else:
            print("❌ Inpainting test failed")
    else:
        print("❌ Text-to-image test failed - fix this before testing inpainting")

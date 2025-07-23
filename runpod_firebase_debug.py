"""
Add this test function to your handler.py for RunPod debugging
Call it with: {"test_firebase_debug": true} in your job input
"""

import os
import json

def test_firebase_debug(job_input):
    """Debug Firebase functionality in RunPod environment"""
    
    print("🔧 [RUNPOD DEBUG] Starting Firebase debug test...")
    
    # Test 1: Environment variables
    print("\n🔧 [TEST 1] Environment Variables:")
    firebase_key = os.environ.get("FIREBASE_SERVICE_ACCOUNT_KEY")
    firebase_bucket = os.environ.get("FIREBASE_STORAGE_BUCKET")
    
    print(f"FIREBASE_SERVICE_ACCOUNT_KEY present: {bool(firebase_key)}")
    print(f"FIREBASE_STORAGE_BUCKET: {firebase_bucket}")
    
    if firebase_key:
        try:
            key_data = json.loads(firebase_key)
            print(f"✅ JSON key valid, project: {key_data.get('project_id')}")
        except Exception as e:
            print(f"❌ JSON key invalid: {e}")
            return {"error": "Invalid Firebase JSON key"}
    
    # Test 2: Firebase imports and initialization
    print("\n🔧 [TEST 2] Firebase Imports and Initialization:")
    try:
        import firebase_admin
        from firebase_admin import credentials, storage, firestore
        print(f"✅ Firebase admin version: {firebase_admin.__version__}")
    except ImportError as e:
        print(f"❌ Firebase import failed: {e}")
        return {"error": "Firebase admin not available"}
    
    # Test 3: Cloud storage initialization
    print("\n🔧 [TEST 3] Cloud Storage Initialization:")
    try:
        from cloud_storage import cloud_storage
        print(f"✅ Storage type: {cloud_storage.storage_type}")
        print(f"✅ Storage bucket: {type(cloud_storage.storage_bucket)}")
        print(f"✅ Firestore DB: {type(cloud_storage.firestore_db)}")
        
        if cloud_storage.storage_type != "firebase":
            return {"error": f"Expected firebase storage, got: {cloud_storage.storage_type}"}
            
    except Exception as e:
        print(f"❌ Cloud storage init failed: {e}")
        import traceback
        traceback.print_exc()
        return {"error": f"Cloud storage initialization failed: {str(e)}"}
    
    # Test 4: Network connectivity
    print("\n🔧 [TEST 4] Network Connectivity:")
    try:
        import requests
        response = requests.get('https://firebase.googleapis.com', timeout=10)
        print(f"✅ Firebase API reachable: {response.status_code}")
    except Exception as e:
        print(f"❌ Network connectivity issue: {e}")
        return {"error": f"Network connectivity failed: {str(e)}"}
    
    # Test 5: Simple upload test
    print("\n🔧 [TEST 5] Simple Upload Test:")
    try:
        from PIL import Image
        from io import BytesIO
        
        # Create tiny test image
        test_image = Image.new('RGB', (5, 5), color='green')
        img_buffer = BytesIO()
        test_image.save(img_buffer, format='PNG')
        img_bytes = img_buffer.getvalue()
        
        print(f"✅ Created test image: {len(img_bytes)} bytes")
        
        # Try direct upload
        test_url = cloud_storage.upload_file(
            file_data=img_bytes,
            filename="runpod_test.png",
            content_type="image/png",
            user_id="runpod-debug",
            file_uid="debug-test-001"
        )
        
        print(f"✅ Upload successful: {test_url}")
        
        if test_url.startswith("https://"):
            print("✅ Real Firebase URL returned")
            success = True
        else:
            print("⚠️ Fallback URL returned (Firebase upload failed)")
            success = False
            
    except Exception as e:
        print(f"❌ Upload test failed: {e}")
        import traceback
        traceback.print_exc()
        return {"error": f"Upload test failed: {str(e)}"}
    
    # Test 6: Threading test
    print("\n🔧 [TEST 6] Threading Test:")
    import threading
    print(f"✅ Active threads: {threading.active_count()}")
    
    def test_background_task():
        print("✅ Background thread executed successfully")
        
    try:
        thread = threading.Thread(target=test_background_task, daemon=True)
        thread.start()
        thread.join(timeout=5)  # Wait up to 5 seconds
        
        if thread.is_alive():
            print("⚠️ Background thread still running")
        else:
            print("✅ Background thread completed")
            
    except Exception as e:
        print(f"❌ Threading test failed: {e}")
    
    result = {
        "status": "debug_complete",
        "firebase_initialized": cloud_storage.storage_type == "firebase",
        "upload_successful": success,
        "test_url": test_url if 'test_url' in locals() else None,
        "environment_ok": bool(firebase_key and firebase_bucket),
        "message": "Firebase debug test completed - check logs for details"
    }
    
    print(f"\n🔧 [RUNPOD DEBUG] Final result: {result}")
    return result


# Add this to your generate_image function:
# if job_input.get("test_firebase_debug"):
#     return test_firebase_debug(job_input)

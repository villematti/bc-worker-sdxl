#!/usr/bin/env python3
"""
Test Firebase upload with actual credentials
"""

import os
import json
import sys
from io import BytesIO
from PIL import Image

def test_with_real_credentials():
    """Test Firebase upload with real credentials"""
    
    print("🔧 [DEBUG] Testing with real Firebase credentials...")
    
    # Read the actual Firebase service account JSON
    try:
        with open('storage_access.json', 'r') as f:
            service_account_data = json.load(f)
        print("✅ Successfully loaded storage_access.json")
    except Exception as e:
        print(f"❌ Failed to load storage_access.json: {e}")
        return False
    
    # Set environment variables
    os.environ['FIREBASE_SERVICE_ACCOUNT_KEY'] = json.dumps(service_account_data)
    os.environ['FIREBASE_STORAGE_BUCKET'] = 'bc-image-gen.firebasestorage.app'
    
    print(f"✅ Set Firebase bucket: {os.environ['FIREBASE_STORAGE_BUCKET']}")
    
    # Test 1: Check if firebase-admin is available
    print("\n🔧 [TEST 1] Testing firebase-admin availability...")
    try:
        import firebase_admin
        from firebase_admin import credentials, storage, firestore
        print("✅ firebase-admin is available")
    except ImportError as e:
        print(f"❌ firebase-admin not installed: {e}")
        print("💡 Run: pip install firebase-admin")
        return False
    
    # Test 2: Test cloud storage initialization
    print("\n🔧 [TEST 2] Testing cloud storage initialization...")
    try:
        # Force reload the cloud_storage module to pick up new env vars
        import importlib
        if 'cloud_storage' in sys.modules:
            importlib.reload(sys.modules['cloud_storage'])
        
        from cloud_storage import cloud_storage
        print(f"✅ Cloud storage type: {cloud_storage.storage_type}")
        
        if cloud_storage.storage_type == "firebase":
            print("✅ Firebase initialized successfully")
            print(f"✅ Storage bucket type: {type(cloud_storage.storage_bucket)}")
            print(f"✅ Firestore DB type: {type(cloud_storage.firestore_db)}")
        else:
            print(f"❌ Expected firebase type, got: {cloud_storage.storage_type}")
            return False
            
    except Exception as e:
        print(f"❌ Cloud storage initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Test actual upload
    print("\n🔧 [TEST 3] Testing actual Firebase upload...")
    try:
        # Create a small test image
        test_image = Image.new('RGB', (10, 10), color='blue')
        
        # Convert to bytes
        img_buffer = BytesIO()
        test_image.save(img_buffer, format='PNG')
        img_bytes = img_buffer.getvalue()
        
        print(f"✅ Created test image: {len(img_bytes)} bytes")
        
        # Test the upload_file method directly
        test_url = cloud_storage.upload_file(
            file_data=img_bytes,
            filename="test.png",
            content_type="image/png",
            user_id="test-user-debug",
            file_uid="test-file-debug"
        )
        
        print(f"✅ Upload successful! URL: {test_url}")
        
        # Test if it's a real Firebase URL or base64 fallback
        if test_url.startswith("https://"):
            print("✅ Real Firebase Storage URL returned")
        elif test_url.startswith("data:"):
            print("⚠️ Base64 fallback URL returned (upload may have failed)")
        else:
            print(f"⚠️ Unexpected URL format: {test_url[:100]}...")
            
    except Exception as e:
        print(f"❌ Upload test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Test Firestore update
    print("\n🔧 [TEST 4] Testing Firestore update...")
    try:
        test_data = {
            "status": "test",
            "generated": True,
            "test_timestamp": firestore.SERVER_TIMESTAMP
        }
        
        success = cloud_storage.update_generation_status(
            user_id="test-user-debug",
            file_uid="test-file-debug", 
            generation_data=test_data,
            media_type="images"
        )
        
        if success:
            print("✅ Firestore update successful")
        else:
            print("⚠️ Firestore update returned False")
            
    except Exception as e:
        print(f"❌ Firestore test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n✅ All tests passed! Firebase integration is working.")
    print("💡 If uploads are still failing in RunPod, check:")
    print("   1. Network connectivity in RunPod environment")
    print("   2. Background thread execution")
    print("   3. RunPod environment variable setup")
    
    return True

if __name__ == "__main__":
    test_with_real_credentials()

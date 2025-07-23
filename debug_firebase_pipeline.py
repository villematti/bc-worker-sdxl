#!/usr/bin/env python3
"""
Comprehensive debug script to test the full Firebase upload pipeline
This will help identify exactly where the upload is failing
"""

import os
import sys
import json
from io import BytesIO
from PIL import Image
import base64

def test_firebase_pipeline():
    """Test the complete Firebase upload pipeline with debugging"""
    
    print("🔧 [DEBUG] Starting comprehensive Firebase pipeline test...")
    
    # Set mock Firebase credentials
    os.environ['FIREBASE_SERVICE_ACCOUNT_KEY'] = json.dumps({
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "test-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...\n-----END PRIVATE KEY-----\n",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token"
    })
    os.environ['FIREBASE_STORAGE_BUCKET'] = 'test-bucket.appspot.com'
    
    # Test 1: Check if firebase-admin is importable
    print("\n🔧 [TEST 1] Testing firebase-admin import...")
    try:
        import firebase_admin
        from firebase_admin import credentials, storage, firestore
        print("✅ firebase-admin imported successfully")
    except ImportError as e:
        print(f"❌ firebase-admin import failed: {e}")
        print("💡 Install with: pip install firebase-admin")
        return False
    
    # Test 2: Test cloud storage initialization
    print("\n🔧 [TEST 2] Testing cloud storage initialization...")
    try:
        from cloud_storage import cloud_storage
        print(f"✅ Cloud storage type: {cloud_storage.storage_type}")
        print(f"✅ Storage bucket present: {cloud_storage.storage_bucket is not None}")
        print(f"✅ Firestore DB present: {cloud_storage.firestore_db is not None}")
        
        if cloud_storage.storage_type != "firebase":
            print(f"❌ Expected firebase storage type, got: {cloud_storage.storage_type}")
            return False
            
    except Exception as e:
        print(f"❌ Cloud storage initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Test image upload function
    print("\n🔧 [TEST 3] Testing image upload function...")
    try:
        from cloud_storage import save_and_upload_images_cloud
        
        # Create a test image
        test_image = Image.new('RGB', (100, 100), color='red')
        
        # Test the upload function (this will fail due to fake credentials but should show the flow)
        try:
            result = save_and_upload_images_cloud(
                images=[test_image],
                job_id="test-job-123",
                user_id="test-user-456", 
                file_uid="test-file-789"
            )
            print(f"✅ Upload function completed: {result}")
        except Exception as upload_error:
            print(f"⚠️ Upload failed (expected with fake credentials): {upload_error}")
            # This is expected to fail, but we want to see the flow
            
    except Exception as e:
        print(f"❌ Image upload function test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Test handler import and basic structure
    print("\n🔧 [TEST 4] Testing handler imports...")
    try:
        from handler import generate_image, _save_and_upload_images, _save_and_upload_video
        print("✅ Handler functions imported successfully")
    except Exception as e:
        print(f"❌ Handler import failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n✅ All tests completed! The pipeline structure looks correct.")
    print("💡 The issue is likely in the RunPod environment:")
    print("   1. Check RunPod logs for actual error messages")
    print("   2. Verify Firebase credentials are valid JSON")
    print("   3. Check network connectivity from RunPod to Firebase")
    print("   4. Ensure background threads are completing successfully")
    
    return True

if __name__ == "__main__":
    test_firebase_pipeline()

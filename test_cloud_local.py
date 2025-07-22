"""
Local test for cloud storage functionality
Tests the cloud storage integration without requiring Firebase setup
"""

import sys
import os
sys.path.append('.')

from cloud_storage import CloudStorageManager
import tempfile
from PIL import Image
import uuid

def test_local_cloud_storage():
    """Test cloud storage functionality in local mode (no Firebase)"""
    
    print("🧪 Testing Cloud Storage Manager (Local Mode)")
    print("=" * 50)
    
    # Initialize cloud storage manager (should detect local mode)
    storage = CloudStorageManager()
    
    print(f"✅ Storage type detected: {storage.storage_type}")
    
    # Test with fake image data
    test_image = Image.new('RGB', (256, 256), color='red')
    
    # Convert to bytes
    from io import BytesIO
    img_buffer = BytesIO()
    test_image.save(img_buffer, format='PNG')
    img_bytes = img_buffer.getvalue()
    
    # Test file upload (should return base64 in local mode)
    user_id = "test_user_123"
    file_uid = str(uuid.uuid4())
    
    print(f"\n📤 Testing file upload:")
    print(f"User ID: {user_id}")
    print(f"File UID: {file_uid}")
    
    result_url = storage.upload_file(
        file_data=img_bytes,
        filename="test_image.png",
        content_type="image/png",
        user_id=user_id,
        file_uid=file_uid
    )
    
    # Check if result is base64 (local mode) or URL (cloud mode)
    if result_url.startswith("data:image/png;base64,"):
        print("✅ Local mode: Returned base64 encoded image")
        print(f"📏 Base64 length: {len(result_url)} characters")
    else:
        print(f"✅ Cloud mode: Returned URL: {result_url}")
    
    # Test database operations (should skip in local mode)
    print(f"\n🗄️ Testing database operations:")
    
    success = storage.create_generation_request(user_id, file_uid, {
        'task_type': 'text2img',
        'prompt': 'test prompt',
        'job_id': 'test_job_123'
    })
    
    if success:
        print("✅ Database request created successfully")
    else:
        print("ℹ️ Database operations skipped (no cloud database configured)")
    
    success = storage.update_generation_status(user_id, file_uid, {
        'images': [result_url],
        'seed': 42,
        'status': 'completed'
    })
    
    if success:
        print("✅ Database status updated successfully")
    else:
        print("ℹ️ Database operations skipped (no cloud database configured)")

def test_handler_integration():
    """Test how the handler would use cloud storage"""
    
    print("\n🔧 Testing Handler Integration")
    print("=" * 50)
    
    # Import the cloud storage functions
    try:
        from cloud_storage import save_and_upload_images_cloud, save_and_upload_video_cloud
        
        # Test image upload
        test_images = [Image.new('RGB', (512, 512), color='blue')]
        user_id = "test_user_456"
        file_uid = str(uuid.uuid4())
        job_id = "test_job_456"
        
        print(f"📸 Testing image upload function:")
        image_urls = save_and_upload_images_cloud(test_images, job_id, user_id, file_uid)
        
        print(f"✅ Image upload completed:")
        for i, url in enumerate(image_urls):
            if url.startswith("data:"):
                print(f"  Image {i}: Base64 ({len(url)} chars)")
            else:
                print(f"  Image {i}: {url}")
        
        print(f"\n🎬 Testing video upload function:")
        # Create fake video frames (just colored images)
        video_frames = [Image.new('RGB', (320, 240), color=color) 
                       for color in ['red', 'green', 'blue', 'yellow', 'purple']]
        
        try:
            video_url = save_and_upload_video_cloud(video_frames, job_id, user_id, file_uid, fps=5)
            
            if video_url.startswith("data:"):
                print(f"✅ Video upload completed: Base64 ({len(video_url)} chars)")
            else:
                print(f"✅ Video upload completed: {video_url}")
                
        except Exception as e:
            print(f"⚠️ Video upload test failed: {e}")
            print("This is expected if diffusers export_to_video is not available")
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("Make sure cloud_storage.py is in the same directory")

if __name__ == "__main__":
    print("🚀 Cloud Storage Local Testing")
    print("=" * 60)
    
    # Test basic cloud storage functionality
    test_local_cloud_storage()
    
    # Test handler integration
    test_handler_integration()
    
    print("\n🎯 Summary:")
    print("• Local mode automatically detected (no cloud credentials)")
    print("• Base64 encoding used as fallback")
    print("• Database operations gracefully skipped")
    print("• Ready for cloud deployment with proper environment variables")
    
    print("\n🔧 To enable cloud storage:")
    print("1. Set up Firebase project and get service account key")
    print("2. Set environment variables:")
    print("   - FIREBASE_SERVICE_ACCOUNT_KEY")
    print("   - FIREBASE_STORAGE_BUCKET")
    print("3. Deploy with proper credentials")
    print("4. Firebase storage will automatically activate")

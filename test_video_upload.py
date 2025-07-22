"""
Test video generation and upload to Firebase Storage
Creates a simple test video and uploads it using c        # Update generation status with final data (as RunPod worker would)
        generation_data = {
            "video_url": video_url,
            "prompt": "Test video generation",
            "num_frames": len(video_frames),
            "fps": 15,
            "file_uid": file_uid,
            "user_id": user_id
        }
        
        print("📊 RunPod worker updating generation status...")
        success = cloud_storage.update_generation_status(user_id, file_uid, generation_data, "videos")
        if success:
            print("✅ Generation status updated by RunPod worker")
        else:
            print("⚠️ Failed to update generation status (or Firebase not available)")
        
        # Expected file structure info
        print("\n📁 Expected file structure:")
        print(f"   Storage Path: generating/{user_id}/video/{file_uid}.mp4")
        print(f"   Firestore Document: generations/{user_id}/videos/{file_uid}")
        print(f"   Document Fields: status, generated, modified, generation_data, etc.")
        print(f"\n🔄 Workflow:")
        print(f"   1. Firebase Function creates initial document (status: 'queued')")
        print(f"   2. RunPod worker processes and uploads (status: 'completed')")
        print(f"   3. Frontend gets real-time updates via Firestore listeners")
"""

import os
import uuid
import numpy as np
from PIL import Image
import tempfile

# Set environment variables to use the local JSON file for testing
# In RunPod, these would be set as environment variables
os.environ['FIREBASE_SERVICE_ACCOUNT_KEY'] = 'storage_access.json'  # File path
os.environ['FIREBASE_STORAGE_BUCKET'] = 'bc-image-gen.firebasestorage.app'

# Import our cloud storage module
from cloud_storage import save_and_upload_video_cloud, cloud_storage

def create_test_video_frames(num_frames=30, width=256, height=256):
    """
    Create a simple test video with changing colors
    
    Args:
        num_frames: Number of frames to generate
        width: Frame width
        height: Frame height
        
    Returns:
        List of numpy arrays representing video frames
    """
    frames = []
    
    for i in range(num_frames):
        # Create a frame with a gradient that changes over time
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Create a moving gradient effect
        for y in range(height):
            for x in range(width):
                # Color changes based on frame number and position
                r = int((x / width * 255 + i * 8) % 255)
                g = int((y / height * 255 + i * 4) % 255)
                b = int(((x + y) / (width + height) * 255 + i * 2) % 255)
                frame[y, x] = [r, g, b]
        
        frames.append(frame)
    
    return frames

def test_video_upload():
    """Test video generation and upload to Firebase Storage"""
    
    print("🎬 Testing video upload to Firebase Storage...")
    print(f"Storage type: {cloud_storage.storage_type}")
    
    # Generate random UIDs for testing
    user_id = str(uuid.uuid4())
    file_uid = str(uuid.uuid4())
    job_id = "test-job-123"
    
    print(f"👤 Test user_id: {user_id}")
    print(f"📁 Test file_uid: {file_uid}")
    
    # Create test video frames
    print("🎨 Generating test video frames...")
    video_frames = create_test_video_frames(num_frames=30, width=256, height=256)
    print(f"✅ Generated {len(video_frames)} frames")
    
    # Create initial generation request in Firestore
    request_data = {
        "prompt": "Test video generation",
        "num_frames": len(video_frames),
        "width": 256,
        "height": 256,
        "fps": 15
    }
    
    print("📝 Simulating Firebase function creating initial document...")
    try:
        from firebase_admin import firestore
        doc_ref = cloud_storage.firestore_db.collection('generations').document(user_id).collection('videos').document(file_uid)
        doc_ref.set({
            'status': 'queued',
            'created_at': firestore.SERVER_TIMESTAMP,
            'request_data': request_data,
            'file_uid': file_uid,
            'user_id': user_id
        })
        print("✅ Initial document created (simulated Firebase function)")
    except Exception as e:
        print(f"❌ Failed to create initial document: {e}")
    
    # Upload video to cloud storage
    print("☁️ Uploading video to Firebase Storage...")
    try:
        video_url = save_and_upload_video_cloud(
            video_frames=video_frames,
            job_id=job_id,
            user_id=user_id,
            file_uid=file_uid,
            fps=15
        )
        
        print(f"✅ Video uploaded successfully!")
        print(f"🔗 Video URL: {video_url}")
        
        # Update generation status in Firestore
        generation_data = {
            "video_url": video_url,
            "prompt": "Test video generation",
            "num_frames": len(video_frames),
            "fps": 15,
            "file_uid": file_uid,
            "user_id": user_id
        }
        
        print("📊 Updating generation status in Firestore...")
        success = cloud_storage.update_generation_status(user_id, file_uid, generation_data)
        if success:
            print("✅ Generation status updated")
        else:
            print("⚠️ Failed to update generation status (or Firebase not available)")
        
        # Expected file structure info
        print("\n📁 Expected file structure in Firebase Storage:")
        print(f"   Storage Path: generating/{user_id}/video/{file_uid}.mp4")
        print(f"   Firestore Document: generations/{user_id}/files/{file_uid}")
        print(f"   Document Fields: status, generated, modified, generation_data, etc.")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to upload video: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Firebase Video Upload Test")
    print("=" * 50)
    
    # Check if Firebase is properly configured
    if cloud_storage.storage_type == "firebase":
        print("✅ Firebase is configured and available")
    else:
        print("⚠️ Firebase not configured, will fallback to base64")
    
    # Run the test
    success = test_video_upload()
    
    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n❌ Test failed!")
    
    print("\n💡 If using Firebase, check the Firebase Console:")
    print("   - Storage: https://console.firebase.google.com/project/bc-image-gen/storage")
    print("   - Firestore: https://console.firebase.google.com/project/bc-image-gen/firestore")

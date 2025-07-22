"""
Test the exact Firestore paths used in our cloud storage
"""
import os
import uuid

# Set environment variables  
os.environ['FIREBASE_SERVICE_ACCOUNT_KEY'] = 'storage_access.json'
os.environ['FIREBASE_STORAGE_BUCKET'] = 'bc-image-gen.firebasestorage.app'

from cloud_storage import cloud_storage

def test_exact_paths():
    """Test the exact Firestore paths we use in the cloud storage"""
    
    print("🧪 Testing RunPod worker functions (simulating Firebase function workflow)...")
    
    # Generate test IDs (normally done by Firebase function)
    user_id = str(uuid.uuid4())
    file_uid = str(uuid.uuid4())
    
    print(f"👤 User ID: {user_id}")
    print(f"📁 File UID: {file_uid}")
    
    # Simulate what Firebase function would do - create initial document
    print("\n📝 Simulating Firebase function creating initial document...")
    try:
        from firebase_admin import firestore
        doc_ref = cloud_storage.firestore_db.collection('generations').document(user_id).collection('videos').document(file_uid)
        doc_ref.set({
            'status': 'queued',
            'created_at': firestore.SERVER_TIMESTAMP,
            'request_data': {"prompt": "test video", "fps": 15},
            'file_uid': file_uid,
            'user_id': user_id
        })
        print("✅ Initial document created (simulated Firebase function)")
    except Exception as e:
        print(f"❌ Failed to create initial document: {e}")
    
    # Test RunPod worker functions
    print("\n🎬 Testing RunPod worker - mark media ready...")
    success = cloud_storage.mark_media_ready(user_id, file_uid, "videos")
    print(f"Result: {'✅ Success' if success else '❌ Failed'}")
    
    print("\n📊 Testing RunPod worker - update generation status...")
    generation_data = {"video_url": "https://example.com/video.mp4", "fps": 15}
    success = cloud_storage.update_generation_status(user_id, file_uid, generation_data, "videos")
    print(f"Result: {'✅ Success' if success else '❌ Failed'}")
    
    print(f"\n📁 Expected Firestore structure:")
    print(f"   generations/{user_id}/videos/{file_uid}")
    print(f"   Fields: status, generated, modified, generation_data, etc.")
    print(f"\n💡 Note: Initial document creation is handled by Firebase function")
    print(f"   RunPod worker only updates existing documents")

if __name__ == "__main__":
    test_exact_paths()

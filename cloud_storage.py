"""
Cloud Storage and Database Management for SDXL Worker
Handles uploading images/videos to Firebase Storage and updating Firestore
"""

import os
import base64
import json
from io import BytesIO
from typing import Optional, Dict, Any, List
import uuid
from datetime import datetime

# Firebase imports
try:
    import firebase_admin
    from firebase_admin import credentials, storage, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("⚠️ Firebase not available. Install with: pip install firebase-admin")

class CloudStorageManager:
    """Manages Firebase Storage and Firestore operations for generated content"""
    
    def __init__(self):
        self.firebase_app = None
        self.storage_bucket = None
        self.firestore_db = None
        self.storage_type = self._detect_storage_type()
        self._initialize_storage()
    
    def _detect_storage_type(self) -> str:
        """Detect if Firebase is available and configured"""
        if os.environ.get("FIREBASE_SERVICE_ACCOUNT_KEY") and FIREBASE_AVAILABLE:
            return "firebase"
        else:
            return "local"  # Fallback to local base64 encoding
    
    def _initialize_storage(self):
        """Initialize Firebase Storage"""
        try:
            if self.storage_type == "firebase":
                self._initialize_firebase()
            else:
                print("📱 Using local base64 encoding (no Firebase configured)")
        except Exception as e:
            print(f"⚠️ Failed to initialize Firebase storage: {e}")
            self.storage_type = "local"
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        service_account_key = os.environ.get("FIREBASE_SERVICE_ACCOUNT_KEY")
        bucket_name = os.environ.get("FIREBASE_STORAGE_BUCKET")
        
        if not service_account_key or not bucket_name:
            raise ValueError("Missing FIREBASE_SERVICE_ACCOUNT_KEY or FIREBASE_STORAGE_BUCKET")
        
        # Parse service account key (can be JSON string or file path)
        if service_account_key.startswith("{"):
            # JSON string
            service_account_info = json.loads(service_account_key)
            cred = credentials.Certificate(service_account_info)
        else:
            # File path
            cred = credentials.Certificate(service_account_key)
        
        # Initialize Firebase app if not already done
        if not firebase_admin._apps:
            self.firebase_app = firebase_admin.initialize_app(cred, {
                'storageBucket': bucket_name
            })
        else:
            self.firebase_app = firebase_admin.get_app()
        
        self.storage_bucket = storage.bucket()
        self.firestore_db = firestore.client()
        print(f"✅ Firebase initialized with bucket: {bucket_name}")
    
    def upload_file(self, file_data: bytes, filename: str, content_type: str, 
                   user_id: str, file_uid: str) -> str:
        """
        Upload file to Firebase Storage and return public URL
        
        Args:
            file_data: Raw file bytes
            filename: Name for the file (not used - file_uid becomes filename)
            content_type: MIME type (e.g., "video/mp4", "image/png")
            user_id: Firebase user ID
            file_uid: Unique identifier for this file
            
        Returns:
            Public URL to access the file
        """
        if self.storage_type == "firebase":
            return self._upload_to_firebase(file_data, filename, content_type, user_id, file_uid)
        else:
            # Fallback to base64 encoding
            encoded_data = base64.b64encode(file_data).decode("utf-8")
            return f"data:{content_type};base64,{encoded_data}"
    
    def _upload_to_firebase(self, file_data: bytes, filename: str, content_type: str,
                           user_id: str, file_uid: str) -> str:
        """Upload file to Firebase Storage"""
        # Determine file type and extension from content type
        if content_type.startswith("video/"):
            file_type = "video"
            extension = ".mp4"
        else:
            file_type = "image"
            extension = ".png"
        
        # Create simple path: generating/{user_id}/{file_type}/{file_uid}.extension
        storage_path = f"generating/{user_id}/{file_type}/{file_uid}{extension}"
        
        # Upload to Firebase Storage
        blob = self.storage_bucket.blob(storage_path)
        blob.upload_from_string(file_data, content_type=content_type)
        
        # Make the file publicly accessible
        blob.make_public()
        
        print(f"✅ Uploaded to Firebase Storage: {storage_path}")
        return blob.public_url
    
    def update_generation_status(self, user_id: str, file_uid: str, 
                               generation_data: Dict[str, Any], media_type: str = "videos") -> bool:
        """
        Update Firestore with generation completion status
        
        Args:
            user_id: Firebase user ID
            file_uid: Unique identifier for this generation
            generation_data: Complete generation information
            media_type: Type of media ("videos" or "images")
            
        Returns:
            True if successful, False otherwise
        """
        if self.storage_type != "firebase" or not self.firestore_db:
            print("⚠️ Firestore not available, skipping database update")
            return False
        
        try:
            # Document path: generations/{user_id}/{media_type}/{file_uid}
            doc_ref = self.firestore_db.collection('generations').document(user_id).collection(media_type).document(file_uid)
            
            # Update document with generation results
            doc_ref.set({
                'status': 'completed',
                'completed_at': firestore.SERVER_TIMESTAMP,
                'generation_data': generation_data,
                'file_uid': file_uid,
                'user_id': user_id
            }, merge=True)
            
            print(f"✅ Updated Firestore: generations/{user_id}/{media_type}/{file_uid}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update Firestore: {e}")
            return False
    
    def mark_media_ready(self, user_id: str, file_uid: str, media_type: str = "videos") -> bool:
        """
        Mark media as ready in Firestore using the generations structure
        Structure: generations/{user_id}/{media_type}/{file_uid} - updates existing document
        
        Args:
            user_id: Firebase user ID
            file_uid: Unique identifier for this generation
            media_type: Type of media ("videos" or "images")
            
        Returns:
            True if successful, False otherwise
        """
        if self.storage_type != "firebase" or not self.firestore_db:
            print("⚠️ Firestore not available, skipping media ready update")
            return False
        
        try:
            # Document path: generations/{user_id}/{media_type}/{file_uid}
            doc_ref = self.firestore_db.collection('generations').document(user_id).collection(media_type).document(file_uid)
            
            # Update document with generated status
            doc_ref.set({
                'generated': True,
                'modified': firestore.SERVER_TIMESTAMP
            }, merge=True)
            
            print(f"✅ Marked media ready: generations/{user_id}/{media_type}/{file_uid}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to mark media ready: {e}")
            return False


# Global instance
cloud_storage = CloudStorageManager()


def save_and_upload_images_cloud(images: List, job_id: str, user_id: str, 
                                 file_uid: str) -> List[str]:
    """
    Save images to cloud storage and return URLs
    This function is called by RunPod after Firebase function creates initial request
    
    Args:
        images: List of PIL Image objects
        job_id: RunPod job ID (for local temp storage)
        user_id: Firebase user ID (provided by Firebase function)
        file_uid: Unique identifier for this generation (provided by Firebase function)
        
    Returns:
        List of public URLs to access the images
    """
    import tempfile
    
    image_urls = []
    
    for index, image in enumerate(images):
        # Convert PIL image to bytes
        img_buffer = BytesIO()
        image.save(img_buffer, format='PNG')
        img_bytes = img_buffer.getvalue()
        
        # For multiple images, append index to file_uid
        if len(images) > 1:
            image_file_uid = f"{file_uid}_{index}"
        else:
            image_file_uid = file_uid
        
        # Upload to cloud storage
        try:
            image_url = cloud_storage.upload_file(
                file_data=img_bytes,
                filename="",  # Not used anymore
                content_type="image/png",
                user_id=user_id,
                file_uid=image_file_uid
            )
            image_urls.append(image_url)
            
            # Mark image as ready in Firestore
            cloud_storage.mark_media_ready(user_id, image_file_uid, "images")
            
        except Exception as e:
            print(f"❌ Failed to upload image {index}: {e}")
            # Update Firestore with error status for this image
            error_data = {
                "status": "failed",
                "error": str(e)
            }
            cloud_storage.update_generation_status(user_id, image_file_uid, error_data, "images")
            
            # Fallback to base64
            image_data = base64.b64encode(img_bytes).decode("utf-8")
            image_urls.append(f"data:image/png;base64,{image_data}")
    
    # Update main document with final data
    try:
        generation_data = {
            "image_urls": image_urls,
            "status": "completed",
            "image_count": len(images)
        }
        cloud_storage.update_generation_status(user_id, file_uid, generation_data, "images")
    except Exception as e:
        print(f"❌ Failed to update final generation status: {e}")
    
    return image_urls


def save_and_upload_video_cloud(video_frames: List, job_id: str, user_id: str,
                               file_uid: str, fps: int = 15) -> str:
    """
    Save video to cloud storage and return URL
    This function is called by RunPod after Firebase function creates initial request
    
    Args:
        video_frames: List of video frame arrays
        job_id: RunPod job ID (for local temp storage)
        user_id: Firebase user ID (provided by Firebase function)
        file_uid: Unique identifier for this generation (provided by Firebase function)
        fps: Frames per second
        
    Returns:
        Public URL to access the video
    """
    import tempfile
    from diffusers.utils import export_to_video
    
    try:
        # Create temporary file for video export
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            temp_video_path = temp_file.name
        
        # Export video using diffusers utility
        export_to_video(video_frames, temp_video_path, fps=fps)
        
        # Read video file as bytes
        with open(temp_video_path, 'rb') as video_file:
            video_bytes = video_file.read()
        
        # Clean up temp file
        os.unlink(temp_video_path)
        
        # Upload to cloud storage
        video_url = cloud_storage.upload_file(
            file_data=video_bytes,
            filename="",  # Not used anymore
            content_type="video/mp4",
            user_id=user_id,
            file_uid=file_uid
        )
        
        # Mark media as ready and update with final URL
        cloud_storage.mark_media_ready(user_id, file_uid, "videos")
        
        # Update with final generation data including URL
        generation_data = {
            "video_url": video_url,
            "status": "completed",
            "fps": fps
        }
        cloud_storage.update_generation_status(user_id, file_uid, generation_data, "videos")
        
        return video_url
        
    except Exception as e:
        print(f"❌ Failed to upload video: {e}")
        # Update Firestore with error status
        error_data = {
            "status": "failed",
            "error": str(e)
        }
        cloud_storage.update_generation_status(user_id, file_uid, error_data, "videos")
        
        # Fallback to base64 (though this will be large)
        video_data = base64.b64encode(video_bytes).decode("utf-8")
        return f"data:video/mp4;base64,{video_data}"

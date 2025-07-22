"""
Test script for cloud storage integration with SDXL Worker
Demonstrates how to make requests with Firebase user metadata
"""

import json
import base64
import uuid
from datetime import datetime

# Example request payloads showing the new cloud storage integration

def create_video_request_with_cloud_storage():
    """Example video generation request with Firebase cloud storage"""
    
    request = {
        # Standard video generation parameters
        "task_type": "text2video",
        "prompt": "A majestic eagle soaring through mountain peaks, cinematic, high quality",
        "negative_prompt": "blurry, low quality, static, poor lighting",
        "video_width": 832,
        "video_height": 480,
        "num_frames": 49,  # Shorter for faster generation
        "video_guidance_scale": 5.0,
        "fps": 15,
        "seed": 42,
        
        # NEW: Cloud storage and database integration
        "user_id": "firebase_user_123",  # Firebase UID from your app
        "file_uid": str(uuid.uuid4()),   # Unique ID for this generation
        "use_cloud_storage": True        # Enable cloud storage
    }
    
    print("🎬 Video Generation Request with Cloud Storage:")
    print(json.dumps(request, indent=2))
    print(f"Expected result: Video uploaded to Firebase Storage at path:")
    print(f"generating/{request['user_id']}/video/{request['file_uid']}.mp4")
    print(f"Database entry created at: generations/{request['user_id']}/files/{request['file_uid']}")
    return request

def create_image_request_with_cloud_storage():
    """Example image generation request with Firebase cloud storage"""
    
    request = {
        # Standard image generation parameters
        "task_type": "text2img",
        "prompt": "A futuristic city skyline at sunset, cyberpunk style, neon lights",
        "negative_prompt": "blurry, low quality, distorted",
        "width": 1024,
        "height": 1024,
        "num_inference_steps": 30,
        "guidance_scale": 7.5,
        "num_images": 2,  # Generate 2 images
        "seed": 123,
        
        # NEW: Cloud storage and database integration
        "user_id": "firebase_user_456",  # Firebase UID from your app
        "file_uid": str(uuid.uuid4()),   # Unique ID for this generation
        "use_cloud_storage": True        # Enable cloud storage
    }
    
    print("\n🖼️ Image Generation Request with Cloud Storage:")
    print(json.dumps(request, indent=2))
    print(f"Expected result: Images uploaded to Firebase Storage at paths:")
    print(f"generating/{request['user_id']}/image/{request['file_uid']}_0.png")
    print(f"generating/{request['user_id']}/image/{request['file_uid']}_1.png")
    print(f"Database entry created at: generations/{request['user_id']}/files/{request['file_uid']}")
    return request

def create_fallback_request():
    """Example request that falls back to base64 encoding (existing behavior)"""
    
    request = {
        "task_type": "text2img",
        "prompt": "A beautiful landscape with mountains and lakes",
        "width": 512,
        "height": 512,
        "num_inference_steps": 20,
        "guidance_scale": 7.0,
        "seed": 999,
        
        # NO cloud storage parameters - will use existing base64 behavior
    }
    
    print("\n📱 Standard Request (Base64 Fallback):")
    print(json.dumps(request, indent=2))
    print("Expected result: Images returned as base64 encoded strings (existing behavior)")
    return request

def expected_cloud_response_format():
    """Show what the response format looks like with cloud storage"""
    
    # Video response with cloud storage
    video_response = {
        "videos": [
            "https://firebasestorage.googleapis.com/v0/b/your-project.appspot.com/o/generating%2Ffirebase_user_123%2Fvideo%2F12345.mp4?alt=media"
        ],
        "video_url": "https://firebasestorage.googleapis.com/v0/b/your-project.appspot.com/o/generating%2Ffirebase_user_123%2Fvideo%2F12345.mp4?alt=media",
        "video_info": {
            "frames": 49,
            "width": 832,
            "height": 480,
            "fps": 15,
            "duration_seconds": 3.27
        },
        "seed": 42,
        "task_type": "text2video",
        "file_uid": "12345-uuid-here",
        "user_id": "firebase_user_123"
    }
    
    # Image response with cloud storage
    image_response = {
        "images": [
            "https://firebasestorage.googleapis.com/v0/b/your-project.appspot.com/o/generating%2Ffirebase_user_456%2Fimage%2F67890_0.png?alt=media",
            "https://firebasestorage.googleapis.com/v0/b/your-project.appspot.com/o/generating%2Ffirebase_user_456%2Fimage%2F67890_1.png?alt=media"
        ],
        "image_url": "https://firebasestorage.googleapis.com/v0/b/your-project.appspot.com/o/generating%2Ffirebase_user_456%2Fimage%2F67890_0.png?alt=media",
        "seed": 123,
        "task_type": "text2img",
        "file_uid": "67890-uuid-here", 
        "user_id": "firebase_user_456"
    }
    
    print("\n📤 Expected Response Formats:")
    print("\n🎬 Video Response (Cloud Storage):")
    print(json.dumps(video_response, indent=2))
    
    print("\n🖼️ Image Response (Cloud Storage):")
    print(json.dumps(image_response, indent=2))

def firestore_database_structure():
    """Show the Firestore database structure created by the system"""
    
    database_structure = {
        "generations": {
            "firebase_user_123": {
                "files": {
                    "uuid-12345": {
                        "status": "completed",
                        "created_at": "2025-01-22T10:30:00Z",
                        "completed_at": "2025-01-22T10:35:00Z",
                        "request_data": {
                            "task_type": "text2video",
                            "prompt": "A majestic eagle soaring...",
                            "parameters": "{ video_width: 832, ... }",
                            "job_id": "runpod-job-abc123"
                        },
                        "generation_data": {
                            "videos": ["https://firebase..."],
                            "video_info": "{ frames: 49, ... }",
                            "seed": 42
                        },
                        "file_uid": "uuid-12345",
                        "user_id": "firebase_user_123"
                    }
                }
            },
            "firebase_user_456": {
                "files": {
                    "uuid-67890": {
                        "status": "completed",
                        "created_at": "2025-01-22T11:00:00Z", 
                        "completed_at": "2025-01-22T11:02:00Z",
                        "request_data": {
                            "task_type": "text2img",
                            "prompt": "A futuristic city...",
                            "parameters": "{ width: 1024, ... }"
                        },
                        "generation_data": {
                            "images": ["https://firebase...", "https://firebase..."],
                            "seed": 123
                        },
                        "file_uid": "uuid-67890",
                        "user_id": "firebase_user_456"
                    }
                }
            }
        }
    }
    
    print("\n🗄️ Firestore Database Structure:")
    print(json.dumps(database_structure, indent=2))

def environment_variables_needed():
    """Show the environment variables needed for cloud storage setup"""
    
    print("\n🔧 Environment Variables for Cloud Storage:")
    print("=" * 50)
    
    print("\n📱 Firebase Configuration:")
    print("FIREBASE_SERVICE_ACCOUNT_KEY=/path/to/service-account-key.json")
    print("# OR as JSON string:")
    print('FIREBASE_SERVICE_ACCOUNT_KEY=\'{"type": "service_account", "project_id": "your-project", ...}\'')
    print("FIREBASE_STORAGE_BUCKET=your-project.appspot.com")
    
    print("\n🔧 Dockerfile Example:")
    print("ENV FIREBASE_SERVICE_ACCOUNT_KEY=/app/firebase-key.json")
    print("ENV FIREBASE_STORAGE_BUCKET=your-project.appspot.com")
    print("COPY firebase-service-account-key.json /app/firebase-key.json")

if __name__ == "__main__":
    print("🚀 SDXL Worker Cloud Storage Integration Examples")
    print("=" * 60)
    
    # Show example requests
    video_req = create_video_request_with_cloud_storage()
    image_req = create_image_request_with_cloud_storage()
    fallback_req = create_fallback_request()
    
    # Show expected responses
    expected_cloud_response_format()
    
    # Show database structure
    firestore_database_structure()
    
    # Show environment setup
    environment_variables_needed()
    
    print("\n✨ Benefits of Cloud Storage Integration:")
    print("• 📦 Reduced response payload size (URLs instead of base64)")
    print("• 🚀 Faster API responses (no large data transfers)")
    print("• 📱 Better mobile app performance") 
    print("• 🗄️ Automatic database tracking of generations")
    print("• 🔄 Real-time status updates for your app")
    print("• 📊 User generation history and analytics")
    print("• 🔒 Secure, organized file storage by user")
    print("• 🔥 Firebase integration for seamless mobile development")
    
    print("\n🎯 Your Mobile App Integration:")
    print("1. Send request with user_id and file_uid")
    print("2. Listen to Firestore for status updates:")
    print("   generations/{user_id}/files/{file_uid}")
    print("3. When status changes to 'completed', get file URLs")
    print("4. Display images/videos directly from Firebase Storage URLs")

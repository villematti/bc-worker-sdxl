# Cloud Storage Integration for SDXL Worker

This worker now supports cloud storage integration with Firebase Storage and Firestore database. This allows you to:

- Upload generated images/videos to cloud storage instead of returning large base64 strings
- Track generation status and history in a database
- Provide real-time updates to your mobile app
- Organize files by user with proper access control

## 🏗️ Architecture

```
Mobile App → RunPod Worker → Firebase Storage + Firestore
     ↑                              ↓
     └─── Real-time status updates ─┘
```

### Request Flow:
1. Mobile app sends generation request with `user_id`, `file_uid`, and `use_cloud_storage: true`
2. Worker creates database entry with status "processing"
3. Worker generates image/video
4. Worker uploads files to Firebase Storage
5. Worker updates database with status "completed" and file URLs
6. Mobile app receives real-time database updates

## 📋 Prerequisites

### 1. Firebase Project Setup
1. Create a Firebase project at https://console.firebase.google.com
2. Enable Firebase Storage and Firestore Database
3. Create a service account:
   - Go to Project Settings → Service Accounts
   - Click "Generate new private key"
   - Download the JSON file

### 2. Firestore Security Rules
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Allow users to read/write their own generations
    match /generations/{userId}/files/{fileId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

### 3. Firebase Storage Security Rules
```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // Allow users to read/write their own files
    match /generating/{userId}/{fileType}/{fileName} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

## 🔧 Environment Variables

Add these to your RunPod environment:

```bash
# Firebase Configuration
FIREBASE_SERVICE_ACCOUNT_KEY=/path/to/service-account-key.json
FIREBASE_STORAGE_BUCKET=your-project.appspot.com

# Alternative: JSON string (for RunPod secrets)
FIREBASE_SERVICE_ACCOUNT_KEY='{"type": "service_account", "project_id": "your-project", ...}'
```

## 📱 API Usage

### Video Generation with Cloud Storage
```json
{
  "task_type": "text2video",
  "prompt": "A majestic eagle soaring through mountain peaks",
  "video_width": 832,
  "video_height": 480,
  "num_frames": 49,
  "fps": 15,
  
  "user_id": "firebase_user_123",
  "file_uid": "unique-generation-id",
  "use_cloud_storage": true
}
```

### Image Generation with Cloud Storage
```json
{
  "task_type": "text2img",
  "prompt": "A futuristic city skyline at sunset",
  "width": 1024,
  "height": 1024,
  "num_images": 2,
  
  "user_id": "firebase_user_456", 
  "file_uid": "unique-generation-id",
  "use_cloud_storage": true
}
```

### Response Format
```json
{
  "images": [
    "https://firebasestorage.googleapis.com/.../image_0.png",
    "https://firebasestorage.googleapis.com/.../image_1.png"
  ],
  "image_url": "https://firebasestorage.googleapis.com/.../image_0.png",
  "seed": 123,
  "task_type": "text2img",
  "file_uid": "unique-generation-id",
  "user_id": "firebase_user_456"
}
```

## 🗄️ Database Structure

### Firestore Collections
```
generations/
├── {user_id}/
    └── files/
        └── {file_uid}/
            ├── status: "processing" | "completed" | "failed"
            ├── created_at: timestamp
            ├── completed_at: timestamp
            ├── request_data: { original request parameters }
            ├── generation_data: { results with URLs }
            ├── file_uid: string
            └── user_id: string
```

### Firebase Storage Structure
```
generating/
├── {user_id}/
    ├── video/
    │   ├── {file_uid}.mp4
    │   └── {another_file_uid}.mp4
    └── image/
        ├── {file_uid}.png          (single image)
        ├── {file_uid}_0.png        (multiple images)
        └── {file_uid}_1.png
```

## 📱 Mobile App Integration

### 1. Listen for Real-time Updates
```javascript
// React Native / JavaScript example
import { onSnapshot, doc } from 'firebase/firestore';

const listenToGeneration = (userId, fileUid) => {
  const docRef = doc(db, 'generations', userId, 'files', fileUid);
  
  return onSnapshot(docRef, (doc) => {
    if (doc.exists()) {
      const data = doc.data();
      
      if (data.status === 'completed') {
        // Files are ready!
        const fileUrls = data.generation_data.images || [data.generation_data.video_url];
        displayFiles(fileUrls);
      } else if (data.status === 'processing') {
        showLoadingIndicator();
      }
    }
  });
};
```

### 2. Make Generation Request
```javascript
const generateContent = async (prompt, userId) => {
  const fileUid = generateUUID();
  
  // Start listening for updates
  const unsubscribe = listenToGeneration(userId, fileUid);
  
  // Make API request
  const response = await fetch('https://api.runpod.ai/v2/your-endpoint/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      input: {
        task_type: 'text2img',
        prompt: prompt,
        user_id: userId,
        file_uid: fileUid,
        use_cloud_storage: true
      }
    })
  });
  
  return { fileUid, unsubscribe };
};
```

## 🚀 Deployment

### Dockerfile Updates
```dockerfile
# Add Firebase dependencies
RUN pip install firebase-admin

# Copy service account key (if using file)
COPY firebase-service-account-key.json /app/firebase-key.json
ENV FIREBASE_SERVICE_ACCOUNT_KEY=/app/firebase-key.json
ENV FIREBASE_STORAGE_BUCKET=your-project.appspot.com
```

### RunPod Template
Set environment variables in your RunPod template:
- `FIREBASE_SERVICE_ACCOUNT_KEY`: Your service account JSON (as string)
- `FIREBASE_STORAGE_BUCKET`: Your Firebase Storage bucket name

## 🔄 Fallback Behavior

If Firebase is not configured or fails:
- Worker automatically falls back to base64 encoding
- Maintains backward compatibility
- No breaking changes to existing integrations

## 📊 Benefits

### Performance
- **50-90% smaller API responses** (URLs vs base64)
- **Faster mobile app loading** (progressive image loading)
- **Reduced bandwidth costs** for both client and server

### User Experience  
- **Real-time status updates** (processing → completed)
- **Generation history** (all past creations accessible)
- **Organized file management** (by user and generation)
- **Direct media URLs** (can be cached, shared, etc.)

### Developer Experience
- **Simple integration** (just add 3 parameters)
- **Graceful fallbacks** (works without Firebase)
- **Real-time notifications** (Firebase onSnapshot)
- **Scalable architecture** (Firebase handles file serving)
- **Mobile-first design** (built for Firebase ecosystem)

## 🔧 Testing

Test locally without Firebase:
```bash
python test_cloud_local.py
```

Test with example requests:
```bash  
python test_cloud_storage.py
```

The system automatically detects Firebase availability and provides appropriate fallbacks.

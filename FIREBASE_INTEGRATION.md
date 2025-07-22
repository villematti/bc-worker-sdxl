# Firebase Function Integration Guide

This document explains how to integrate the RunPod SDXL worker with Firebase Functions.

## Architecture Overview

```
Frontend → Firebase Function → RunPod Worker → Updates Firestore
```

1. **Frontend**: User submits generation request
2. **Firebase Function**: Creates initial Firestore document, generates UIDs, calls RunPod
3. **RunPod Worker**: Processes generation, uploads to Firebase Storage, updates Firestore
4. **Frontend**: Listens to Firestore for real-time updates

## Firebase Function Responsibilities

### 1. Generate UIDs
```javascript
const file_uid = crypto.randomUUID(); // or use Firebase Admin SDK
const user_id = context.auth.uid; // from authenticated user
```

### 2. Create Initial Firestore Document
```javascript
// For video generation
await admin.firestore()
  .collection('generations')
  .doc(user_id)
  .collection('videos')
  .doc(file_uid)
  .set({
    status: 'queued',
    created_at: admin.firestore.FieldValue.serverTimestamp(),
    request_data: {
      prompt: prompt,
      // ... other parameters
    },
    file_uid: file_uid,
    user_id: user_id
  });

// For image generation  
await admin.firestore()
  .collection('generations')
  .doc(user_id)
  .collection('images')
  .doc(file_uid)
  .set({
    status: 'queued',
    created_at: admin.firestore.FieldValue.serverTimestamp(),
    request_data: {
      prompt: prompt,
      // ... other parameters
    },
    file_uid: file_uid,
    user_id: user_id
  });
```

### 3. Call RunPod API
```javascript
const runpodResponse = await fetch('https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${RUNPOD_API_KEY}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    input: {
      prompt: prompt,
      user_id: user_id,           // ← Required: Firebase user ID
      file_uid: file_uid,         // ← Required: Generated file UID
      use_cloud_storage: true,    // ← Required: Enable cloud storage
      // ... other generation parameters
    }
  })
});
```

## RunPod Worker Responsibilities

### 1. Process Generation
- Receives `user_id` and `file_uid` from request
- Generates images/videos based on parameters

### 2. Upload to Firebase Storage
- Uploads files to: `generating/{user_id}/{type}/{file_uid}.{ext}`
- Files are made publicly accessible

### 3. Update Firestore
- Updates document at: `generations/{user_id}/{videos|images}/{file_uid}`
- Sets status: `queued` → `processing` → `completed` or `failed`
- Adds `generated: true` and `modified: timestamp` when ready
- Includes final URLs and generation data

## Firestore Document Lifecycle

### Initial State (Created by Firebase Function)
```javascript
{
  status: 'queued',
  created_at: <timestamp>,
  request_data: { /* original request */ },
  file_uid: 'uuid-here',
  user_id: 'user-uuid-here'
}
```

### During Processing (Updated by RunPod)
```javascript
{
  status: 'processing',
  // ... existing fields remain
}
```

### Completed (Updated by RunPod)
```javascript
{
  status: 'completed',
  completed_at: <timestamp>,
  generated: true,
  modified: <timestamp>,
  generation_data: {
    video_url: 'https://storage.googleapis.com/...',
    // or image_urls: ['url1', 'url2'],
    fps: 15 // for videos
  },
  // ... existing fields remain
}
```

### Failed (Updated by RunPod)
```javascript
{
  status: 'failed',
  completed_at: <timestamp>,
  error: 'Error message here',
  // ... existing fields remain
}
```

## Frontend Real-time Listening

```javascript
// Listen for video updates
const videosRef = collection(db, 'generations', user.uid, 'videos');
onSnapshot(videosRef, (snapshot) => {
  snapshot.docChanges().forEach((change) => {
    if (change.type === 'modified') {
      const data = change.doc.data();
      if (data.generated && data.status === 'completed') {
        // Video is ready! Show video_url
        console.log('Video ready:', data.generation_data.video_url);
      }
    }
  });
});

// Listen for image updates  
const imagesRef = collection(db, 'generations', user.uid, 'images');
onSnapshot(imagesRef, (snapshot) => {
  snapshot.docChanges().forEach((change) => {
    if (change.type === 'modified') {
      const data = change.doc.data();
      if (data.generated && data.status === 'completed') {
        // Images are ready! Show image_urls
        console.log('Images ready:', data.generation_data.image_urls);
      }
    }
  });
});
```

## Environment Variables for RunPod

Set these in RunPod environment:

```bash
FIREBASE_SERVICE_ACCOUNT_KEY={"type":"service_account","project_id":"..."}
FIREBASE_STORAGE_BUCKET=your-project.firebasestorage.app
```

## File Structure Summary

### Firebase Storage
```
generating/
  ├── {user_id}/
  │   ├── video/
  │   │   └── {file_uid}.mp4
  │   └── image/
  │       ├── {file_uid}.png
  │       └── {file_uid}_1.png (for multiple images)
```

### Firestore
```
generations/
  ├── {user_id}/
  │   ├── videos/
  │   │   └── {file_uid}/ (document with status, URLs, etc.)
  │   └── images/
  │       └── {file_uid}/ (document with status, URLs, etc.)
```

This architecture provides:
- ✅ Clean separation of concerns
- ✅ Real-time updates for frontend
- ✅ Proper error handling
- ✅ Easy querying by media type
- ✅ Scalable structure

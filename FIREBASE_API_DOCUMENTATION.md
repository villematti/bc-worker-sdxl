# 🔗 RunPod Worker API Documentation for Firebase Functions

## 📋 **Overview**

This document describes the API contract between Firebase Functions and the RunPod SDXL Worker for asynchronous image/video generation.

---

## 🚀 **API Endpoint**

```
POST https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync
```

**Headers:**
```
Authorization: Bearer {RUNPOD_API_KEY}
Content-Type: application/json
```

---

## 📥 **Request Format**

### **Required Input Structure:**
```json
{
  "input": {
    "prompt": "A red sports car on a mountain road",
    "user_id": "firebase_user_uid",
    "file_uid": "unique_generation_id", 
    "use_cloud_storage": true,
    
    // Optional parameters
    "width": 512,
    "height": 512,
    "num_images_per_prompt": 1,
    "num_inference_steps": 20,
    "guidance_scale": 7.5,
    "negative_prompt": "blurry, low quality",
    "seed": null,
    
    // Video-specific (optional)
    "num_frames": 16,
    "fps": 8,
    "video_width": 512,
    "video_height": 512,
    "video_guidance_scale": 5.0
  }
}
```

### **Required Parameters:**
- `prompt` (string): Text description for generation
- `user_id` (string): Firebase user UID
- `file_uid` (string): Unique identifier for this generation
- `use_cloud_storage` (boolean): Must be `true` for Firebase integration

### **Optional Parameters:**
- `width/height` (int): Image dimensions (256-1024)
- `num_images_per_prompt` (int): Number of images to generate (1-4)
- `num_inference_steps` (int): Quality vs speed tradeoff (10-50)
- `guidance_scale` (float): How closely to follow prompt (1.0-20.0)
- `negative_prompt` (string): What to avoid in generation
- `seed` (int): For reproducible results (null = random)

### **Video Parameters:**
- `num_frames` (int): Video length in frames (16-81)
- `fps` (int): Frames per second (6-15)
- `video_width/video_height` (int): Video dimensions
- `video_guidance_scale` (float): Video-specific guidance

---

## 📤 **Response Format**

### **✅ Success Response (200 OK)**

When the worker accepts the job for background processing:

```json
{
  "status": "accepted",
  "message": "Generation task accepted and processing",
  "user_id": "firebase_user_uid",
  "file_uid": "unique_generation_id",
  "task_type": "text2image"
}
```

**Response Fields:**
- `status`: Always `"accepted"` for successful job acceptance
- `message`: Human-readable confirmation message
- `user_id`: Echo of the input user_id
- `file_uid`: Echo of the input file_uid  
- `task_type`: Either `"text2image"` or `"text2video"`

### **❌ Error Response (400 Bad Request)**

When validation fails or required parameters are missing:

```json
{
  "error": "user_id and file_uid are required for cloud storage",
  "status": "failed"
}
```

**Common Error Messages:**
- `"Validation failed: {specific_validation_error}"`
- `"user_id and file_uid are required for cloud storage"`
- `"{field_name} is required"`
- `"{field_name} must be between {min} and {max}"`

---

## 🔄 **Processing Flow**

### **1. Firebase Function Workflow:**
```javascript
// 1. Create initial Firestore document
const docRef = doc(db, 'generations', userId, mediaType, fileUid);
await setDoc(docRef, {
  status: 'queued',
  created_at: serverTimestamp(),
  prompt: requestData.prompt,
  // ... other metadata
});

// 2. Call RunPod Worker
const response = await fetch(runpodEndpoint, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${RUNPOD_API_KEY}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    input: {
      prompt: requestData.prompt,
      user_id: userId,
      file_uid: fileUid,
      use_cloud_storage: true,
      ...otherParams
    }
  })
});

// 3. Handle immediate response
const result = await response.json();

if (result.status === 'accepted') {
  // Job accepted - worker will update Firestore
  return { success: true, fileUid, message: 'Generation started' };
} else {
  // Job rejected - update Firestore with error
  await updateDoc(docRef, {
    status: 'failed',
    error: true,
    error_message: result.error
  });
  throw new Error(result.error);
}
```

### **2. Worker Processing (Background):**
```
1. Validates input → Returns 200 OK immediately
2. Updates Firestore: status = "processing"
3. Generates images/video
4. Uploads to Firebase Storage
5. Updates Firestore: status = "completed" + URLs
```

---

## 📊 **Firestore Updates from Worker**

The worker will update the Firestore document at:
```
/generations/{user_id}/{media_type}/{file_uid}
```

Where `media_type` is:
- `"images"` for image generation
- `"videos"` for video generation

### **Status Progression:**
```
"queued" → "processing" → "completed" | "failed"
```

### **Success Document Structure:**
```json
{
  "generated": true,
  "error": false,
  "status": "completed",
  "completed_at": "2025-07-23T19:30:00Z",
  "modified": "2025-07-23T19:30:00Z",
  
  // For images
  "images": [
    "https://storage.googleapis.com/bc-image-gen.firebasestorage.app/generating/user123/image/file456.png",
    "https://storage.googleapis.com/bc-image-gen.firebasestorage.app/generating/user123/image/file456_1.png"
  ],
  "image_url": "https://storage.googleapis.com/bc-image-gen.firebasestorage.app/generating/user123/image/file456.png",
  "image_count": 2,
  
  // For videos  
  "videos": ["https://storage.googleapis.com/bc-image-gen.firebasestorage.app/generating/user123/video/file789.mp4"],
  "video_url": "https://storage.googleapis.com/bc-image-gen.firebasestorage.app/generating/user123/video/file789.mp4",
  "video_info": {
    "frames": 16,
    "fps": 8,
    "duration_seconds": 2.0,
    "width": 512,
    "height": 512
  },
  
  // Common fields
  "seed": 1234567890,
  "task_type": "text2image",
  "file_uid": "file456",
  "user_id": "user123"
}
```

### **Error Document Structure:**
```json
{
  "generated": false,
  "error": true,
  "status": "failed",
  "error_message": "CUDA Out of Memory during image generation",
  "error_type": "OutOfMemoryError",
  "failed_at": "2025-07-23T19:25:00Z",
  "modified": "2025-07-23T19:25:00Z",
  "file_uid": "file456",
  "user_id": "user123"
}
```

### **Error Types:**
- `"ModelNotAvailable"`: Video model not loaded
- `"OutOfMemoryError"`: GPU memory exhausted
- `"RuntimeError"`: Processing/tensor errors
- `"ConnectionError"`: Upload/storage failures
- `"Exception"`: General unexpected errors

---

## 🎯 **Firebase Function Implementation Example**

```javascript
import { httpsCallable } from 'firebase/functions';
import { doc, setDoc, onSnapshot, serverTimestamp } from 'firebase/firestore';

export async function generateImage(prompt, options = {}) {
  const userId = auth.currentUser.uid;
  const fileUid = crypto.randomUUID();
  const mediaType = options.numFrames ? 'videos' : 'images';
  
  try {
    // 1. Create initial document
    const docRef = doc(db, 'generations', userId, mediaType, fileUid);
    await setDoc(docRef, {
      status: 'queued',
      created_at: serverTimestamp(),
      prompt,
      generated: false,
      error: false,
      ...options
    });
    
    // 2. Call RunPod via Cloud Function
    const generateFunction = httpsCallable(functions, 'generateWithRunPod');
    const result = await generateFunction({
      prompt,
      user_id: userId,
      file_uid: fileUid,
      use_cloud_storage: true,
      ...options
    });
    
    // 3. Return listener for real-time updates
    return {
      fileUid,
      mediaType,
      docRef,
      unsubscribe: onSnapshot(docRef, (doc) => {
        const data = doc.data();
        if (data.generated) {
          console.log('✅ Generation complete:', data.images || data.video_url);
        } else if (data.error) {
          console.error('❌ Generation failed:', data.error_message);
        }
      })
    };
    
  } catch (error) {
    console.error('Failed to start generation:', error);
    throw error;
  }
}
```

---

## ⚡ **Key Integration Points**

### **1. Immediate Response Handling**
- ✅ **200 + "accepted"**: Job started successfully
- ❌ **400 + error**: Fix parameters and retry
- ⏱️ **Timeout**: Retry the request

### **2. Real-time Progress Tracking**
```javascript
// Listen for status changes
onSnapshot(docRef, (doc) => {
  const data = doc.data();
  
  switch(data.status) {
    case 'queued':
      showStatus('Queued for processing...');
      break;
    case 'processing':
      showStatus('Generating your content...');
      break;
    case 'completed':
      if (data.generated) {
        displayResults(data.images || [data.video_url]);
      }
      break;
    case 'failed':
      showError(`Failed: ${data.error_message}`);
      break;
  }
});
```

### **3. Error Recovery**
```javascript
function handleGenerationError(errorType, errorMessage) {
  switch(errorType) {
    case 'OutOfMemoryError':
      return 'Try reducing image size or complexity';
    case 'ModelNotAvailable':
      return 'Video generation temporarily unavailable';
    default:
      return 'Please try again in a moment';
  }
}
```

---

## 📝 **Testing Examples**

### **Image Generation Test:**
```bash
curl -X POST https://api.runpod.ai/v2/YOUR_ENDPOINT/runsync \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "prompt": "A sunset over mountains",
      "user_id": "test-user",
      "file_uid": "test-img-001",
      "use_cloud_storage": true,
      "width": 512,
      "height": 512
    }
  }'
```

**Expected Response:**
```json
{
  "status": "accepted",
  "message": "Generation task accepted and processing",
  "user_id": "test-user", 
  "file_uid": "test-img-001",
  "task_type": "text2image"
}
```

### **Video Generation Test:**
```bash
curl -X POST https://api.runpod.ai/v2/YOUR_ENDPOINT/runsync \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "prompt": "Waves crashing on beach",
      "user_id": "test-user",
      "file_uid": "test-vid-001", 
      "use_cloud_storage": true,
      "num_frames": 16,
      "fps": 8
    }
  }'
```

**Expected Response:**
```json
{
  "status": "accepted",
  "message": "Generation task accepted and processing",
  "user_id": "test-user",
  "file_uid": "test-vid-001", 
  "task_type": "text2video"
}
```

---

## 🔍 **Monitoring & Debugging**

### **Check Processing Status:**
```javascript
// Get all active generations
const activeGens = await getDocs(
  query(
    collection(db, 'generations', userId, 'images'),
    where('status', 'in', ['queued', 'processing']),
    orderBy('created_at', 'desc')
  )
);

// Check for stuck jobs (processing > 5 minutes)
const stuckJobs = await getDocs(
  query(
    collection(db, 'generations', userId, 'images'),
    where('status', '==', 'processing'),
    where('modified', '<', fiveMinutesAgo)
  )
);
```

### **Error Analytics:**
```javascript
// Get failure rate
const failures = await getDocs(
  query(
    collectionGroup(db, 'images'),
    where('error', '==', true),
    where('failed_at', '>', last24Hours)
  )
);

console.log(`Failure rate: ${failures.size} failures in 24h`);
```

---

## 🎉 **Summary**

- **✅ Call worker** → Get immediate `"accepted"` response
- **✅ Worker processes** → Updates Firestore in real-time  
- **✅ Listen to Firestore** → Get results as they complete
- **✅ Handle errors** → Comprehensive error information available
- **✅ No polling needed** → Real-time updates via Firestore listeners

**Your Firebase Function just needs to make the API call and listen to Firestore!** 🚀

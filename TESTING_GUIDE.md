# 🧪 Testing Guide - Copy-Paste Examples

## 🚀 **Quick Test Examples**

### **Test 1: Simple Image Generation**
```json
{
  "input": {
    "prompt": "A red sports car on a mountain road",
    "user_id": "test-user-001",
    "file_uid": "test-image-001", 
    "use_cloud_storage": true,
    "width": 512,
    "height": 512,
    "num_inference_steps": 20,
    "guidance_scale": 7.5
  }
}
```

**Expected Response:**
```json
{
  "status": "success",
  "images": [
    "https://storage.googleapis.com/bc-image-gen.firebasestorage.app/generating/test-user-001/image/test-image-001.png"
  ],
  "seed": 1234567890,
  "execution_time": 15.2
}
```

**Expected Firestore Document:** `generations/test-user-001/images/test-image-001`
```json
{
  "status": "completed",
  "generated": true,
  "modified": "2025-07-22T19:30:00Z",
  "generation_data": {
    "image_urls": ["https://storage.googleapis.com/..."],
    "status": "completed",
    "image_count": 1
  }
}
```

---

### **Test 2: Multiple Images**
```json
{
  "input": {
    "prompt": "A cute golden retriever puppy",
    "user_id": "test-user-002",
    "file_uid": "test-multi-002",
    "use_cloud_storage": true,
    "width": 512,
    "height": 512,
    "num_inference_steps": 15,
    "guidance_scale": 8.0
  }
}
```

**Expected Response:**
```json
{
  "status": "success", 
  "images": [
    "https://storage.googleapis.com/bc-image-gen.firebasestorage.app/generating/test-user-002/image/test-multi-002_0.png",
    "https://storage.googleapis.com/bc-image-gen.firebasestorage.app/generating/test-user-002/image/test-multi-002_1.png",
    "https://storage.googleapis.com/bc-image-gen.firebasestorage.app/generating/test-user-002/image/test-multi-002_2.png"
  ],
  "seed": 1234567890,
  "execution_time": 22.8
}
```

---

### **Test 3: Video Generation**
```json
{
  "input": {
    "prompt": "A butterfly landing on a flower in slow motion",
    "user_id": "test-user-003", 
    "file_uid": "test-video-003",
    "use_cloud_storage": true,
    "width": 512,
    "height": 512,
    "num_frames": 16,
    "fps": 8,
    "num_inference_steps": 20,
    "guidance_scale": 7.5
  }
}
```

**Expected Response:**
```json
{
  "status": "success",
  "video": "https://storage.googleapis.com/bc-image-gen.firebasestorage.app/generating/test-user-003/video/test-video-003.mp4",
  "seed": 1234567890,
  "execution_time": 45.3
}
```

**Expected Firestore Document:** `generations/test-user-003/videos/test-video-003`
```json
{
  "status": "completed",
  "generated": true, 
  "modified": "2025-07-22T19:35:00Z",
  "generation_data": {
    "video_url": "https://storage.googleapis.com/...",
    "status": "completed",
    "fps": 8
  }
}
```

---

## 🔧 **cURL Commands for Testing**

### **Image Test:**
```bash
curl -X POST https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "prompt": "A serene lake with mountains in background",
      "user_id": "curl-test-user",
      "file_uid": "curl-test-image",
      "use_cloud_storage": true,
      "width": 512,
      "height": 512,
      "num_inference_steps": 15
    }
  }'
```

### **Video Test:**
```bash
curl -X POST https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "prompt": "Clouds moving across blue sky",
      "user_id": "curl-test-user",
      "file_uid": "curl-test-video", 
      "use_cloud_storage": true,
      "width": 512,
      "height": 512,
      "num_frames": 12,
      "fps": 6
    }
  }'
```

---

## 📱 **JavaScript/Fetch Examples**

### **Image Generation:**
```javascript
const response = await fetch('https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_RUNPOD_API_KEY',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    input: {
      prompt: "A magical forest with glowing mushrooms",
      user_id: "js-test-user",
      file_uid: "js-test-image",
      use_cloud_storage: true,
      width: 768,
      height: 768,
      num_inference_steps: 25,
      guidance_scale: 8.5
    }
  })
});

const result = await response.json();
console.log('Generated image URL:', result.images[0]);
```

### **Video Generation:**
```javascript
const response = await fetch('https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_RUNPOD_API_KEY',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    input: {
      prompt: "A campfire flickering at night",
      user_id: "js-test-user",
      file_uid: "js-test-video",
      use_cloud_storage: true,
      width: 512,
      height: 512,
      num_frames: 20,
      fps: 10,
      num_inference_steps: 20
    }
  })
});

const result = await response.json();
console.log('Generated video URL:', result.video);
```

---

## ✅ **Validation Checklist**

### **Before Testing:**
- [ ] RunPod endpoint is deployed with environment variables set
- [ ] `FIREBASE_SERVICE_ACCOUNT_KEY` contains valid JSON
- [ ] `FIREBASE_STORAGE_BUCKET` is set to `bc-image-gen.firebasestorage.app`
- [ ] Firebase project has Storage and Firestore enabled

### **During Testing:**
- [ ] Response contains Firebase Storage URLs (not base64)
- [ ] Files appear in Firebase Storage console
- [ ] Firestore documents are created and updated
- [ ] Status progresses: `queued` → `processing` → `completed`
- [ ] `generated: true` field appears when complete

### **After Testing:**
- [ ] Images/videos are publicly accessible via URLs
- [ ] Firestore documents contain correct metadata
- [ ] Multiple images create separate files with `_0`, `_1` suffixes
- [ ] Error handling works (try invalid prompts)

---

## 🐛 **Troubleshooting**

### **If you get base64 responses instead of URLs:**
- Check environment variables are set correctly
- Verify Firebase service account has correct permissions
- Check Firebase console for error messages

### **If Firestore documents aren't updating:**
- Verify Firestore is enabled in Firebase console
- Check service account has Firestore permissions
- Look for error messages in RunPod logs

### **If files don't appear in Storage:**
- Check Firebase Storage is enabled
- Verify bucket name matches environment variable
- Check service account has Storage permissions

---

## 🎯 **Success Indicators**

✅ **You know it's working when:**
- Response contains `storage.googleapis.com` URLs
- Files appear in Firebase Storage under `generating/{user_id}/`
- Firestore documents exist at `generations/{user_id}/{type}/{file_uid}`
- Documents have `generated: true` and proper URLs
- Frontend can listen to Firestore for real-time updates

🎉 **Happy testing!**

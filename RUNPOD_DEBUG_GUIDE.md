# RunPod Firebase Upload Debugging Guide

## ✅ LOCAL TEST RESULTS
- Firebase credentials: VALID ✅
- Firebase Storage uploads: WORKING ✅  
- Firestore database updates: WORKING ✅
- Code functionality: WORKING ✅

## 🔍 RUNPOD DEPLOYMENT TROUBLESHOOTING

Since Firebase works locally but fails in RunPod, the issue is environment-specific. Here's what to check:

### 1. Environment Variables Setup in RunPod
Ensure these environment variables are set correctly in RunPod:

```bash
FIREBASE_SERVICE_ACCOUNT_KEY='{"type":"service_account","project_id":"bc-image-gen",...}'
FIREBASE_STORAGE_BUCKET=bc-image-gen.firebasestorage.app
```

**Common Issues:**
- JSON not properly escaped in RunPod environment
- Missing quotes around the JSON string
- Truncated JSON due to character limits

### 2. Network Connectivity Issues
RunPod containers might have network restrictions:

**Test in RunPod container:**
```python
import requests
try:
    response = requests.get('https://firebase.googleapis.com')
    print(f"Firebase connectivity: {response.status_code}")
except Exception as e:
    print(f"Network error: {e}")
```

### 3. Background Thread Execution
The async architecture uses background threads that might not complete in RunPod:

**Potential Issues:**
- Container shutdown before background thread completes
- Thread exceptions not being logged
- Resource constraints killing background processes

### 4. Logging and Error Visibility
Add comprehensive logging to see what's happening:

```python
# Add to RunPod deployment
import sys
import logging

# Configure logging to see all output
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
logger = logging.getLogger(__name__)

# Add to background processing
logger.info(f"Starting background processing for {user_id}/{file_uid}")
```

### 5. Firebase Dependencies
Ensure `firebase-admin` is properly installed in RunPod container:

**Check in RunPod:**
```python
try:
    import firebase_admin
    print(f"Firebase admin version: {firebase_admin.__version__}")
except ImportError as e:
    print(f"Firebase admin not available: {e}")
```

### 6. Immediate vs Background Processing
Test if the issue is with background threading by temporarily making it synchronous:

**Quick Test Fix:**
```python
# In generate_image(), temporarily replace:
thread = threading.Thread(target=background_process, daemon=True)
thread.start()

# With direct call:
background_process()  # This will block but show if upload works
```

## 🔧 DEBUGGING STEPS FOR RUNPOD

1. **Check Environment Variables**
   ```python
   print("FIREBASE_SERVICE_ACCOUNT_KEY present:", bool(os.environ.get("FIREBASE_SERVICE_ACCOUNT_KEY")))
   print("FIREBASE_STORAGE_BUCKET:", os.environ.get("FIREBASE_STORAGE_BUCKET"))
   ```

2. **Test Firebase Initialization**
   ```python
   from cloud_storage import cloud_storage
   print("Storage type:", cloud_storage.storage_type)
   print("Storage bucket:", type(cloud_storage.storage_bucket))
   ```

3. **Test Simple Upload**
   ```python
   # Add this test endpoint to RunPod handler
   if job_input.get("test_firebase"):
       from PIL import Image
       test_img = Image.new('RGB', (10, 10), 'red')
       # Test upload directly
   ```

4. **Monitor Background Threads**
   ```python
   import threading
   print(f"Active threads: {threading.active_count()}")
   for thread in threading.enumerate():
       print(f"Thread: {thread.name}, alive: {thread.is_alive()}")
   ```

## 🎯 MOST LIKELY ISSUES

1. **Environment Variable Format**: The JSON service account key might not be properly formatted in RunPod
2. **Background Thread Termination**: RunPod might be killing the container before background upload completes
3. **Network Restrictions**: RunPod might block Firebase API calls
4. **Resource Limits**: Memory/CPU limits might prevent Firebase SDK from working

## 🚀 IMMEDIATE ACTION PLAN

1. Add debug logging to see exactly where it fails in RunPod
2. Test synchronous upload (no background thread) to isolate threading issues
3. Verify environment variables are properly set in RunPod console
4. Check RunPod logs for any Firebase-related error messages

The code is correct - this is a deployment/environment issue!

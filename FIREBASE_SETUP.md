# Firebase Service Account Setup Guide

## 🔥 What Service Account Do You Need?

You need a **Firebase Service Account** with the following permissions:

### Required Services:
1. **Firebase Storage** - File uploads and management
2. **Firestore Database** - Real-time status tracking  
3. **Firebase Admin SDK** - Server-side operations

### Required Roles:
- **Firebase Admin** or **Editor** role on your project
- **Storage Admin** - Upload/delete files in Firebase Storage
- **Cloud Datastore Owner** - Read/write Firestore documents

## 🏗️ Step-by-Step Firebase Setup

### 1. Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com)
2. Click "Create a project" or "Add project"
3. Enter project name (e.g., "my-sdxl-app")
4. Enable Google Analytics (optional)
5. Click "Create project"

### 2. Enable Required Services

#### Enable Firebase Storage:
1. In Firebase Console → **Storage**
2. Click "Get started"
3. Choose **Start in test mode** (we'll add security rules later)
4. Select a **storage location** (choose closest to your users)
5. Click "Done"

#### Enable Firestore Database:
1. In Firebase Console → **Firestore Database**
2. Click "Create database"
3. Choose **Start in test mode**
4. Select a **database location** (same region as Storage)
5. Click "Done"

### 3. Create Service Account

#### Method A: Firebase Console (Recommended)
1. Go to **Project Settings** (gear icon) → **Service accounts**
2. Click **"Generate new private key"**
3. Click **"Generate key"** → Downloads JSON file
4. Save this file securely (you'll need it for deployment)

#### Method B: Google Cloud Console
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select your Firebase project
3. Navigate to **IAM & Admin** → **Service Accounts**
4. Click **"Create Service Account"**
5. Enter details:
   - **Name**: `sdxl-worker-service`
   - **Description**: `Service account for SDXL worker cloud storage`
6. Click **"Create and continue"**
7. Add roles:
   - `Firebase Admin SDK Administrator Service Agent`
   - `Storage Admin`
   - `Cloud Datastore Owner`
8. Click **"Continue"** → **"Done"**
9. Click on the created service account
10. Go to **"Keys"** tab → **"Add Key"** → **"Create new key"**
11. Choose **JSON** format → **"Create"**

### 4. Configure Security Rules

#### Firestore Security Rules:
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Allow users to read/write their own generations
    match /generations/{userId}/files/{fileId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Allow service account (server-side) to write all documents
    match /{document=**} {
      allow read, write: if request.auth.token.firebase.sign_in_provider == 'custom';
    }
  }
}
```

#### Firebase Storage Security Rules:
```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // Allow users to read/write their own files
    match /generating/{userId}/{fileType}/{fileName} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Allow service account (server-side) to write all files
    match /{allPaths=**} {
      allow read, write: if request.auth.token.firebase.sign_in_provider == 'custom';
    }
  }
}
```

### 5. Get Configuration Details

From your Firebase project, you'll need:

1. **Storage Bucket Name**:
   - Go to **Storage** → copy the bucket name (e.g., `your-project.appspot.com`)

2. **Service Account Key**:
   - The JSON file you downloaded in step 3

## 🚀 Environment Configuration

### For RunPod Deployment:

**Option A: JSON File (Recommended for local testing)**
```bash
FIREBASE_SERVICE_ACCOUNT_KEY=/path/to/service-account-key.json
FIREBASE_STORAGE_BUCKET=your-project.appspot.com
```

**Option B: JSON String (Recommended for RunPod)**
```bash
FIREBASE_SERVICE_ACCOUNT_KEY='{"type": "service_account", "project_id": "your-project", "private_key_id": "abc123", "private_key": "-----BEGIN PRIVATE KEY-----\nMIIE...", "client_email": "sdxl-worker@your-project.iam.gserviceaccount.com", "client_id": "123", "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token", "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs", "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/sdxl-worker%40your-project.iam.gserviceaccount.com"}'
FIREBASE_STORAGE_BUCKET=your-project.appspot.com
```

### For Dockerfile:
```dockerfile
# Copy service account key
COPY firebase-service-account-key.json /app/firebase-key.json

# Set environment variables
ENV FIREBASE_SERVICE_ACCOUNT_KEY=/app/firebase-key.json
ENV FIREBASE_STORAGE_BUCKET=your-project.appspot.com
```

## ✅ Testing Your Setup

### 1. Test Connection Locally:
```bash
# Install Firebase Admin SDK
pip install firebase-admin

# Test the configuration
python test_cloud_local.py
```

### 2. Expected Output:
```
✅ Firebase initialized with bucket: your-project.appspot.com
✅ Storage type detected: firebase
✅ Uploaded to Firebase Storage: generating/test_user/image/test-123.png
✅ Created generation request: generations/test_user/files/test-123
✅ Updated Firestore: generations/test_user/files/test-123
```

## 🔒 Security Best Practices

1. **Never commit service account keys** to version control
2. **Use environment variables** for all sensitive data
3. **Limit service account permissions** to only what's needed
4. **Enable Firebase Security Rules** to protect user data
5. **Regularly rotate service account keys** (every 90 days)
6. **Monitor usage** in Firebase Console for unusual activity

## 🐛 Troubleshooting

### Common Errors:

**"Missing FIREBASE_SERVICE_ACCOUNT_KEY"**
- Ensure environment variable is set correctly
- Check JSON format is valid

**"Permission denied"**
- Verify service account has required roles
- Check Firebase Security Rules allow server access

**"Bucket not found"**
- Verify bucket name is correct (usually `projectname.appspot.com`)
- Ensure Firebase Storage is enabled

**"Invalid credentials"**
- Re-download service account key
- Verify JSON file is not corrupted

### Debug Mode:
Add this to test Firebase connectivity:
```python
import firebase_admin
from firebase_admin import credentials

# Test credentials
try:
    cred = credentials.Certificate('path/to/service-account-key.json')
    app = firebase_admin.initialize_app(cred)
    print("✅ Firebase credentials valid!")
except Exception as e:
    print(f"❌ Firebase error: {e}")
```

## 💰 Cost Considerations

### Firebase Pricing (as of 2025):
- **Storage**: $0.026/GB/month
- **Download**: $0.12/GB  
- **Operations**: $0.04/10K operations
- **Firestore**: $0.18/100K reads, $0.18/100K writes

### Estimated Monthly Costs:
- **1000 videos** (50MB each): ~$1.50 storage + $6.00 downloads = $7.50
- **10000 images** (2MB each): ~$0.60 storage + $2.40 downloads = $3.00
- **Database operations**: ~$1.00

**Total: ~$12/month for moderate usage**

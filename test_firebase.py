#!/usr/bin/env python3

import os

# Set mock Firebase credentials
os.environ['FIREBASE_SERVICE_ACCOUNT_KEY'] = '{"type": "service_account", "project_id": "test"}'
os.environ['FIREBASE_STORAGE_BUCKET'] = 'test-bucket.appspot.com'

print("Testing Firebase initialization with mock credentials...")

try:
    from cloud_storage import cloud_storage
    print(f"✅ Cloud storage type: {cloud_storage.storage_type}")
    print(f"✅ Storage bucket: {cloud_storage.storage_bucket}")
    print(f"✅ Firestore DB: {cloud_storage.firestore_db}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

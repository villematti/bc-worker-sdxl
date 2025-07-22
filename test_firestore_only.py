"""
Simple Firestore connectivity test
"""
import os

# Set environment variables
os.environ['FIREBASE_SERVICE_ACCOUNT_KEY'] = 'storage_access.json'
os.environ['FIREBASE_STORAGE_BUCKET'] = 'bc-image-gen.firebasestorage.app'

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    
    # Initialize Firebase
    service_account_key = os.environ.get("FIREBASE_SERVICE_ACCOUNT_KEY")
    cred = credentials.Certificate(service_account_key)
    
    if not firebase_admin._apps:
        app = firebase_admin.initialize_app(cred)
    
    # Test Firestore connection
    db = firestore.client()
    
    print("🔗 Testing Firestore connection...")
    
    # Try to create a simple test document
    test_ref = db.collection('test').document('connectivity')
    test_ref.set({
        'test': True,
        'timestamp': firestore.SERVER_TIMESTAMP
    })
    
    print("✅ Firestore write successful!")
    
    # Try to read it back
    doc = test_ref.get()
    if doc.exists:
        print("✅ Firestore read successful!")
        print(f"📄 Document data: {doc.to_dict()}")
    else:
        print("❌ Document not found after write")
    
    # Clean up test document
    test_ref.delete()
    print("🧹 Test document cleaned up")
    
except Exception as e:
    print(f"❌ Firestore test failed: {e}")
    print("\n💡 Possible solutions:")
    print("1. Create Firestore database: https://console.firebase.google.com/project/bc-image-gen/firestore")
    print("2. Check service account permissions")
    print("3. Verify service account has 'Cloud Datastore User' role")

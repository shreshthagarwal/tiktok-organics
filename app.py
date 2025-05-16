from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
import uuid

load_dotenv()

app = Flask(__name__)

# Initialize Firebase
firebase_creds = {
    "type": os.getenv('FIREBASE_TYPE'),
    "project_id": os.getenv('FIREBASE_PROJECT_ID'),
    "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
    "private_key": os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),
    "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
    "client_id": os.getenv('FIREBASE_CLIENT_ID'),
    "auth_uri": os.getenv('FIREBASE_AUTH_URI'),
    "token_uri": os.getenv('FIREBASE_TOKEN_URI'),
    "auth_provider_x509_cert_url": os.getenv('FIREBASE_AUTH_PROVIDER_CERT_URL'),
    "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_CERT_URL')
}

cred = credentials.Certificate(firebase_creds)
firebase_admin.initialize_app(cred)
db = firestore.client()

# TikTok Config
CLIENT_KEY = os.getenv('TIKTOK_CLIENT_KEY')
CLIENT_SECRET = os.getenv('TIKTOK_CLIENT_SECRET')
REDIRECT_URI = 'https://tiktok-organics-1.onrender.com/'

@app.route('/')
def handle_callback():
    if 'code' in request.args:
        # Exchange code for tokens
        response = requests.post(
            "https://open.tiktokapis.com/v2/oauth/token/",
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            data={
                'client_key': CLIENT_KEY,
                'client_secret': CLIENT_SECRET,
                'code': request.args['code'],
                'grant_type': 'authorization_code',
                'redirect_uri': REDIRECT_URI
            }
        )
        
        if response.status_code == 200:
            token_data = response.json()
            user_id = token_data.get('open_id', str(uuid.uuid4()))
            
            # Store in Firestore
            db.collection('tiktok_users').document(user_id).set({
                'tokens': {
                    'access_token': token_data['access_token'],
                    'refresh_token': token_data.get('refresh_token'),
                    'expires_at': firestore.SERVER_TIMESTAMP
                },
                'user_info': {
                    'scopes': token_data.get('scope', '').split(',')
                }
            }, merge=True)
            
            return f"""
            <html>
              <body>
                <h1>Authentication Successful</h1>
                <p>User ID: {user_id}</p>
                <script>
                  // Pass to frontend
                  localStorage.setItem('tiktok_user_id', '{user_id}');
                  window.close(); // If opened in popup
                </script>
              </body>
            </html>
            """
        
        return f"Error: {response.text}", 400
    
    return "Waiting for TikTok callback..."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

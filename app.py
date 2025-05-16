from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuration
CLIENT_KEY = os.getenv('TIKTOK_CLIENT_KEY')
CLIENT_SECRET = os.getenv('TIKTOK_CLIENT_SECRET')
REDIRECT_URI = 'https://tiktok-organics-1.onrender.com/'

# Token storage (volatile - use Redis/DB in production)
tokens = {}

@app.route('/home')
def home():
    return "Server is running - TikTok OAuth ready"

@app.route('/')
def handle_callback():
    if 'code' in request.args:
        # Token exchange
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
            tokens.update(response.json())
            return "Authentication successful! Frontend can now fetch tokens."
        
        return f"Error: {response.json().get('message', 'Token exchange failed')}", 400
    
    return "Waiting for TikTok callback..."

@app.route('/get-tokens')
def provide_tokens():
    if not tokens.get('access_token'):
        return jsonify({'error': 'No tokens available'}), 404
    
    return jsonify({
        'access_token': tokens['access_token'],
        'expires_in': tokens.get('expires_in'),
        'refresh_token': tokens.get('refresh_token')  # Only include if needed
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

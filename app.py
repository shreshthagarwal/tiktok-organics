from flask import Flask, request, jsonify, redirect
import secrets
import hashlib
import base64
import requests
import os
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables
load_dotenv()

# TikTok OAuth configuration
CLIENT_KEY = os.getenv('TIKTOK_CLIENT_KEY')
CLIENT_SECRET = os.getenv('TIKTOK_CLIENT_SECRET')
REDIRECT_URI = os.getenv('TIKTOK_REDIRECT_URI')
SCOPE = os.getenv('TIKTOK_SCOPE')

# PKCE generation
def generate_code_verifier():
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b'=').decode('utf-8')

def generate_code_challenge(code_verifier):
    digest = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b'=').decode('utf-8')

# Store verifier temporarily (in memory for demo purposes)
verifier_store = {}

@app.route('/get-auth-url', methods=['GET'])
def get_auth_url():
    state = secrets.token_hex(8)
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)

    # Save verifier by state
    verifier_store[state] = code_verifier

    auth_url = (
        f"https://www.tiktok.com/v2/auth/authorize"
        f"?client_key={CLIENT_KEY}"
        f"&response_type=code"
        f"&scope={SCOPE}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&state={state}"
        f"&code_challenge={code_challenge}"
        f"&code_challenge_method=S256"
    )

    return jsonify({"auth_url": auth_url})


@app.route('/callback')
def callback():
    code = request.args.get('code')
    state = request.args.get('state')

    if not code or not state or state not in verifier_store:
        return "Missing or invalid parameters", 400

    code_verifier = verifier_store[state]

    token_url = 'https://open.tiktokapis.com/v2/oauth/token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'client_key': CLIENT_KEY,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI,
        'code_verifier': code_verifier
    }

    response = requests.post(token_url, headers=headers, data=data)
    if response.status_code != 200:
        return f"Failed to get token: {response.text}", 500

    token_data = response.json()
    # Store or return access_token and refresh_token
    return jsonify(token_data)


if __name__ == '__main__':
    app.run(host='localhost', port=5000, ssl_context=('cert.pem', 'key.pem'))

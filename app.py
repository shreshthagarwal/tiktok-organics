from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>Hello</h1>"

@app.route('/callback')
def callback():
    code = request.args.get('code')
    state = request.args.get('state')
    if code:
        print(f"Received code: {code}")
        return f"<h1>Authorization code received</h1><p>{code}</p>"
    return "<h1>No code received</h1>", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

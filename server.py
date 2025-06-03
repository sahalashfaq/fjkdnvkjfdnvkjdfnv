from flask import Flask, request, jsonify
import requests
import time
from urllib.parse import urlparse
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for Streamlit communication

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
HEADERS = {'User-Agent': USER_AGENT}

def validate_url(url):
    """Ensure URL has proper formatting"""
    parsed = urlparse(url)
    if not parsed.scheme:
        url = 'http://' + url
    return url

@app.route('/check', methods=['POST'])
def check_websites():
    urls = request.json.get('urls', [])
    results = []
    
    for url in urls:
        try:
            validated_url = validate_url(url)
            start_time = time.time()
            
            response = requests.head(
                validated_url,
                headers=HEADERS,
                allow_redirects=True,
                timeout=10
            )
            
            latency = round((time.time() - start_time) * 1000, 2)  # ms
            final_url = response.url if response.url != validated_url else None
            
            results.append({
                'original_url': url,
                'final_url': final_url,
                'status_code': response.status_code,
                'status': 'Live' if response.status_code < 400 else 'Down',
                'latency_ms': latency,
                'error': None,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            results.append({
                'original_url': url,
                'final_url': None,
                'status_code': None,
                'status': 'Error',
                'latency_ms': None,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
    
    return jsonify(results)

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files (CSS)"""
    return app.send_static_file(filename)

if __name__ == '__main__':
    app.run(port=5000, debug=True)
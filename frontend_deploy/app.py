#!/usr/bin/env python3
"""
Simple Flask app to serve Streamlit
"""

import os
import subprocess
import threading
import time
from flask import Flask, redirect

# Create Flask app
app = Flask(__name__)

# Start Streamlit in a separate thread
def start_streamlit():
    """Start Streamlit server"""
    time.sleep(5)  # Give Flask time to start
    subprocess.run([
        'python', '-m', 'streamlit', 'run', 
        'streamlit_app_deploy.py',
        '--server.port=8502',
        '--server.headless=true',
        '--server.enableCORS=false'
    ])

@app.route('/')
def index():
    """Redirect to Streamlit app"""
    return redirect('http://localhost:8502')

@app.route('/health')
def health():
    """Health check endpoint"""
    return {'status': 'healthy', 'service': 'Frontend Proxy'}

if __name__ == '__main__':
    # Start Streamlit in background
    streamlit_thread = threading.Thread(target=start_streamlit)
    streamlit_thread.daemon = True
    streamlit_thread.start()
    
    # Start Flask app
    port = int(os.environ.get('PORT', 8501))
    app.run(host='0.0.0.0', port=port, debug=False)

# For EB deployment
application = app
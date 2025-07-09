#!/usr/bin/env python3
"""
GitHub webhook handler for automatic knowledge base updates
"""

import os
import json
import hashlib
import hmac
from pathlib import Path
from flask import Flask, request, jsonify
import threading
import time

app = Flask(__name__)

# Configuration
WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "your-webhook-secret")
REPO_URL = "https://github.com/SFang-cmd/obiKnowledge"
UPDATE_FLAG_FILE = Path(__file__).parent / "data" / ".update_required"

def verify_signature(payload_body, signature_header):
    """Verify GitHub webhook signature"""
    if not signature_header:
        return False
    
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        payload_body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected_signature}", signature_header)

def trigger_update():
    """Create a flag file to signal that an update is needed"""
    UPDATE_FLAG_FILE.parent.mkdir(parents=True, exist_ok=True)
    UPDATE_FLAG_FILE.touch()
    print(f"Update flag created at {UPDATE_FLAG_FILE}")

@app.route('/webhook', methods=['POST'])
def github_webhook():
    """Handle GitHub webhook"""
    signature = request.headers.get('X-Hub-Signature-256')
    
    # Verify signature
    if not verify_signature(request.data, signature):
        return jsonify({'error': 'Invalid signature'}), 401
    
    # Parse payload
    payload = request.get_json()
    
    if not payload:
        return jsonify({'error': 'No JSON payload'}), 400
    
    # Check if this is a push event to main branch
    if (payload.get('ref') == 'refs/heads/main' and 
        payload.get('repository', {}).get('full_name') == 'SFang-cmd/obiKnowledge'):
        
        print(f"Received push to main branch for obiKnowledge")
        print(f"Commit: {payload.get('head_commit', {}).get('message', 'Unknown')}")
        
        # Trigger update
        trigger_update()
        
        return jsonify({
            'status': 'success',
            'message': 'Update triggered',
            'commit': payload.get('head_commit', {}).get('id', '')[:7]
        })
    
    return jsonify({'status': 'ignored', 'message': 'Not a main branch push'})

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'webhook_configured': bool(WEBHOOK_SECRET and WEBHOOK_SECRET != 'your-webhook-secret'),
        'update_pending': UPDATE_FLAG_FILE.exists()
    })

@app.route('/force-update', methods=['POST'])
def force_update():
    """Manually trigger an update"""
    trigger_update()
    return jsonify({'status': 'update triggered'})

if __name__ == '__main__':
    print("🔗 GitHub Webhook Handler")
    print(f"Monitoring: {REPO_URL}")
    print(f"Webhook secret configured: {bool(WEBHOOK_SECRET and WEBHOOK_SECRET != 'your-webhook-secret')}")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)
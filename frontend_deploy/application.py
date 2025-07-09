#!/usr/bin/env python3
"""
Frontend application entry point for Elastic Beanstalk
"""

import os
import subprocess
import sys

def main():
    """Main entry point for the frontend application"""
    # Get port from environment variable
    port = os.environ.get('PORT', '8501')
    
    # Set Streamlit server configuration
    os.environ['STREAMLIT_SERVER_PORT'] = port
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    os.environ['STREAMLIT_SERVER_ENABLE_CORS'] = 'false'
    
    # Launch Streamlit
    cmd = [
        sys.executable, '-m', 'streamlit', 'run', 
        'streamlit_app_deploy.py',
        '--server.port', port,
        '--server.headless', 'true',
        '--server.enableCORS', 'false'
    ]
    
    # Execute the command
    subprocess.run(cmd)

if __name__ == "__main__":
    main()

# For WSGI compatibility
application = None  # Streamlit doesn't use WSGI
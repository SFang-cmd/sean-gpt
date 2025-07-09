#!/usr/bin/env python3
"""
Launch script for Sean GPT application
"""

import subprocess
import sys
import os
from pathlib import Path

def check_backend_ready():
    """Check if backend is ready with knowledge base"""
    backend_path = Path(__file__).parent / "backend"
    chroma_path = backend_path / "data" / "chroma_db"
    
    if not chroma_path.exists():
        print("❌ Backend knowledge base not found")
        print("Please run the backend test first:")
        print("  cd backend")
        print("  source .venv/bin/activate")
        print("  python test_rag.py")
        return False
    
    print("✅ Backend knowledge base found")
    return True

def check_env_vars():
    """Check if required environment variables are set"""
    env_file = Path(__file__).parent / ".env"
    
    if not env_file.exists():
        print("❌ Environment file not found")
        print("Please create backend/.env with your OpenAI API key:")
        print("  OPENAI_API_KEY=your_key_here")
        return False
    
    # Read env file to check for API key
    with open(env_file) as f:
        content = f.read()
        if "OPENAI_API_KEY=sk-" in content or "OPENAI_API_KEY=your_openai_api_key_here" not in content:
            print("✅ OpenAI API key configured")
            return True
        else:
            print("❌ Please add your OpenAI API key to backend/.env")
            return False

def launch_streamlit():
    """Launch the Streamlit application"""
    frontend_path = Path(__file__).parent / "frontend"
    venv_python = frontend_path / ".venv" / "bin" / "python"
    # Use the simplified app
    streamlit_script = Path(__file__).parent / "streamlit_app_simple.py"
    
    if not venv_python.exists():
        print("❌ Frontend virtual environment not found")
        print("Please set up the frontend first:")
        print("  cd frontend")
        print("  python -m venv .venv")
        print("  source .venv/bin/activate")
        print("  pip install -r requirements.txt")
        return False
    
    print("🚀 Launching Sean GPT...")
    print("📝 The app will open in your browser")
    print("💡 Use the sidebar to initialize the pipeline and load knowledge base")
    print("-" * 50)
    
    # Launch streamlit
    try:
        subprocess.run([
            str(venv_python), "-m", "streamlit", "run", 
            str(streamlit_script),
            "--server.headless=false"
        ], cwd=str(frontend_path))
    except KeyboardInterrupt:
        print("\n👋 Sean GPT stopped")
    except Exception as e:
        print(f"❌ Error launching app: {e}")
        return False
    
    return True

def main():
    print("🤖 Sean GPT Launcher")
    print("=" * 30)
    
    # Check backend
    if not check_backend_ready():
        return False
    
    # Check environment
    if not check_env_vars():
        return False
    
    # Launch app
    return launch_streamlit()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
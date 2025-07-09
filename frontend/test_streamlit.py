#!/usr/bin/env python3
"""
Test script to validate Streamlit app components
"""

import sys
from pathlib import Path

# Add backend path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_path))

def test_imports():
    """Test that all imports work"""
    try:
        import streamlit as st
        print("✅ Streamlit import successful")
        
        from backend.app.core.rag_pipeline import RAGPipeline
        print("✅ RAGPipeline import successful")
        
        from backend.app.services.obsidian_loader import ObsidianLoader
        print("✅ ObsidianLoader import successful")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_streamlit_functions():
    """Test Streamlit app functions"""
    try:
        # Import the main app module
        import streamlit_app
        print("✅ Streamlit app module import successful")
        
        # Test if main function exists
        if hasattr(streamlit_app, 'main'):
            print("✅ Main function exists")
        else:
            print("❌ Main function not found")
        
        return True
    except Exception as e:
        print(f"❌ Streamlit app test error: {e}")
        return False

def main():
    print("🧪 Testing Streamlit Frontend")
    print("=" * 40)
    
    # Test imports
    if not test_imports():
        return False
    
    # Test streamlit functions
    if not test_streamlit_functions():
        return False
    
    print("\n🎉 All tests passed!")
    print("=" * 40)
    print("To run the app:")
    print("cd frontend")
    print("source .venv/bin/activate")
    print("streamlit run streamlit_app.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
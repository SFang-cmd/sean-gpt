#!/usr/bin/env python3
"""
Health check script for deployment monitoring
"""

import os
import sys
from pathlib import Path

def check_environment():
    """Check if environment is properly configured"""
    checks = {
        "OpenAI API Key": bool(os.getenv("OPENAI_API_KEY")),
        "Backend Directory": Path(__file__).parent.exists(),
        "Data Directory": (Path(__file__).parent / "data").exists(),
    }
    
    return checks

def check_dependencies():
    """Check if all required dependencies are available"""
    checks = {}
    
    try:
        import openai
        checks["OpenAI"] = True
    except ImportError:
        checks["OpenAI"] = False
    
    try:
        import chromadb
        checks["ChromaDB"] = True
    except ImportError:
        checks["ChromaDB"] = False
    
    try:
        import streamlit
        checks["Streamlit"] = True
    except ImportError:
        checks["Streamlit"] = False
    
    try:
        import langchain_openai
        checks["LangChain"] = True
    except ImportError:
        checks["LangChain"] = False
    
    return checks

def main():
    """Run health checks"""
    print("🏥 Sean GPT Health Check")
    print("=" * 30)
    
    # Environment checks
    print("\n📋 Environment:")
    env_checks = check_environment()
    for check, status in env_checks.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {check}")
    
    # Dependency checks
    print("\n📦 Dependencies:")
    dep_checks = check_dependencies()
    for check, status in dep_checks.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {check}")
    
    # Overall status
    all_checks = list(env_checks.values()) + list(dep_checks.values())
    if all(all_checks):
        print("\n🎉 All checks passed! Ready for deployment.")
        return 0
    else:
        print("\n⚠️ Some checks failed. Please fix before deployment.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Demo script to showcase Sean GPT functionality
"""

import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.rag_pipeline import RAGPipeline

def main():
    print("🚀 Sean GPT Demo")
    print("=" * 50)
    
    # Check for OpenAI key
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("❌ Please set OPENAI_API_KEY environment variable")
        print("You can add it to backend/.env file")
        return False
    
    print("✅ OpenAI API key found")
    
    # Initialize pipeline
    print("📊 Initializing RAG pipeline...")
    pipeline = RAGPipeline(
        openai_api_key=openai_key,
        chroma_persist_directory="./backend/data/chroma_db",
        chunk_size=1000,
        chunk_overlap=200
    )
    
    # Check if knowledge base exists
    stats = pipeline.get_collection_stats()
    if stats['total_chunks'] == 0:
        print("❌ No knowledge base found. Please run the backend test first:")
        print("cd backend && python test_rag.py")
        return False
    
    print(f"✅ Knowledge base loaded: {stats['total_chunks']} chunks")
    
    # Interactive demo
    print("\n💬 Interactive Demo")
    print("Ask questions about the knowledge base (type 'quit' to exit)")
    print("-" * 50)
    
    while True:
        try:
            question = input("\n🤔 Your question: ")
            
            if question.lower() in ['quit', 'exit', 'q']:
                break
                
            if not question.strip():
                continue
            
            print("🔍 Searching knowledge base...")
            response = pipeline.query(question, k=3)
            
            print(f"\n🤖 Sean GPT: {response.answer}")
            
            if response.sources:
                print(f"\n📚 Sources ({len(response.sources)}):")
                for i, source in enumerate(response.sources[:2], 1):
                    print(f"   {i}. {source['title']} (relevance: {1-source['distance']:.2f})")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n👋 Thanks for trying Sean GPT!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
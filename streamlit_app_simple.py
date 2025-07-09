#!/usr/bin/env python3
"""
Simple Sean GPT Streamlit app with hard-coded repository
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Add backend path to sys.path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    from app.core.rag_pipeline import RAGPipeline
    BACKEND_AVAILABLE = True
except ImportError as e:
    st.error(f"Backend import error: {e}")
    BACKEND_AVAILABLE = False

# Page config
st.set_page_config(
    page_title="Sean GPT - Simple",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f5f5f5;
        border-left: 4px solid #4caf50;
    }
    .success-box {
        background-color: #e8f5e8;
        color: #2e7d32;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #c8e6c9;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #ffebee;
        color: #c62828;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #ffcdd2;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'pipeline' not in st.session_state:
    st.session_state.pipeline = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'knowledge_base_loaded' not in st.session_state:
    st.session_state.knowledge_base_loaded = False

def initialize_pipeline():
    """Initialize the RAG pipeline"""
    if not BACKEND_AVAILABLE:
        st.error("Backend is not available. Please check your installation.")
        return None
        
    try:
        # Get OpenAI API key from environment
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if not openai_key:
            st.error("❌ OpenAI API key not found")
            st.info("💡 Set OPENAI_API_KEY environment variable")
            return None
        
        # Validate API key format
        if not openai_key.startswith('sk-'):
            st.error("❌ Invalid OpenAI API key format")
            return None
        
        # Initialize pipeline
        pipeline = RAGPipeline(
            openai_api_key=openai_key,
            chroma_persist_directory="./backend/data/chroma_db"
        )
        
        st.success("✅ Pipeline initialized successfully!")
        return pipeline
        
    except Exception as e:
        st.error(f"❌ Failed to initialize pipeline: {str(e)}")
        return None

def load_knowledge_base():
    """Load the default knowledge base"""
    if st.session_state.pipeline is None:
        st.error("❌ Pipeline not initialized")
        return False
    
    try:
        with st.spinner("🔄 Loading knowledge base from GitHub repository..."):
            stats = st.session_state.pipeline.setup_knowledge_base()
        
        st.success(f"✅ Knowledge base loaded! {stats['chunks_created']} chunks processed")
        return True
        
    except Exception as e:
        st.error(f"❌ Failed to load knowledge base: {str(e)}")
        return False

def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown('<h1 class="main-header">🧠 Sean GPT</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Your Personal Knowledge Assistant</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("🛠️ Setup")
        
        # Initialize Pipeline
        if st.button("⚡ Initialize Pipeline"):
            pipeline = initialize_pipeline()
            if pipeline:
                st.session_state.pipeline = pipeline
        
        # Load Knowledge Base
        if st.button("📚 Load Knowledge Base"):
            if load_knowledge_base():
                st.session_state.knowledge_base_loaded = True
        
        # Status indicators
        st.divider()
        st.header("📊 Status")
        
        if st.session_state.pipeline:
            st.success("✅ Pipeline Ready")
            
            # Show collection stats
            if st.session_state.pipeline.has_existing_data():
                stats = st.session_state.pipeline.get_collection_stats()
                st.info(f"📝 {stats['total_chunks']} chunks loaded")
                st.session_state.knowledge_base_loaded = True
            else:
                st.warning("⚠️ No knowledge base loaded")
        else:
            st.error("❌ Pipeline Not Initialized")
        
        # Force reload option
        if st.session_state.pipeline and st.button("🔄 Force Reload Knowledge Base"):
            with st.spinner("🗑️ Clearing and reloading..."):
                stats = st.session_state.pipeline.setup_knowledge_base(force_reload=True)
            st.success(f"✅ Reloaded! {stats['chunks_created']} chunks processed")
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.header("💬 Chat with Your Knowledge Base")
        
        # Display chat history
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f'<div class="chat-message user-message"><strong>You:</strong> {message["content"]}</div>', 
                           unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-message assistant-message"><strong>Sean GPT:</strong> {message["content"]}</div>', 
                           unsafe_allow_html=True)
        
        # Query input
        query = st.text_input("Ask a question about Sean's knowledge base:", key="query_input")
        
        col_query, col_settings = st.columns([3, 1])
        
        with col_query:
            if st.button("🔍 Ask", type="primary"):
                if not query:
                    st.error("Please enter a question")
                elif not st.session_state.pipeline:
                    st.error("Pipeline not initialized. Please initialize the pipeline first.")
                elif not st.session_state.knowledge_base_loaded:
                    st.error("Knowledge base not loaded. Please load the knowledge base first.")
                else:
                    # Add user message to history
                    st.session_state.chat_history.append({"role": "user", "content": query})
                    
                    # Query the pipeline
                    with st.spinner("🧠 Thinking..."):
                        try:
                            response = st.session_state.pipeline.query(query, k=top_k)
                            st.session_state.chat_history.append({"role": "assistant", "content": response.answer})
                            
                            # Display sources
                            if response.sources:
                                with st.expander("📚 Sources"):
                                    for i, source in enumerate(response.sources, 1):
                                        st.markdown(f"**Source {i}: {source['title']}**")
                                        st.markdown(f"File: `{source['file']}`")
                                        st.markdown(f"Headers: {source['headers']}")
                                        st.markdown(f"Tags: {source['tags']}")
                                        st.markdown(f"Preview: {source['content_preview']}")
                                        st.divider()
                        
                        except Exception as e:
                            error_msg = f"Error: {str(e)}"
                            st.error(error_msg)
                            st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
                    
                    # Rerun to update the display
                    st.rerun()
        
        with col_settings:
            top_k = st.selectbox("Results", [3, 5, 10], index=1)
    
    with col2:
        st.header("🔧 Actions")
        
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()
        
        # System info
        st.divider()
        st.subheader("ℹ️ Info")
        st.info(f"**Messages:** {len(st.session_state.chat_history)}")
        st.info(f"**Repository:** obiKnowledge")
        
        if st.session_state.pipeline:
            stats = st.session_state.pipeline.get_collection_stats()
            st.info(f"**Chunks:** {stats['total_chunks']}")

if __name__ == "__main__":
    main()
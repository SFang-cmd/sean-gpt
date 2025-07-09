import streamlit as st
import requests
import sys
import os
from pathlib import Path
import json
from typing import List, Dict, Any
import time
import hashlib

# Add backend path to sys.path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    from app.core.rag_pipeline import RAGPipeline
    from app.services.obsidian_loader import ObsidianLoader, clone_or_update_repo
    BACKEND_AVAILABLE = True
except ImportError as e:
    st.error(f"Backend import error: {e}")
    BACKEND_AVAILABLE = False

# Configuration - Your specific repository
REPO_URL = "https://github.com/SFang-cmd/obiKnowledge"
REPO_NAME = "obiKnowledge"
CHECK_INTERVAL_MINUTES = 30  # Check for updates every 30 minutes

# Page config
st.set_page_config(
    page_title="Sean GPT - Knowledge Assistant",
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
    .status-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
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
if 'last_repo_check' not in st.session_state:
    st.session_state.last_repo_check = 0
if 'repo_last_commit' not in st.session_state:
    st.session_state.repo_last_commit = ""

def initialize_pipeline():
    """Initialize the RAG pipeline with production-ready error handling"""
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
        
        # Test API key validity
        with st.spinner("🔑 Validating API key..."):
            try:
                from openai import OpenAI
                client = OpenAI(api_key=openai_key)
                client.models.list()
                st.success("✅ API key validated")
            except Exception as api_error:
                st.error(f"❌ API key validation failed: {str(api_error)}")
                return None
        
        # Initialize pipeline
        with st.spinner("🔧 Initializing RAG pipeline..."):
            pipeline = RAGPipeline(
                openai_api_key=openai_key,
                chroma_persist_directory=str(backend_path / "data" / "chroma_db"),
                chunk_size=1000,
                chunk_overlap=200
            )
        
        return pipeline
    except Exception as e:
        st.error(f"❌ Pipeline initialization failed: {str(e)}")
        return None

def get_latest_commit_sha():
    """Get the latest commit SHA from GitHub API"""
    try:
        api_url = f"https://api.github.com/repos/SFang-cmd/obiKnowledge/commits/main"
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            return response.json()['sha'][:7]  # Short SHA
        return None
    except Exception as e:
        print(f"Error fetching commit SHA: {e}")
        return None

def check_for_updates():
    """Check if the repository has been updated"""
    current_time = time.time()
    
    # Only check if enough time has passed
    if current_time - st.session_state.last_repo_check < CHECK_INTERVAL_MINUTES * 60:
        return False
    
    st.session_state.last_repo_check = current_time
    latest_commit = get_latest_commit_sha()
    
    if latest_commit and latest_commit != st.session_state.repo_last_commit:
        st.session_state.repo_last_commit = latest_commit
        return True
    
    return False

def load_knowledge_base():
    """Load Sean's knowledge base from the configured repository"""
    if st.session_state.pipeline is None:
        st.error("Pipeline not initialized")
        return False
    
    try:
        # Clone/update the repository
        with st.spinner("📥 Syncing with Sean's knowledge repository..."):
            local_repo_path = backend_path / "data" / "obiKnowledge"
            clone_or_update_repo(REPO_URL, str(local_repo_path))
            
            # Update the last commit SHA
            st.session_state.repo_last_commit = get_latest_commit_sha() or ""
        
        # Process documents
        progress_container = st.empty()
        with progress_container:
            with st.spinner("🔄 Processing Sean's notes and generating embeddings..."):
                st.info("Processing your complete college knowledge base...")
                
                # Ingest documents from the repository
                stats = st.session_state.pipeline.ingest_documents(str(local_repo_path))
            
        st.session_state.knowledge_base_loaded = True
        st.success(f"✅ Knowledge base loaded successfully!")
        st.info(f"📊 Processed {stats['documents_processed']} documents into {stats['chunks_created']} chunks")
        
        return True
        
    except Exception as e:
        st.error(f"Error loading knowledge base: {str(e)}")
        return False

def query_knowledge_base(question: str):
    """Query the knowledge base and return response"""
    if st.session_state.pipeline is None:
        st.error("Pipeline not initialized")
        return None
    
    try:
        with st.spinner("🧠 Searching Sean's knowledge..."):
            response = st.session_state.pipeline.query(question, k=5)
            return response
    except Exception as e:
        st.error(f"Error querying knowledge base: {str(e)}")
        return None

def display_sources(sources: List[Dict[str, Any]]):
    """Display source information"""
    if not sources:
        return
    
    st.subheader("📚 Sources from Sean's Notes")
    
    for i, source in enumerate(sources, 1):
        with st.expander(f"Source {i}: {source['title']} (relevance: {1-source['distance']:.2f})"):
            st.write(f"**File:** {source['file']}")
            if source['headers']:
                st.write(f"**Section:** {source['headers']}")
            if source['tags']:
                st.write(f"**Tags:** {source['tags']}")
            st.write(f"**Content Preview:**")
            st.write(source['content_preview'])

def main():
    # Header
    st.markdown('<h1 class="main-header">🧠 Sean GPT</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">AI assistant trained on Sean\'s complete college knowledge base</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ System Status")
        
        # Backend status
        if BACKEND_AVAILABLE:
            st.success("✅ Backend available")
        else:
            st.error("❌ Backend not available")
            st.stop()
        
        # Repository info
        st.subheader("📚 Knowledge Source")
        st.info(f"**Repository:** {REPO_NAME}")
        st.info(f"**Auto-sync:** Every {CHECK_INTERVAL_MINUTES} minutes")
        
        if st.session_state.repo_last_commit:
            st.info(f"**Latest sync:** {st.session_state.repo_last_commit}")
        
        # Initialize pipeline
        if st.button("Initialize System"):
            st.session_state.pipeline = initialize_pipeline()
            if st.session_state.pipeline:
                st.success("✅ System initialized!")
                st.rerun()
        
        # Load/Update knowledge base
        if st.session_state.pipeline:
            if st.button("Load Knowledge Base") or check_for_updates():
                if load_knowledge_base():
                    st.rerun()
        
        # Manual update check
        if st.session_state.pipeline and st.button("Check for Updates"):
            if check_for_updates():
                st.info("🔄 Updates found! Loading...")
                if load_knowledge_base():
                    st.rerun()
            else:
                st.success("✅ Knowledge base is up to date")
        
        # Knowledge base status
        st.header("📊 Status")
        if st.session_state.pipeline:
            st.success("✅ Pipeline ready")
            
            # Check for existing data
            try:
                stats = st.session_state.pipeline.get_collection_stats()
                has_data = st.session_state.pipeline.has_existing_data()
                
                if has_data:
                    st.metric("Total chunks", stats['total_chunks'])
                    st.success("✅ Knowledge base loaded")
                    
                    # Option to use existing data
                    if not st.session_state.knowledge_base_loaded:
                        if st.button("Use Existing Knowledge Base"):
                            st.session_state.knowledge_base_loaded = True
                            st.success("✅ Using existing knowledge base!")
                            st.rerun()
                else:
                    st.warning("No knowledge base loaded")
            except Exception as e:
                st.warning(f"Error checking database: {e}")
        else:
            st.warning("❌ Pipeline not initialized")
        
        if st.session_state.knowledge_base_loaded:
            st.success("✅ Knowledge base active")
        else:
            st.warning("❌ No knowledge base active")
        
        # Clear chat history
        if st.button("Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💬 Ask Sean's AI")
        
        # Display chat history
        for i, (role, message, sources) in enumerate(st.session_state.chat_history):
            if role == "user":
                st.markdown(f'<div class="chat-message user-message"><strong>You:</strong> {message}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-message assistant-message"><strong>Sean GPT:</strong> {message}</div>', unsafe_allow_html=True)
                if sources:
                    with st.expander(f"View sources for response {i//2 + 1}"):
                        display_sources(sources)
        
        # Chat input
        if st.session_state.pipeline and st.session_state.knowledge_base_loaded:
            question = st.chat_input("Ask me anything about Sean's college notes...")
            
            if question:
                # Add user message to history
                st.session_state.chat_history.append(("user", question, None))
                
                # Query the knowledge base
                response = query_knowledge_base(question)
                
                if response:
                    # Add assistant response to history
                    st.session_state.chat_history.append(("assistant", response.answer, response.sources))
                
                # Rerun to update the chat display
                st.rerun()
        else:
            st.info("Please initialize the system and load the knowledge base to start chatting.")
    
    with col2:
        st.header("📈 Session Info")
        
        if st.session_state.chat_history:
            st.metric("Questions asked", len([m for m in st.session_state.chat_history if m[0] == "user"]))
            
            # Recent questions
            st.subheader("Recent Questions")
            recent_questions = [m[1] for m in st.session_state.chat_history if m[0] == "user"][-5:]
            for q in reversed(recent_questions):
                st.write(f"• {q}")
        else:
            st.info("No questions asked yet")
        
        # Sample questions
        st.subheader("💡 Try asking about:")
        sample_topics = [
            "Computer Science concepts",
            "Mathematics from your courses", 
            "Machine Learning techniques",
            "Data Structures & Algorithms",
            "Course-specific content",
            "Cross-course connections"
        ]
        
        for topic in sample_topics:
            st.write(f"• {topic}")

if __name__ == "__main__":
    main()
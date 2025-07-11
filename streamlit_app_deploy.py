#!/usr/bin/env python3
"""
Simple Sean GPT Streamlit app with hard-coded repository
"""

import streamlit as st
import sys
import os
from pathlib import Path
import time

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
    page_icon="🤖",
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
    .stProgress > div > div {
        background-color: #1f77b4;
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
    /* Loading overlay styles */
    .loading-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(255, 255, 255, 0.9);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    }
</style>
""", unsafe_allow_html=True)

def initialize_pipeline():
    """Initialize the RAG pipeline"""
    if not BACKEND_AVAILABLE:
        st.error("Backend is not available. Please check your installation.")
        return None
        
    try:
        # Get OpenAI API key from environment
        openai_key = st.session_state.user_api_key
        
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
            openai_api_key=openai_key
        )
        
        # st.success("✅ Pipeline initialized successfully!")
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
        
        # st.success(f"✅ Knowledge base loaded! {stats['chunks_created']} chunks processed")
        return True
        
    except Exception as e:
        st.error(f"❌ Failed to load knowledge base: {str(e)}")
        return False

def set_loading_state(is_loading=False, message="", progress=None):
    """Set the loading state and message"""
    st.session_state.loading = is_loading
    if message:
        st.session_state.loading_message = message
    if progress is not None:
        st.session_state.loading_progress = progress
    # We don't force rerun here to allow multiple updates

def main():
    # Initialize session state variables
    if "pipeline" not in st.session_state:
        st.session_state.pipeline = None
    if "knowledge_base_loaded" not in st.session_state:
        st.session_state.knowledge_base_loaded = False
    if "loading" not in st.session_state:
        st.session_state.loading = True
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "app_initialized" not in st.session_state:
        st.session_state.app_initialized = False
    if "clear_input" not in st.session_state:
        st.session_state.clear_input = False
    if "last_query" not in st.session_state:
        st.session_state.last_query = ""
    
    # Set up app stage if not already in session state
    if "app_stage" not in st.session_state:
        st.session_state.app_stage = "api_key_prompt"
    
    # Create a placeholder for the entire app content
    main_content = st.empty()
    
    # Show content based on app stage
    if st.session_state.app_stage == "api_key_prompt":
        # Create loading screen in the placeholder
        with main_content.container():
            # Center the loading content with columns
            _, center_col, _ = st.columns([1, 2, 1])
            
            with center_col:
                st.markdown('<h1 class="main-header">🤖 Sean GPT</h1>', unsafe_allow_html=True)
                st.markdown('<p style="text-align: center; font-size: 1.2rem;">Initializing Sean\'s personal knowledge assistant...</p>', unsafe_allow_html=True)
                
                # Loading progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Stage A: OpenAI API Key Input
                st.markdown("**🔑 OpenAI API Key Required**")
                st.warning("Please enter your OpenAI API Key to continue")
                
                # API Key input form
                api_key_col1, api_key_col2, api_key_col3 = st.columns([1, 2, 1])
                    
                with api_key_col2:
                    api_key = st.text_input(
                        "OpenAI API Key",
                        type="password",
                        placeholder="sk-...",
                        help="Your API key will be used for search and answer generation."
                        )
                        
                    if st.button("Set API Key & Continue", type="primary"):
                        if api_key and api_key.startswith('sk-'):
                            # Store the API key in environment variable
                            st.session_state.user_api_key = api_key
                            st.success("API key set successfully!")
                            # Transition to loading stage
                            st.session_state.app_stage = "loading"
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Please enter a valid OpenAI API key starting with 'sk-'")


    elif st.session_state.app_stage == "loading":
        # Stage B: Loading Screen
        with main_content.container():
            # Center the loading content with columns
            _, center_col, _ = st.columns([1, 2, 1])
            
            with center_col:
                st.markdown('<h1 class="main-header">🤖 Sean GPT</h1>', unsafe_allow_html=True)
                st.markdown('<p style="text-align: center; font-size: 1.2rem;">Initializing Sean\'s personal knowledge assistant...</p>', unsafe_allow_html=True)
                
                # Loading progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                status_text.markdown("**🔑 API Key validated, initializing system...**")
                
                time.sleep(0.5)
                progress_bar.progress(10)
                    
                # Initialize pipeline
                status_text.markdown("**⚙️ Initializing pipeline...**")
                progress_bar.progress(20)
                pipeline = initialize_pipeline()
                time.sleep(0.5)
                
                if pipeline:
                    st.session_state.pipeline = pipeline
                    status_text.markdown("**✅ Pipeline initialized!**")
                    progress_bar.progress(40)
                    
                    # Load Knowledge Base
                    time.sleep(0.25)
                    status_text.markdown("**📚 Loading knowledge base...**")
                    progress_bar.progress(60)
                    success = load_knowledge_base()
                    time.sleep(0.5)
                    
                    if success:
                        st.session_state.knowledge_base_loaded = True
                        status_text.markdown("**✅ Knowledge base loaded!**")
                        progress_bar.progress(80)
                        
                        # Add a small delay before transition for better UX
                        time.sleep(0.25)
                        
                        # Mark app as initialized and ready for main interface
                        st.session_state.app_initialized = True
                        st.session_state.loading = False
                        st.session_state.app_stage = "main_interface"

                        status_text.markdown("**✅ Load Complete!**")
                        progress_bar.progress(100)
                        time.sleep(0.5)
                        
                        # Refresh the page to show main content
                        st.rerun()
                    else:
                        status_text.markdown("**❌ Failed to load knowledge base**")
                        # Option to retry or go back to API key stage
                        if st.button("Return to API Key Input"):
                            st.session_state.app_stage = "api_key_prompt"
                            st.rerun()
                else:
                    status_text.markdown("**❌ Failed to initialize pipeline**")
                    # Option to retry or go back to API key stage
                    if st.button("Return to API Key Input"):
                        st.session_state.app_stage = "api_key_prompt"
                        st.rerun()
                    
    elif st.session_state.app_stage == "main_interface":
        # Stage C: Main app content (only shown after full initialization)
        with main_content.container():
            # Header
            st.markdown('<h1 class="main-header">🤖 Sean GPT</h1>', unsafe_allow_html=True)
            st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Sean\'s Personal Knowledge Assistant</p>', unsafe_allow_html=True)
            
            st.header("💬 Chat with My Knowledge Base")
                
            # Display chat history
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    st.markdown(f'<div class="chat-message user-message"><strong>You:</strong> {message["content"]}</div>', 
                                   unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-message assistant-message"><strong>Sean GPT:</strong> {message["content"]}</div>', 
                                   unsafe_allow_html=True)
                    # Display sources
                    if message["sources"]:
                        with st.expander("📚 Sources"):
                            for i, source in enumerate(message["sources"]):
                                st.markdown(f"**Source {i}: {source['title']}**")
                                st.markdown(f"File: `{source['file']}`")
                                st.markdown(f"Headers: {source['headers']}")
                                st.markdown(f"Tags: {source['tags']}")
                                st.markdown(f"Preview: {source['content_preview']}")
                                st.divider()

            with st.sidebar:
                st.header("🔧 Actions")
                
                if not st.session_state.user_api_key:
                    # API Key Input
                    st.subheader("🔑 OpenAI API Key")
                    
                    # Store API key in session state if not already there
                    if "user_api_key" not in st.session_state:
                        st.session_state.user_api_key = ""
                
                    api_key_input = st.text_input(
                        "Enter your OpenAI API key",
                        type="password",
                        placeholder="sk-...",
                        help="Your API key will be used for search and answer generation. The embeddings database is pre-generated.",
                        key="api_key_input"
                    )
                    
                    if st.button("Set API Key & Initialize", type="primary"):
                        if api_key_input:
                            # Store the key in session state
                            st.session_state.user_api_key = api_key_input
                            os.environ["OPENAI_API_KEY"] = api_key_input
                            
                            # Reinitialize the pipeline with the new API key
                            with st.spinner("🔁 Initializing pipeline with your API key..."):
                                if initialize_pipeline():
                                    st.success("✅ API key set and pipeline initialized!")
                                else:
                                    st.error("❌ Failed to initialize pipeline. Check your API key.")
                        else:
                            st.error("Please enter an API key")
                        
                # Option to restart the entire app flow
                if st.button("🔄 Restart App"):
                    st.session_state.app_stage = "api_key_prompt"
                    st.session_state.app_initialized = False
                    st.session_state.user_api_key = ""
                    st.rerun()
                
                top_k = st.selectbox("# of Documents to Generate Response From", [1, 2, 3, 5, 10, 20], index=2)
                
                if st.button("🗑️ Clear Chat"):
                    st.session_state.chat_history = []
                    st.rerun()
            
                # System info
                st.divider()
                st.subheader("ℹ️ Info")
                st.info(f"**Messages:** {len(st.session_state.chat_history) // 2}")
                st.info(f"**Repository:** obiKnowledge")
                
                if st.session_state.pipeline:
                    stats = st.session_state.pipeline.get_collection_stats()
                    st.info(f"**Chunks:** {stats['total_chunks']}")

            # Main Chat Input
            # Check if we need to reset the input (after submission)
            if st.session_state.get('clear_input', False):
                st.session_state.query_input = ""
                st.session_state.clear_input = False
                st.session_state.last_query = ""
                
            # Input with automatic Enter key detection
            query = st.text_input(label="Ask a question", placeholder="Ask a question about Sean's knowledge base:", key="query_input", label_visibility="hidden")
            submit_button = st.button("🔍 Ask", type="primary")

            print("----------------")
            print("DEBUG - Button pressed:", submit_button)
            print("DEBUG - Query:", query)
            print("DEBUG - query_submitted:", st.session_state.get('query_submitted', None))
            print("DEBUG - last_query:", st.session_state.get('last_query', None))
            
            if submit_button and not st.session_state.query_submitted:  # Make sure we have a query to process
                # Save current query to avoid reprocessing
                st.session_state.query_submitted = True
                st.session_state.last_query = query
                print("DEBUG - PROCESSING QUERY")
                
                if not st.session_state.pipeline:
                    st.error("Pipeline not initialized. Please initialize the pipeline first.")
                elif not st.session_state.knowledge_base_loaded:
                    st.error("Knowledge base not loaded. Please load the knowledge base first.")
                elif not st.session_state.user_api_key:
                    st.error("Please set your OpenAI API key first.")
                    st.info("Your API key is needed to generate embeddings for your query and create responses.")
                    with st.sidebar:
                        st.error("⚠️ OpenAI API key required")
                        st.markdown("👈 Enter your API key in the sidebar")
                else:
                    print("DEBUG - QUERYING PIPELINE")
                    # Add user message to history
                    st.session_state.chat_history.append({"role": "user", "content": query, "sources": None})
                    
                    # Query the pipeline
                    with st.spinner("🧠 Thinking..."):
                        try:
                            print("DEBUG - Thinking...")
                            response = st.session_state.pipeline.query(query, k=top_k)
                            # print("DEBUG - Thinking... response:", response)
                            print("DEBUG - Chat History")
                            print(st.session_state.chat_history)
                            st.session_state.chat_history.append({"role": "assistant", "content": response.answer, "sources": response.sources})
                            print("DEBUG - Thinking... chat_history:", st.session_state.chat_history)
                            
                            # Set flag to clear input on next rerun
                            st.session_state.clear_input = True
                        
                        except Exception as e:
                            print("Error: ", e)
                            error_msg = f"Error: {str(e)}"
                            st.error(error_msg)
                            st.session_state.chat_history.append({"role": "assistant", "content": error_msg})

                    st.session_state.query_submitted = False
                    # Rerun to update the display
                    st.rerun()
            else:
                # Reset submission flag when not submitting
                st.session_state.query_submitted = False

if __name__ == "__main__":
    main()
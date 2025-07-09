import streamlit as st
import requests
import sys
import os
from pathlib import Path
import json
from typing import List, Dict, Any

# Add backend path to sys.path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    from app.core.rag_pipeline import RAGPipeline
    from app.services.obsidian_loader import ObsidianLoader
    BACKEND_AVAILABLE = True
except ImportError as e:
    st.error(f"Backend import error: {e}")
    BACKEND_AVAILABLE = False
import tempfile
import zipfile

# Page config
st.set_page_config(
    page_title="Sean GPT",
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
    .source-box {
        background-color: #fff3e0;
        border: 1px solid #ff9800;
        border-radius: 0.25rem;
        padding: 0.5rem;
        margin: 0.5rem 0;
        font-size: 0.9rem;
    }
    .metric-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
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
    """Initialize the RAG pipeline with production-ready error handling"""
    if not BACKEND_AVAILABLE:
        st.error("Backend is not available. Please check your installation.")
        return None
        
    try:
        # Get OpenAI API key from environment or user input
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if not openai_key:
            st.error("❌ OpenAI API key not found")
            st.info("💡 Set OPENAI_API_KEY environment variable or create .env file")
            with st.expander("🔧 Setup Instructions"):
                st.code("""
# Option 1: Environment variable
export OPENAI_API_KEY=sk-your-key-here

# Option 2: Create .env file in backend directory
echo "OPENAI_API_KEY=sk-your-key-here" > backend/.env
                """)
            return None
        
        # Validate API key format
        if not openai_key.startswith('sk-'):
            st.error("❌ Invalid OpenAI API key format (should start with 'sk-')")
            return None
        
        # Test API key validity
        with st.spinner("🔑 Validating API key..."):
            try:
                from openai import OpenAI
                client = OpenAI(api_key=openai_key)
                # Quick test call
                client.models.list()
                st.success("✅ API key validated")
            except Exception as api_error:
                st.error(f"❌ API key validation failed: {str(api_error)}")
                return None
        
        # Initialize pipeline with error handling
        with st.spinner("🔧 Initializing RAG pipeline..."):
            pipeline = RAGPipeline(
                openai_api_key=openai_key,
                chroma_persist_directory=str(backend_path / "data" / "chroma_db"),
                chunk_size=1000,
                chunk_overlap=200
            )
        
        return pipeline
    except ImportError as e:
        st.error(f"❌ Missing dependencies: {str(e)}")
        st.info("💡 Run: pip install openai")
        return None
    except Exception as e:
        st.error(f"❌ Pipeline initialization failed: {str(e)}")
        st.info("💡 Check logs for details")
        return None

def load_from_github(repo_url: str):
    """Load knowledge base from GitHub repository"""
    if st.session_state.pipeline is None:
        st.error("Pipeline not initialized")
        return
    
    try:
        # Check if we should clear existing data first
        if st.session_state.pipeline.has_existing_data():
            st.warning("⚠️ Existing data found in database. This will add to existing data.")
            if st.button("Clear existing data first?"):
                st.session_state.pipeline.clear_collection()
                st.rerun()
                return
        
        with st.spinner("Cloning/updating repository from GitHub..."):
            # Use the obsidian loader's GitHub functionality
            from app.services.obsidian_loader import clone_or_update_repo
            
            # Clone to backend data directory
            local_repo_path = backend_path / "data" / "github_vault"
            
            # Clone or update repository
            st.info("📥 Downloading repository...")
            clone_or_update_repo(repo_url, str(local_repo_path))
            
        # Show progress for document processing
        progress_container = st.empty()
        with progress_container:
            with st.spinner("🔄 Processing documents and generating embeddings..."):
                st.info("This may take several minutes for large repositories...")
                
                # Ingest documents from the cloned repository
                stats = st.session_state.pipeline.ingest_documents(str(local_repo_path))
            
        st.session_state.knowledge_base_loaded = True
        st.success(f"✅ Successfully loaded from GitHub!")
        st.info(f"📊 Processed {stats['documents_processed']} documents into {stats['chunks_created']} chunks")
            
    except Exception as e:
        st.error(f"Error loading from GitHub: {str(e)}")
        st.error("Make sure the repository URL is correct and accessible")

def load_sample_data():
    """Load sample data for demo"""
    if st.session_state.pipeline is None:
        st.error("Pipeline not initialized")
        return
    
    try:
        with st.spinner("Loading sample knowledge base..."):
            # Create sample notes (same as in test_rag.py)
            sample_dir = backend_path / "data" / "obsidian-notes"
            sample_dir.mkdir(parents=True, exist_ok=True)
            
            # Sample note 1: Machine Learning
            ml_note = """---
title: Machine Learning Basics
tags: [cs, ai, ml]
created: 2023-01-15
---

# Machine Learning Basics

Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.

## Types of Machine Learning

### Supervised Learning
- Uses labeled training data
- Examples: classification, regression
- Algorithms: [[Linear Regression]], [[Decision Trees]]

### Unsupervised Learning
- Finds patterns in unlabeled data
- Examples: clustering, dimensionality reduction
- Algorithms: K-means, PCA

### Reinforcement Learning
- Agent learns through interaction with environment
- Reward/punishment system
- Examples: game playing, robotics

## Key Concepts

**Training Data**: Dataset used to train the model
**Features**: Input variables used to make predictions
**Labels**: Target outputs for supervised learning
**Model**: Mathematical representation of a real-world process

#ai #machinelearning #cs229
"""
            
            with open(sample_dir / "machine_learning_basics.md", "w") as f:
                f.write(ml_note)
            
            # Sample note 2: Data Structures
            ds_note = """---
title: Data Structures Overview
tags: [cs, algorithms, data-structures]
created: 2023-01-20
---

# Data Structures Overview

Data structures are ways of organizing and storing data efficiently.

## Linear Data Structures

### Arrays
- Fixed size collection of elements
- O(1) access time
- O(n) insertion/deletion

### Linked Lists
- Dynamic size
- O(n) access time
- O(1) insertion/deletion at head

### Stacks
- LIFO (Last In, First Out)
- Operations: push, pop, peek
- Used in: function calls, expression evaluation

### Queues
- FIFO (First In, First Out)
- Operations: enqueue, dequeue
- Used in: BFS, task scheduling

## Non-Linear Data Structures

### Trees
- Hierarchical structure
- Binary trees, BSTs, AVL trees
- Used in: file systems, databases

### Graphs
- Vertices and edges
- Directed vs undirected
- Algorithms: [[BFS]], [[DFS]], [[Dijkstra]]

#datastructures #algorithms #cs106b
"""
            
            with open(sample_dir / "data_structures.md", "w") as f:
                f.write(ds_note)
            
            # Sample note 3: Linear Algebra
            la_note = """---
title: Linear Algebra for ML
tags: [math, linear-algebra, ml]
created: 2023-01-25
---

# Linear Algebra for Machine Learning

Linear algebra is fundamental to understanding machine learning algorithms.

## Vectors

A vector is an ordered list of numbers representing magnitude and direction.

### Vector Operations
- **Addition**: v + w = [v₁ + w₁, v₂ + w₂, ...]
- **Scalar multiplication**: cv = [cv₁, cv₂, ...]
- **Dot product**: v·w = v₁w₁ + v₂w₂ + ...

## Matrices

A matrix is a rectangular array of numbers.

### Matrix Operations
- **Addition**: A + B (element-wise)
- **Multiplication**: AB (row × column)
- **Transpose**: A^T (rows become columns)
- **Inverse**: A^(-1) (if it exists)

## Applications in ML

### Linear Regression
- Uses matrix multiplication: y = Xβ + ε
- Normal equation: β = (X^T X)^(-1) X^T y

### Principal Component Analysis (PCA)
- Eigenvalue decomposition
- Dimensionality reduction
- Related to: [[Machine Learning Basics]]

### Neural Networks
- Weight matrices
- Forward propagation as matrix multiplication
- Backpropagation uses chain rule

#math #linearalgebra #ml #math51
"""
            
            with open(sample_dir / "linear_algebra.md", "w") as f:
                f.write(la_note)
            
            # Ingest the documents
            stats = st.session_state.pipeline.ingest_documents(str(sample_dir))
            
            st.session_state.knowledge_base_loaded = True
            st.success(f"✅ Knowledge base loaded successfully!")
            st.info(f"📊 Processed {stats['documents_processed']} documents into {stats['chunks_created']} chunks")
            
    except Exception as e:
        st.error(f"Error loading sample data: {str(e)}")

def query_knowledge_base(question: str):
    """Query the knowledge base and return response"""
    if st.session_state.pipeline is None:
        st.error("Pipeline not initialized")
        return None
    
    try:
        with st.spinner("Searching knowledge base..."):
            response = st.session_state.pipeline.query(question, k=5)
            return response
    except Exception as e:
        st.error(f"Error querying knowledge base: {str(e)}")
        return None

def display_sources(sources: List[Dict[str, Any]]):
    """Display source information"""
    if not sources:
        return
    
    st.subheader("📚 Sources")
    
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
    st.markdown('<h1 class="main-header">🤖 Sean GPT</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">RAG-powered AI assistant trained on Sean\'s college notes</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Setup")
        
        # Backend status
        if BACKEND_AVAILABLE:
            st.success("✅ Backend available")
        else:
            st.error("❌ Backend not available")
            st.stop()
        
        # Initialize pipeline
        if st.button("Initialize Pipeline"):
            st.session_state.pipeline = initialize_pipeline()
            if st.session_state.pipeline:
                st.success("✅ Pipeline initialized!")
                st.rerun()
        
        # Load sample data
        if st.session_state.pipeline and st.button("Load Sample Knowledge Base"):
            load_sample_data()
            st.rerun()
        
        # GitHub repository integration
        st.subheader("📂 GitHub Integration")
        if st.session_state.pipeline:
            github_url = st.text_input(
                "GitHub Repository URL:",
                placeholder="https://github.com/username/repo",
                help="Enter the URL of your Obsidian vault repository"
            )
            
            if st.button("Load from GitHub") and github_url:
                load_from_github(github_url)
                st.rerun()
        
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
                    st.success("✅ Existing knowledge base found")
                    
                    # Option to use existing data
                    if st.button("Use Existing Knowledge Base"):
                        st.session_state.knowledge_base_loaded = True
                        st.success("✅ Using existing knowledge base!")
                        st.rerun()
                    
                    # Option to clear existing data
                    if st.button("Clear Existing Data", type="secondary"):
                        st.session_state.pipeline.clear_collection()
                        st.session_state.knowledge_base_loaded = False
                        st.success("✅ Database cleared!")
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
        st.header("💬 Chat Interface")
        
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
            question = st.chat_input("Ask me anything about Sean's notes...")
            
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
            st.info("Please initialize the pipeline and load the knowledge base to start chatting.")
    
    with col2:
        st.header("📈 Analytics")
        
        if st.session_state.chat_history:
            st.metric("Total questions", len([m for m in st.session_state.chat_history if m[0] == "user"]))
            
            # Recent questions
            st.subheader("Recent Questions")
            recent_questions = [m[1] for m in st.session_state.chat_history if m[0] == "user"][-5:]
            for q in reversed(recent_questions):
                st.write(f"• {q}")
        else:
            st.info("No chat history yet")
        
        # Sample questions
        st.subheader("💡 Try these questions:")
        sample_questions = [
            "What is a bijective function?",
            "Explain graph coloring in planar graphs",
            "What are data structures covered in CIS1210?",
            "How is linear algebra used in machine learning?",
            "Tell me about computer vision techniques",
            "What did you learn in CIS5190 about ML?"
        ]
        
        for q in sample_questions:
            if st.button(q, key=f"sample_{q}"):
                if st.session_state.pipeline and st.session_state.knowledge_base_loaded:
                    # Add to chat history and process
                    st.session_state.chat_history.append(("user", q, None))
                    response = query_knowledge_base(q)
                    if response:
                        st.session_state.chat_history.append(("assistant", response.answer, response.sources))
                    st.rerun()

if __name__ == "__main__":
    main()
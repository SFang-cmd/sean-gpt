import streamlit as st
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Now import backend modules
try:
    from app.core.rag_pipeline import RAGPipeline
    from app.services.obsidian_loader import ObsidianLoader
    BACKEND_AVAILABLE = True
except ImportError as e:
    st.error(f"Backend import error: {e}")
    BACKEND_AVAILABLE = False

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
            st.error("Please set your OPENAI_API_KEY environment variable")
            st.info("You can set it in the .env file")
            return None
        
        pipeline = RAGPipeline(
            openai_api_key=openai_key,
            chroma_persist_directory=str(backend_path / "data" / "chroma_db"),
            chunk_size=1000,
            chunk_overlap=200
        )
        
        return pipeline
    except Exception as e:
        st.error(f"Error initializing pipeline: {str(e)}")
        return None

def create_sample_notes():
    """Create sample notes for testing"""
    sample_dir = backend_path / "data" / "obsidian-notes"
    sample_dir.mkdir(parents=True, exist_ok=True)
    
    # Only create if not exists
    if not (sample_dir / "machine_learning_basics.md").exists():
        ml_note = """# Machine Learning Basics

Machine learning is a subset of artificial intelligence that enables computers to learn from data.

## Types of Machine Learning

### Supervised Learning
- Uses labeled training data
- Examples: classification, regression

### Unsupervised Learning  
- Finds patterns in unlabeled data
- Examples: clustering, dimensionality reduction

### Reinforcement Learning
- Agent learns through trial and error
- Examples: game playing, robotics

## Key Concepts
- **Training Data**: Data used to train the model
- **Features**: Input variables
- **Labels**: Target outputs
- **Model**: Mathematical representation

#ai #machinelearning #cs229
"""
        
        with open(sample_dir / "machine_learning_basics.md", "w") as f:
            f.write(ml_note)
    
    return str(sample_dir)

def load_knowledge_base():
    """Load the knowledge base"""
    if not st.session_state.pipeline:
        st.error("Pipeline not initialized")
        return False
        
    try:
        with st.spinner("Loading knowledge base..."):
            # Create sample notes
            notes_dir = create_sample_notes()
            
            # Ingest documents
            stats = st.session_state.pipeline.ingest_documents(notes_dir)
            
            st.session_state.knowledge_base_loaded = True
            st.success(f"✅ Loaded {stats['documents_processed']} documents, {stats['chunks_created']} chunks")
            return True
            
    except Exception as e:
        st.error(f"Error loading knowledge base: {str(e)}")
        return False

def query_knowledge_base(question: str):
    """Query the knowledge base"""
    if not st.session_state.pipeline:
        st.error("Pipeline not initialized")
        return None
        
    try:
        with st.spinner("Searching..."):
            response = st.session_state.pipeline.query(question, k=3)
            return response
    except Exception as e:
        st.error(f"Error querying: {str(e)}")
        return None

def main():
    # Header
    st.markdown('<h1 class="main-header">🤖 Sean GPT</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">RAG-powered AI assistant for Sean\'s knowledge base</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Setup")
        
        # Backend status
        if BACKEND_AVAILABLE:
            st.success("✅ Backend available")
        else:
            st.error("❌ Backend not available")
            st.stop()
        
        # Pipeline initialization
        if st.button("Initialize Pipeline"):
            st.session_state.pipeline = initialize_pipeline()
            if st.session_state.pipeline:
                st.success("✅ Pipeline initialized")
                st.rerun()
        
        # Knowledge base loading
        if st.session_state.pipeline and st.button("Load Knowledge Base"):
            if load_knowledge_base():
                st.rerun()
        
        # Status indicators
        st.header("📊 Status")
        if st.session_state.pipeline:
            st.success("✅ Pipeline ready")
        else:
            st.warning("❌ Pipeline not initialized")
            
        if st.session_state.knowledge_base_loaded:
            st.success("✅ Knowledge base loaded")
            try:
                stats = st.session_state.pipeline.get_collection_stats()
                st.metric("Total chunks", stats['total_chunks'])
            except:
                pass
        else:
            st.warning("❌ Knowledge base not loaded")
    
    # Main content
    st.header("💬 Chat Interface")
    
    # Display chat history
    for role, message, sources in st.session_state.chat_history:
        if role == "user":
            st.markdown(f'<div class="chat-message user-message"><strong>You:</strong> {message}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-message assistant-message"><strong>Sean GPT:</strong> {message}</div>', unsafe_allow_html=True)
            if sources:
                with st.expander("View sources"):
                    for source in sources:
                        st.write(f"**{source['title']}** (relevance: {1-source['distance']:.2f})")
                        st.write(source['content_preview'])
    
    # Chat input
    if st.session_state.pipeline and st.session_state.knowledge_base_loaded:
        # Sample questions
        st.subheader("💡 Try these questions:")
        sample_questions = [
            "What is machine learning?",
            "Explain supervised learning",
            "What are the key concepts in ML?"
        ]
        
        cols = st.columns(len(sample_questions))
        for i, question in enumerate(sample_questions):
            if cols[i].button(question, key=f"sample_{i}"):
                # Process question
                st.session_state.chat_history.append(("user", question, None))
                response = query_knowledge_base(question)
                if response:
                    st.session_state.chat_history.append(("assistant", response.answer, response.sources))
                st.rerun()
        
        # Text input
        question = st.text_input("Ask a question:", key="question_input")
        if st.button("Send") and question:
            # Process question
            st.session_state.chat_history.append(("user", question, None))
            response = query_knowledge_base(question)
            if response:
                st.session_state.chat_history.append(("assistant", response.answer, response.sources))
            st.rerun()
    else:
        st.info("Please initialize the pipeline and load the knowledge base first.")

if __name__ == "__main__":
    main()
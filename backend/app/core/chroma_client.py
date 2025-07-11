import os
import chromadb
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_chroma_client():
    """
    Returns a ChromaDB client based on environment configuration.
    Uses Chroma Cloud if credentials are provided, otherwise falls back to local PersistentClient.
    """
    # Check if Chroma Cloud credentials are available
    chroma_api_key = os.getenv("CHROMA_API_KEY")
    chroma_tenant = os.getenv("CHROMA_TENANT")
    chroma_database = os.getenv("CHROMA_DATABASE", "SeanGPT")
    
    if chroma_api_key and chroma_tenant:
        # Use Chroma Cloud
        print("Using Chroma Cloud for vector database")
        return chromadb.CloudClient(
            api_key=chroma_api_key,
            tenant=chroma_tenant,
            database=chroma_database
        )
    else:
        # Fallback to local persistent storage
        persist_directory = os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma_db")
        print(f"Using local ChromaDB at {persist_directory}")
        return chromadb.PersistentClient(path=persist_directory)

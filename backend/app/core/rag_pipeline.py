import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import chromadb
from langchain_openai import OpenAIEmbeddings, OpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document

from ..services.obsidian_loader import ObsidianLoader, ObsidianDocument, clone_or_update_repo, load_default_knowledge_base
from ..services.text_splitter import MarkdownTextSplitter, DocumentChunk

@dataclass
class RAGResponse:
    """Response from the RAG system"""
    answer: str
    sources: List[Dict[str, Any]]
    query: str
    confidence: float = 0.0

class RAGPipeline:
    """Main RAG pipeline for Sean GPT"""
    
    def __init__(self, 
                 openai_api_key: str,
                 chroma_persist_directory: str = "./data/chroma_db",
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200):
        
        self.openai_api_key = openai_api_key
        self.chroma_persist_directory = chroma_persist_directory
        
        # Initialize components
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.llm = OpenAI(openai_api_key=openai_api_key, temperature=0.7)
        self.text_splitter = MarkdownTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Initialize ChromaDB with new client configuration
        self.client = chromadb.PersistentClient(
            path=chroma_persist_directory
        )
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="sean_notes",
            metadata={"description": "Sean's college notes"}
        )
        
        # Prompt template for RAG
        self.prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template="""You are Sean GPT, an AI assistant trained on Sean's college notes and knowledge base.

Context from Sean's notes:
{context}

Question: {question}

Instructions:
- Answer the question based on the provided context from Sean's notes
- If the context doesn't contain relevant information, say so clearly
- Cite specific notes or sources when possible
- Be conversational and helpful, as if you're Sean explaining concepts to a friend
- If you reference a specific concept, mention which note or class it came from

Answer:"""
        )
    
    def ingest_documents(self, repo_path: str) -> Dict[str, int]:
        """Ingest Obsidian documents into the vector database"""
        print(f"Loading documents from {repo_path}...")
        
        # Load documents
        loader = ObsidianLoader(repo_path)
        documents = loader.load_documents()
        
        # Split into chunks
        print(f"Splitting {len(documents)} documents into chunks...")
        chunks = self.text_splitter.split_documents(documents)
        print(f"✅ Split complete! Created {len(chunks)} chunks total")
        
        # Convert to format for ChromaDB
        print(f"Processing {len(chunks)} chunks for embedding...")
        texts = []
        metadatas = []
        ids = []
        
        for i, chunk in enumerate(chunks):
            if i % 100 == 0:  # Progress every 100 chunks
                print(f"  Prepared {i}/{len(chunks)} chunks for embedding...")
            texts.append(chunk.content)
            metadatas.append({
                "source_file": chunk.source_file,
                "source_title": chunk.source_title,
                "chunk_index": chunk.chunk_index,
                "headers": " > ".join(chunk.headers) if chunk.headers else "",
                "tags": ", ".join(chunk.tags),
                "links": ", ".join(chunk.links),
                "created_date": chunk.metadata.get("created_date", ""),
                "modified_date": chunk.metadata.get("modified_date", "")
            })
            # Create globally unique ID using file path and global chunk index
            import hashlib
            unique_id = f"chunk_{i}_{hashlib.md5(chunk.source_file.encode()).hexdigest()[:8]}"
            ids.append(unique_id)
        
        # Clear existing collection if it has data first
        try:
            existing_count = self.collection.count()
            if existing_count > 0:
                print(f"⚠️ Clearing {existing_count} existing chunks from database...")
                # Delete all documents by getting all IDs first
                all_data = self.collection.get()
                if all_data['ids']:
                    self.collection.delete(ids=all_data['ids'])
                    print("✅ Database cleared")
        except Exception as e:
            print(f"Warning: Could not clear collection: {e}")
            # Continue anyway
        
        # Check for duplicate IDs before processing
        unique_ids = set(ids)
        if len(unique_ids) != len(ids):
            print(f"⚠️ Found {len(ids) - len(unique_ids)} duplicate IDs, regenerating...")
            # Regenerate all IDs to ensure uniqueness
            ids = [f"chunk_{i}" for i in range(len(texts))]
            print(f"✅ Generated {len(ids)} unique IDs")
        
        # Process embeddings and storage in smaller batches since storage is the bottleneck
        batch_size = 25  # Even smaller batches since ChromaDB storage is slow
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        print(f"🔄 Processing {len(texts)} chunks in {total_batches} batches of {batch_size}...")
        print("⏱️ Estimated time: 3-5 minutes for large repositories")
        
        for i in range(0, len(texts), batch_size):
            batch_end = min(i + batch_size, len(texts))
            batch_num = i // batch_size + 1
            
            print(f"📦 Batch {batch_num}/{total_batches}: Processing chunks {i+1}-{batch_end}")
            
            # Get batch data
            batch_texts = texts[i:batch_end]
            batch_metadatas = metadatas[i:batch_end]
            batch_ids = ids[i:batch_end]
            
            # Generate embeddings for this batch
            print(f"  🔄 Generating embeddings for batch {batch_num}...")
            batch_embeddings = self.embeddings.embed_documents(batch_texts)
            
            # Add to ChromaDB with detailed timing
            import time
            print(f"  💾 Storing batch {batch_num} in database...")
            start_time = time.time()
            
            try:
                self.collection.add(
                    documents=batch_texts,
                    embeddings=batch_embeddings,
                    metadatas=batch_metadatas,
                    ids=batch_ids
                )
                storage_time = time.time() - start_time
                print(f"  ✅ Batch {batch_num} stored in {storage_time:.1f}s!")
                
                # Show running total
                current_total = self.collection.count()
                print(f"  📊 Total chunks in database: {current_total}")
                
            except Exception as e:
                print(f"  ❌ Error storing batch {batch_num}: {e}")
                print(f"  📝 Batch details: {len(batch_texts)} texts, {len(batch_embeddings)} embeddings")
                raise
        
        print("🎉 All embeddings generated and stored successfully!")
        
        return {
            "documents_processed": len(documents),
            "chunks_created": len(chunks),
            "embeddings_stored": len(embeddings)
        }
    
    def query(self, question: str, k: int = 5) -> RAGResponse:
        """Query the knowledge base"""
        
        # Get relevant documents
        relevant_docs = self._retrieve_documents(question, k)
        
        if not relevant_docs:
            return RAGResponse(
                answer="I don't have any relevant information in my knowledge base to answer that question.",
                sources=[],
                query=question,
                confidence=0.0
            )
        
        # Prepare context
        context = self._prepare_context(relevant_docs)
        
        # Generate response
        prompt = self.prompt_template.format(context=context, question=question)
        answer = self.llm(prompt)
        
        # Prepare sources
        sources = []
        for doc in relevant_docs:
            sources.append({
                "file": doc["metadata"]["source_file"],
                "title": doc["metadata"]["source_title"],
                "headers": doc["metadata"]["headers"],
                "content_preview": doc["document"][:200] + "..." if len(doc["document"]) > 200 else doc["document"],
                "tags": doc["metadata"]["tags"],
                "distance": doc.get("distance", 0.0)
            })
        
        return RAGResponse(
            answer=answer.strip(),
            sources=sources,
            query=question,
            confidence=1.0 - min([s.get("distance", 0.0) for s in relevant_docs])
        )
    
    def _retrieve_documents(self, query: str, k: int) -> List[Dict[str, Any]]:
        """Retrieve relevant documents from ChromaDB"""
        
        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query)
        
        # Search ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k
        )
        
        # Format results
        relevant_docs = []
        for i in range(len(results["documents"][0])):
            relevant_docs.append({
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if "distances" in results else 0.0
            })
        
        return relevant_docs
    
    def _prepare_context(self, relevant_docs: List[Dict[str, Any]]) -> str:
        """Prepare context string from relevant documents"""
        context_parts = []
        
        for doc in relevant_docs:
            metadata = doc["metadata"]
            content = doc["document"]
            
            # Format each document
            context_part = f"""
Source: {metadata['source_title']} ({metadata['source_file']})
Headers: {metadata['headers']}
Tags: {metadata['tags']}
Content: {content}
"""
            context_parts.append(context_part)
        
        return "\n" + "="*50 + "\n".join(context_parts)
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        count = self.collection.count()
        
        return {
            "total_chunks": count,
            "collection_name": self.collection.name,
            "persist_directory": self.chroma_persist_directory
        }
    
    def has_existing_data(self) -> bool:
        """Check if ChromaDB already contains data"""
        try:
            count = self.collection.count()
            return count > 0
        except:
            return False
    
    def clear_collection(self):
        """Clear all data from the collection"""
        try:
            # Get all ids and delete them
            results = self.collection.get()
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                print(f"✅ Cleared {len(results['ids'])} existing chunks from database")
        except Exception as e:
            print(f"Error clearing collection: {e}")
    
    def load_and_ingest_default_repo(self) -> Dict[str, int]:
        """Convenience method to load and ingest the hard-coded repository"""
        print("🔄 Loading default knowledge base repository...")
        
        # Clone or update the default repository
        repo_path = clone_or_update_repo()
        if not repo_path:
            raise Exception("Failed to clone/update default repository")
        
        # Ingest the documents
        print(f"📚 Ingesting documents from {repo_path}")
        return self.ingest_documents(repo_path)
    
    def setup_knowledge_base(self, force_reload: bool = False) -> Dict[str, int]:
        """Set up the knowledge base with the default repository"""
        if self.has_existing_data() and not force_reload:
            stats = self.get_collection_stats()
            print(f"✅ Knowledge base already loaded with {stats['total_chunks']} chunks")
            return {"documents_processed": 0, "chunks_created": 0, "embeddings_stored": stats['total_chunks']}
        
        if force_reload:
            print("🗑️ Force reload requested - clearing existing data...")
            self.clear_collection()
        
        return self.load_and_ingest_default_repo()

# Example usage
if __name__ == "__main__":
    # Initialize pipeline
    pipeline = RAGPipeline(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        chroma_persist_directory="./data/chroma_db"
    )
    
    # Ingest documents (run once)
    # stats = pipeline.ingest_documents("./data/obsidian-notes")
    # print(f"Ingested: {stats}")
    
    # Query the system
    response = pipeline.query("What is machine learning?")
    print(f"Question: {response.query}")
    print(f"Answer: {response.answer}")
    print(f"Sources: {len(response.sources)} documents")
    for source in response.sources:
        print(f"  - {source['title']} ({source['file']})")
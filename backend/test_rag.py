#!/usr/bin/env python3
"""
Test script for the RAG pipeline
Run this to validate the complete system works
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent))

from app.core.rag_pipeline import RAGPipeline
from app.services.obsidian_loader import ObsidianLoader

def create_sample_notes():
    """Create sample notes for testing"""
    sample_dir = Path("./data/obsidian-notes")
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
    
    print(f"Created sample notes in {sample_dir}")
    return str(sample_dir)

def test_rag_pipeline():
    """Test the complete RAG pipeline"""
    
    # Load environment variables
    load_dotenv()
    
    # Check for OpenAI API key
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("ERROR: Please set OPENAI_API_KEY in your .env file")
        print("Create a .env file with: OPENAI_API_KEY=your_key_here")
        return
    
    print("🚀 Starting RAG Pipeline Test")
    print("=" * 50)
    
    # Create sample notes
    notes_dir = create_sample_notes()
    
    # Initialize pipeline
    print("📊 Initializing RAG Pipeline...")
    pipeline = RAGPipeline(
        openai_api_key=openai_key,
        chroma_persist_directory="./data/chroma_db",
        chunk_size=800,
        chunk_overlap=100
    )
    
    # Test document loading
    print("📚 Testing document loading...")
    loader = ObsidianLoader(notes_dir)
    documents = loader.load_documents()
    print(f"✅ Loaded {len(documents)} documents")
    
    for doc in documents:
        print(f"  - {doc.title} ({len(doc.content)} chars, {len(doc.tags)} tags)")
    
    # Test ingestion
    print("\n🔄 Testing document ingestion...")
    stats = pipeline.ingest_documents(notes_dir)
    print(f"✅ Ingestion complete:")
    print(f"  - Documents processed: {stats['documents_processed']}")
    print(f"  - Chunks created: {stats['chunks_created']}")
    print(f"  - Embeddings stored: {stats['embeddings_stored']}")
    
    # Test queries
    print("\n🔍 Testing queries...")
    
    test_queries = [
        "What is machine learning?",
        "Explain supervised learning",
        "What are the types of data structures?",
        "How is linear algebra used in ML?",
        "What is PCA?",
        "Tell me about stacks and queues"
    ]
    
    for query in test_queries:
        print(f"\n❓ Query: {query}")
        response = pipeline.query(query, k=3)
        print(f"💬 Answer: {response.answer[:200]}...")
        print(f"📝 Sources: {len(response.sources)} documents")
        for source in response.sources[:2]:  # Show top 2 sources
            print(f"   - {source['title']} (distance: {source['distance']:.3f})")
    
    # Test collection stats
    print("\n📊 Collection Statistics:")
    stats = pipeline.get_collection_stats()
    print(f"✅ Total chunks: {stats['total_chunks']}")
    print(f"✅ Collection: {stats['collection_name']}")
    
    print("\n🎉 RAG Pipeline test completed successfully!")
    print("=" * 50)

if __name__ == "__main__":
    test_rag_pipeline()
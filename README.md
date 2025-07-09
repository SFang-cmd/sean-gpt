# Sean GPT

A RAG (Retrieval-Augmented Generation) system that creates an intelligent interface to query and synthesize information from a personal Obsidian knowledge base of college notes.

## Architecture

- **Data Ingestion**: GitHub repository crawler for Obsidian vault
- **Vector Database**: ChromaDB/Pinecone for embeddings storage
- **LLM Framework**: LangChain for query processing and response generation
- **Backend**: FastAPI for REST API endpoints
- **Frontend**: Streamlit for web interface
- **Infrastructure**: AWS deployment with Docker containerization

## Tech Stack

- **Backend**: Python, FastAPI, LangChain
- **Vector DB**: ChromaDB/Pinecone
- **LLM**: OpenAI GPT-4 / Anthropic Claude
- **Frontend**: Streamlit, Python
- **Infrastructure**: AWS (ECS, RDS, S3), Docker
- **CI/CD**: GitHub Actions

## Getting Started

```bash
# Clone the repository
git clone https://github.com/SFang-cmd/sean-gpt.git
cd sean-gpt

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the development server
docker-compose up
```

## Project Structure

```
sean-gpt/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── services/
│   │   └── models/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── streamlit_app.py
│   ├── pages/
│   ├── components/
│   ├── requirements.txt
│   └── Dockerfile
├── infrastructure/
│   ├── terraform/
│   └── docker-compose.yml
└── data/
    └── obsidian-notes/
```
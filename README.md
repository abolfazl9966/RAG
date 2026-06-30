# RAG-Based Question Answering System

A lightweight Retrieval-Augmented Generation (RAG) application built using Django, FAISS, LangChain, and OpenAI-compatible APIs. The system allows you to ingest documents, generate embeddings, store vector representations in FAISS, retrieve the most relevant chunks, and produce grounded, context-based answers using an LLM.

## Features
- Document ingestion with automatic text chunking  
- Embedding generation using `text-embedding-3-large`  
- Semantic search powered by FAISS  
- Hybrid retrieval (semantic + lexical reranking)  
- Context expansion using neighboring chunks  
- LLM answer generation strictly based on retrieved context  
- REST APIs for ingestion and Q&A  
- Docker support for easy deployment  

## API Endpoints
POST /ask/ → Ask a question

POST /documents/add/ → Add a new document

POST /faiss/rebuild/ → Rebuild FAISS index




## Installation
```bash
git clone https://github.com/abolfazl9966/RAG.git
cd RAG
pip install -r requirements.txt

```
Create a .env file:
GAPGPT_API_KEY=your_api_key

Run migrations and start the server:
```bash
python manage.py migrate
python manage.py runserver
```

Purpose
This project is designed as a clean, modular example of how to build a fully functional RAG system using Python. It showcases practical skills in:

Semantic search
Vector databases
LLM integration
Backend API development
Author
Abolfazl

GitHub: https://github.com/abolfazl9966

`
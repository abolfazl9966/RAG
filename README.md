# Django RAG System (Docs Q&A)

A document-based Question Answering system built with Django and LangChain. It allows administrators to manage documentation and users to ask natural language questions. The system retrieves relevant context using a weighted keyword search algorithm and synthesizes answers using an LLM.

## Features

- **Document Management:** Django Admin interface for CRUD operations on documents.
- **Smart Retrieval:** Custom weighted search algorithm (prioritizing Title matches over Content) to fetch relevant context without the complexity of a vector database.
- **LLM Integration:** Connects to HuggingFace (or OpenRouter) models to generate human-like answers based strictly on the retrieved context.
- **Dockerized:** Fully containerized setup for easy deployment.

## Tech Stack

- **Backend:** Django 5, Python 3.10
- **AI/ML:** LangChain
- **Containerization:** Docker, Docker Compose
- **Database:** SQLite (default for dev/testing)

## Setup & Installation

### Prerequisites
- Docker & Docker Compose installed.
- An API Token from  **OpenRouter**.

### Step-by-Step Guide

1.  **Clone the repository:**
```bash
git clone https://github.com/abolfazl9966/Docs-Q-A.git
cd Docs-Q-A


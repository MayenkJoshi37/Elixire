<<<<<<< HEAD
Elixire Assistant — README.md

Drop this README.md into the root of your Elixire_Deploy repo and commit. It is written to match the app.py, web_server.py, and templates/index.html files you shared. Read and edit the sections labelled REPLACE_ME (email, keys, etc.) before pushing.

Elixire Assistant

A small Flask-based chat assistant for Elixire (a pharmacy management helper).
It uses:

Gemini (Google) for embeddings,

a GROQ LLM (via langchain_groq) for preprocessing / generation / translation,

optional ChromaDB for retrieval-augmented responses,

a minimal Tailwind-based web UI (templates/index.html).

Repository layout
Elixire_Deploy/
├─ app.py                 # core business logic (embeddings, Chroma lazy loader, LLM helpers)
├─ web_server.py          # Flask server (routes: /, /health, /chat)
├─ templates/
│  └─ index.html          # chat UI (Tailwind)
├─ requirements.txt       # (recommended to add)
├─ .env.example           # (recommended to add)
└─ README.md


NOTE: Your copy included tempelate/index.html vs templates/index.html. Flask expects templates/. If your file is currently in tempelate/, rename it:

git mv tempelate templates || mkdir -p templates && mv tempelate/index.html templates/
git add -A && git commit -m "Fix template folder name"

Quickstart — local development

Clone & enter repo

git clone git@github.com:MayenkJoshi37/Elixire_Deploy.git
cd Elixire_Deploy


Create a Python virtual environment

python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1


Install dependencies

Create requirements.txt (example provided below) and install:

pip install -r requirements.txt


Create .env

Copy the example and update values:

cp .env.example .env
# then edit .env with your keys/URLs


Run the server

python web_server.py


Open the UI at: http://localhost:8000/ (default port from .env or 8000)

.env.example (copy to .env and fill values)

Create a file .env in repo root — do not commit secrets.

# Gemini embeddings
GEMINI_API_KEY=REPLACE_ME_GEMINI_KEY
EMBEDDING_MODEL=gemini-embedding-001

# GROQ / LLM
GROQ_API_KEY=REPLACE_ME_GROQ_KEY
GROQ_MODEL_NAME=openai/gpt-oss-120b

# Chroma (optional retrieval DB)
CHROMA_PATH=./chroma_db
# Option A: direct zip URL (public or authenticated)
CHROMA_DB_DOWNLOAD_URL=
# Option B: Google Drive file id of zip (example: 1AbCDef...)
CHROMA_DB_DRIVE_FILE_ID=
CHROMA_COLLECTION_NAME=elixire_docs_bge_large

# Server / misc
PORT=8000
FLASK_DEBUG=false
LOG_LEVEL=INFO
DEFAULT_N_RESULTS=1
MAX_N_RESULTS=5

Minimal requirements.txt suggestion

Add this file to the repo (tweak versions as needed). After you verify in your environment, run pip freeze > requirements.txt for exact pins.

Flask>=2.0
python-dotenv>=0.20.0
requests>=2.28.0
chromadb>=0.3.0            # only if you use Chroma retrieval
google-generativeai>=0.1.0 # for `from google import genai`
langchain-groq             # or the exact package/distribution you use
langchain-core             # as used by your GROQ client


NOTE: package names for GROQ/langchain_groq may differ depending on how you installed them. If you already have a working virtualenv, generate a pinned requirements.txt with pip freeze > requirements.txt.

How it works — high level

Client (browser UI) posts user's message to POST /chat.

web_server.py:

Calls preprocess_user_query() (GROQ LLM) to normalize / translate to English.

Calls get_relevant_chunks() to query ChromaDB using Gemini embeddings (if Chroma is available).

Calls generate_response() which sends a system prompt + user message to GROQ LLM.

Calls postprocess_answer() to translate response into original language (if necessary).

Returns JSON to the UI which formats the output.

Frontend (templates/index.html) renders the chat and applies simple formatting to numbered steps.

Chat API

Endpoint: POST /chat
Body (JSON):

{
  "message": "How do I add a new medicine to inventory?",
  "n_results": 1
}


Curl example

curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"How do I add a new medicine to inventory?","n_results":1}'


Response

{
  "success": true,
  "answer": "<formatted text>",
  "used_chunks": ["..."],    # context returned from Chroma (if any)
  "original_language": "en"
}

ChromaDB notes (important if using retrieval)

app.py checks CHROMA_PATH — if a populated directory exists, it opens it with chromadb.PersistentClient.

If CHROMA_PATH is missing/empty and you provided CHROMA_DB_DOWNLOAD_URL or CHROMA_DB_DRIVE_FILE_ID, the app will attempt to download a zip and extract into CHROMA_PATH.

If neither is supplied, retrieval calls will simply return empty context (the assistant will still respond but without document context).

If you want to provide a zipped Chroma DB in Google Drive, set CHROMA_DB_DRIVE_FILE_ID. If you have a direct download URL, set CHROMA_DB_DOWNLOAD_URL.

Troubleshooting

RuntimeError: Please set GEMINI_API_KEY — add GEMINI_API_KEY to .env.

Template not found / 500 on / — ensure folder is templates/ (Flask default). See note above.

Chroma download/extract failed — check CHROMA_DB_DOWNLOAD_URL or Drive file id and network access. The server logs print download errors.

Embedding / LLM errors — ensure API keys (Gemini / GROQ) and model names are correct and that your environment has network access.

Dependency errors — install correct packages and pin versions in requirements.txt.

Optional: Docker (simple example)

Create a Dockerfile (example):

FROM python:3.10-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
ENV PORT=8000
EXPOSE 8000
CMD ["python", "web_server.py"]


A minimal docker-compose.yml:

version: "3.8"
services:
  elixire:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - GROQ_API_KEY=${GROQ_API_KEY}
      - PORT=8000
    volumes:
      - .:/app


Keep secrets out of committed compose files — use .env only locally or use secret management in production.

Security & best practices

Do not commit .env or any file containing secrets. Add .env to .gitignore.

Use environment-specific configs for production and protect API keys (do not store them in source).

If you expose the app publicly, protect the /chat endpoint with authentication or rate-limiting.

Tests & development tips

Add unit tests for preprocess_user_query, get_relevant_chunks, and postprocess_answer.

Add logging where helpful; current code uses logging in web_server.py and print() in app.py.

Freeze working dependencies: pip freeze > requirements.txt

License & contact
License: MIT (replace with your desired license)
Maintainer: Mayenk Joshi — REPLACE_ME_EMAIL@example.com
Repo: https://github.com/MayenkJoshi37/Elixire_Deploy
=======

# Elixire — Multilingual Conversational Assistant

A multilingual, retrieval-augmented AI assistant built for the Elixire Pharmacy Management Software.
The assistant helps pharmacists understand and use the software through short, simple, step-wise answers in multiple languages.

This project was developed as part of an industry–academia collaboration.


## Live Demo

https://elixire-deploy.onrender.com




## Repository Structure

Elixire_Deploy/
- app.py — Main backend logic (embeddings, retrieval, LLM calls)  
- vector_creation.py — Creates embeddings and builds the ChromaDB  
- web_server.py — (If included) Backend server for API  
- chroma_db/ — Persistent Chroma vector DB  
- requirements.txt — Python dependencies  
- frontend/ — React-based UI (if included)  
- README.md — Project documentation  

## Project Summary

The Elixire Assistant converts training resources (like YouTube transcripts) into a searchable vector database. User queries are processed through language detection, translation, vector retrieval, and LLM generation to produce short, accurate, pharmacist-friendly outputs.


## The System Uses

Gemini Embeddings
ChromaDB
Groq LLM (generation and translation)
SentenceTransformer (BGE-large)
React frontend + Python backend

## Key Features

Multilingual support (automatic language detection and translation)
Retrieval-Augmented Generation (RAG) using ChromaDB
Step-wise, concise answers for pharmacy users
Low hallucination due to strict context grounding
Pluggable LLM backends (Groq, Gemini, Ollama)
Modular architecture for easy integration into web or desktop apps


## System Architecture Overview

### 1. Knowledge Base Preparation

YouTube transcripts are cleaned and chunked
Embeddings are generated using BGE-large
Chunks and embeddings are stored in a ChromaDB persistent collection


### 2. Query Processing

User's language is detected using Groq LLM
Query is translated into English
Query is embedded using Gemini Embeddings
ChromaDB is queried to retrieve the most relevant chunks


### 3. Response Generation

Groq LLM uses retrieved context and system rules
Generates short, numbered, step-wise responses
Translates the output back to the user’s original language
The frontend displays the final formatted answer
>>>>>>> 806a4659ba9ced329b9811f5ded1618d095e9b75

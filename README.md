
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

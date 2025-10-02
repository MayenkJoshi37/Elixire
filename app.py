# app.py
import os
import re
import json
import zipfile
import shutil
import tempfile
from typing import Optional
import chromadb
import requests
from dotenv import load_dotenv
from langchain_groq import ChatGroq as groq
from langchain_core.messages import HumanMessage, SystemMessage
from google import genai

load_dotenv()

# --- Config (tweak via env) ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("Please set GEMINI_API_KEY in your environment (.env or export).")
client = genai.Client(api_key=GEMINI_API_KEY)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")

# Where Chroma DB will live inside the container
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
# URL to download zipped chroma_db (set in Render env vars); prefer a direct HTTPS URL (S3, Drive 'uc?export=download&id=...', Dropbox direct link, etc.)
CHROMA_DB_DOWNLOAD_URL = os.getenv("CHROMA_DB_DOWNLOAD_URL")
# Optional: if using Google Drive and you only have the file id, Render can build a download URL
CHROMA_DB_DRIVE_FILE_ID = os.getenv("CHROMA_DB_DRIVE_FILE_ID")

# --- Helper: download & extract chroma db ---
def _is_chroma_present(path: str) -> bool:
    try:
        return os.path.isdir(path) and len(os.listdir(path)) > 0
    except Exception:
        return False

def _save_stream_to_file(resp, dest_path: str):
    # stream write to file
    with open(dest_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=32768):
            if chunk:
                f.write(chunk)

def _download_from_google_drive(file_id: str, dest: str, session: Optional[requests.Session] = None):
    # Handles Drive "large file" confirm flow
    if session is None:
        session = requests.Session()
    URL = "https://docs.google.com/uc?export=download"
    resp = session.get(URL, params={"id": file_id}, stream=True, timeout=60)
    token = None
    for k, v in resp.cookies.items():
        if k.startswith("download_warning"):
            token = v
            break
    if token:
        resp = session.get(URL, params={"id": file_id, "confirm": token}, stream=True, timeout=60)
    resp.raise_for_status()
    _save_stream_to_file(resp, dest)

def _download_url_to_file(url: str, dest: str):
    session = requests.Session()
    # special-case Google Drive links
    if "drive.google.com" in url and "uc?export=download" not in url:
        # try to extract id (works for many share link forms)
        # Examples:
        # https://drive.google.com/file/d/<FILEID>/view?usp=sharing
        import re
        m = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
        if m:
            file_id = m.group(1)
            return _download_from_google_drive(file_id, dest, session=session)
        # else fallback to streaming the URL directly
    resp = session.get(url, stream=True, timeout=60)
    resp.raise_for_status()
    _save_stream_to_file(resp, dest)

def ensure_chroma_db_available():
    """
    If CHROMA_PATH already exists and has files, do nothing.
    Otherwise attempt to download a zip and extract it into CHROMA_PATH.
    """
    if _is_chroma_present(CHROMA_PATH):
        print(f"[Chroma] Found existing ChromaDB at {CHROMA_PATH}")
        return

    # Determine a download URL
    download_url = CHROMA_DB_DOWNLOAD_URL
    if not download_url and CHROMA_DB_DRIVE_FILE_ID:
        download_url = f"https://docs.google.com/uc?export=download&id={CHROMA_DB_DRIVE_FILE_ID}"

    if not download_url:
        print("[Chroma] No CHROMA_DB_DOWNLOAD_URL or CHROMA_DB_DRIVE_FILE_ID set; starting without persistent DB.")
        return

    print(f"[Chroma] Will attempt to download ChromaDB from: {download_url}")

    # Make temp file
    tmp_dir = tempfile.mkdtemp()
    try:
        zip_path = os.path.join(tmp_dir, "chroma_db.zip")
        print(f"[Chroma] Downloading to temporary file: {zip_path} ... (this may take a minute)")
        try:
            _download_url_to_file(download_url, zip_path)
        except Exception as e:
            print(f"[Chroma] Download failed: {e}")
            raise

        # Extract
        print(f"[Chroma] Extracting {zip_path} -> {CHROMA_PATH} ...")
        os.makedirs(CHROMA_PATH, exist_ok=True)
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(CHROMA_PATH)
        except zipfile.BadZipFile:
            # maybe the uploaded file wasn't zipped — try copying it directly (as fallback)
            print("[Chroma] Not a zip file; attempting to move file into CHROMA_PATH directly.")
            shutil.copy(zip_path, os.path.join(CHROMA_PATH, "chroma_db_downloaded"))
        print("[Chroma] Extraction complete.")
    finally:
        try:
            shutil.rmtree(tmp_dir)
        except Exception:
            pass

# Ensure DB present (or at least attempt to fetch it) *before* creating the persistent client
try:
    ensure_chroma_db_available()
except Exception as e:
    # If download fails, we still proceed — app will run but any queries that hit the vector DB may fail.
    print(f"[Warning] ensure_chroma_db_available failed: {e}")

# --- Initialize ChromaDB persistent client AFTER the above attempt ---
try:
    vector_db = chromadb.PersistentClient(path=CHROMA_PATH)
    print(f"[Info] Initialized chroma PersistentClient at {CHROMA_PATH}")
except Exception as e:
    # If initialization fails, raise an informative error so logs show what's wrong.
    raise RuntimeError(f"Failed to initialize ChromaDB PersistentClient at {CHROMA_PATH}: {e}")

COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "elixire_docs_bge_large")
collection = vector_db.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)
print(f"[Info] Connected to ChromaDB collection: {COLLECTION_NAME} at {CHROMA_PATH}")

# --- GROQ LLM setup (unchanged) ---
llm_groq = groq(model_name=os.getenv("GROQ_MODEL_NAME", "openai/gpt-oss-120b"), api_key=os.getenv("GROQ_API_KEY"))

# --- embedding helpers (unchanged) ---
def _extract_numeric_list(obj):
    while isinstance(obj, (list, tuple)) and len(obj) == 1:
        obj = obj[0]
    if isinstance(obj, (list, tuple)):
        if all(isinstance(x, (int, float)) for x in obj):
            return [float(x) for x in obj]
    if hasattr(obj, "values"):
        try:
            return _extract_numeric_list(obj.values)
        except Exception:
            pass
    if hasattr(obj, "value"):
        try:
            return _extract_numeric_list(obj.value)
        except Exception:
            pass
    numeric = []
    def _r(x):
        if isinstance(x, (int, float)):
            numeric.append(float(x)); return
        if isinstance(x, (list, tuple)):
            for y in x: _r(y); return
        if isinstance(x, dict):
            for v in x.values(): _r(v); return
        if hasattr(x, "values"): _r(x.values); return
        if hasattr(x, "value"): _r(x.value); return
    _r(obj)
    return numeric

def embed_text(text: str):
    resp = client.models.embed_content(model=EMBEDDING_MODEL, contents=text)
    embeddings = getattr(resp, "embeddings", None)
    if embeddings is None:
        try:
            embeddings = resp.get("embeddings")
        except Exception:
            embeddings = None
    if embeddings is None:
        raise RuntimeError("Gemini did not return embeddings for the query. Resp repr: " + repr(resp))
    if isinstance(embeddings, (list, tuple)) and (len(embeddings) == 0):
        return []
    if isinstance(embeddings, (list, tuple)) and all(isinstance(x, (int, float)) for x in embeddings):
        return [float(x) for x in embeddings]
    first = embeddings[0]
    vec = _extract_numeric_list(first)
    if not vec:
        raise RuntimeError("Could not parse embedding returned by Gemini (unexpected structure).")
    return vec

def get_relevant_chunks(query: str, n_results: int = 1) -> list:
    query_embedding = embed_text(query)
    results = collection.query(query_embeddings=[query_embedding], n_results=n_results)
    docs = []
    try:
        docs = results.get("documents", [[]])[0]
    except Exception:
        if "documents" in results and results["documents"]:
            docs = results["documents"][0]
    return docs or []

def generate_response(user_message: str, context_chunks: list) -> str:
    context = "\n\n".join(context_chunks)
    system_prompt = f"""
    You are the Elixire Assistant — a helpful chatbot inside Elixire, a pharmacy management solution.
    Your job is to give users a simple, concise and clear answer.
    Follow these rules for answering:

    GOAL:
    - Give clear, accurate, and concise answers for non-technical users.
    - Entire response must be short and skimmable

    STRUCTURE:
    1. Provide numbered, actionable steps.
    2. Add up to 1 troubleshooting tip only if critical.

    CONTEXT USE:
    - Base your answer strictly on the provided context.
    - If the query is ambiguous, state one simple assumption before answering.
    - Never invent features or information not present in the context.

    STYLE:
    - Professional, friendly, plain language.
    - Avoid jargon (or explain briefly if used).
    - Never provide medical, legal, or regulatory advice.

    Context:
    {context}
    """

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]

    print(f"\n--- Sending prompt to GROQ ---")
    return llm_groq.invoke(messages).content

def format_llm_output(response: str) -> str:
    response = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL)
    response = re.sub(r"\*\*(.*?)\*\*", r"\033[1m\1\033[0m", response)
    response = re.sub(r"\n\s*\n", "\n\n", response.strip())
    return response

def preprocess_user_query(user_message: str) -> dict:
    system_prompt = """
    You are a query pre-processor for a multilingual assistant.
    - If the user query is in English: refine/clean it.
    - If the user query is not in English: translate it into clear English.
    - Always detect the user's original language (use ISO 639-1 code if possible, else language name).
    - Respond ONLY in valid JSON, no extra text.
    Format:
    {
      "user_query_eng": "<refined_or_translated_query_in_english>",
      "user_original_query_lang": "<detected_language_code_or_name>"
    }
    """
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]
    raw_response = llm_groq.invoke(messages).content
    try:
        return json.loads(raw_response)
    except json.JSONDecodeError:
        print("[Warning] Groq did not return valid JSON, falling back.")
        return {
            "user_query_eng": user_message,
            "user_original_query_lang": "en",
        }

def normalize_lang_code(lang: str) -> str:
    lang = lang.strip().lower()
    mapping = {
        "en": "English",
        "english": "English",
        "hi": "Hindi",
        "hindi": "Hindi",
        "mr": "Marathi",
        "marathi": "Marathi",
        "bn": "Bengali",
        "bengali": "Bengali",
        "gu": "Gujarati",
        "gujarati": "Gujarati",
    }
    return mapping.get(lang, lang.capitalize())

def postprocess_answer(answer_eng: str, target_lang: str) -> str:
    target_lang = normalize_lang_code(target_lang)
    if target_lang == "English":
        return answer_eng
    system_prompt = f"""
    You are a translator.
    Convert the following English text into {target_lang}.
    - Keep the same numbering, steps, and structure.
    - Do not add extra commentary.
    """
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=answer_eng),
    ]
    try:
        return llm_groq.invoke(messages).content
    except Exception as e:
        print(f"[Warning] Translation failed: {e}")
        return answer_eng


# (Interactive main loop commented out, keep as before)
# def main():
#     print("\n[Info] Running in GROQ-only mode.")
#     print("Enter your message. Type 'quit' or 'exit' to end the chat.")

#     while True:
#         user_message = input("\nYou: ")
#         if user_message.lower() in ["quit", "exit"]:
#             print("Goodbye!")
#             break

#         # Step 1: preprocess user query
#         print("[Step 1] Preprocessing user query...")
#         query_data = preprocess_user_query(user_message)
#         user_query_eng = query_data["user_query_eng"]
#         user_lang = query_data["user_original_query_lang"]
#         print(f"[Info] Refined/translated query: {user_query_eng}")
#         print(f"[Info] Original language: {user_lang}")

#         # Step 2: retrieve context
#         print("[Step 2] Searching knowledge base for relevant context...")
#         relevant_chunks = get_relevant_chunks(user_query_eng)
#         print(f"[Info] Retrieved {len(relevant_chunks)} relevant chunk(s).")

#         # Step 3: generate English answer
#         print("[Step 3] Generating response from Groq...")
#         final_response_eng = generate_response(user_query_eng, relevant_chunks)

#         # Step 4: postprocess answer into original language (if needed)
#         print("[Step 4] Translating answer back (if required)...")
#         final_response = postprocess_answer(final_response_eng, user_lang)

#         formatted = format_llm_output(final_response)
#         print(f"\n--- GROQ's Response ---\n")
#         print(formatted)
#         print("\n--- End of response ---\n")


# if __name__ == "__main__":
#     main()

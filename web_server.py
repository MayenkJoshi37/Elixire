# web_server.py
import os
import logging
from typing import List, Dict, Any
from flask import Flask, request, jsonify, render_template

# import your existing business logic from app.py
from app import (
    preprocess_user_query,
    get_relevant_chunks,
    generate_response,
    postprocess_answer,
    format_llm_output,
)

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("web_server")

app = Flask(__name__, static_folder="static", template_folder="templates")

# Configuration
DEFAULT_N_RESULTS = int(os.getenv("DEFAULT_N_RESULTS", "1"))
MAX_N_RESULTS = int(os.getenv("MAX_N_RESULTS", "5"))

@app.route("/health", methods=["GET"])
def health() -> Any:
    return jsonify({"status": "ok"}), 200

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        payload = request.get_json(force=True, silent=True)
        if not payload:
            return jsonify({"success": False, "error": "Expected JSON body"}), 400

        user_message = (payload.get("message") or "").strip()
        if not user_message:
            return jsonify({"success": False, "error": "Empty 'message' field"}), 400

        try:
            n_results = int(payload.get("n_results", DEFAULT_N_RESULTS))
        except Exception:
            n_results = DEFAULT_N_RESULTS
        if n_results < 1 or n_results > MAX_N_RESULTS:
            n_results = DEFAULT_N_RESULTS

        logger.info("Received chat request; n_results=%s", n_results)

        # Step 1: preprocess (refine/translate to English)
        query_data = preprocess_user_query(user_message)
        user_query_eng = query_data.get("user_query_eng", user_message)
        user_lang = query_data.get("user_original_query_lang", "en")

        # Step 2: retrieve context
        relevant_chunks: List[str] = get_relevant_chunks(user_query_eng, n_results=n_results)

        # Step 3: generate English response
        final_response_eng = generate_response(user_query_eng, relevant_chunks)

        # Step 4: postprocess (translate back if needed)
        final_response = postprocess_answer(final_response_eng, user_lang)

        formatted = format_llm_output(final_response)

        return (
            jsonify(
                {
                    "success": True,
                    "answer": formatted,
                    "used_chunks": relevant_chunks,
                    "original_language": user_lang,
                }
            ),
            200,
        )

    except Exception as e:
        logger.exception("Unhandled error in /chat")
        return jsonify({"success": False, "error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8000)), debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")

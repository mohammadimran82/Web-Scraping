from flask import Flask, render_template, request, jsonify

from ask_rag import get_rag_answer


# ============================================================
# CREATE FLASK APP
# ============================================================

app = Flask(__name__)


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ============================================================
# ASK RAG
# ============================================================

@app.route(
    "/ask",
    methods=["POST"]
)
def ask():

    try:

        data = request.get_json()

        question = data.get(
            "question",
            ""
        ).strip()

        if not question:

            return jsonify({
                "answer": "Please enter a question.",
                "sources": []
            })


        # ----------------------------------------------------
        # Send question to RAG
        # ----------------------------------------------------

        result = get_rag_answer(
            question
        )


        # ----------------------------------------------------
        # Return RAG answer to browser
        # ----------------------------------------------------

        return jsonify({
            "answer": result["answer"],
            "sources": result["sources"]
        })


    except Exception as e:

        print(
            "ERROR:",
            str(e)
        )

        return jsonify({
            "answer": "Something went wrong while generating the answer.",
            "sources": []
        }), 500


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )
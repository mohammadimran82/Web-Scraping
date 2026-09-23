import ollama
from sentence_transformers import SentenceTransformer
import chromadb
import re


# ============================================================
# SETTINGS
# ============================================================

MODEL_NAME = "llama3.2:3b"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "web_scraper_rag"

TOP_K = 3


# ============================================================
# LOAD EMBEDDING MODEL
# ============================================================

print("Loading embedding model...")

embedding_model = SentenceTransformer(
    EMBEDDING_MODEL
)


# ============================================================
# CONNECT TO CHROMA
# ============================================================

print("Connecting to ChromaDB...")

client = chromadb.PersistentClient(
    path="data/chroma_db"
)

collection = client.get_collection(
    name=COLLECTION_NAME
)

print("RAG system ready.")


# ============================================================
# SEARCH DOCUMENTS
# ============================================================

def search_documents(question):

    question_embedding = embedding_model.encode(
        question
    ).tolist()

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=30
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    combined_results = []

    for document, metadata, distance in zip(
        documents,
        metadatas,
        distances
    ):

        combined_results.append({
            "content": document,
            "metadata": metadata,
            "distance": distance
        })

    return combined_results


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize_text(text):

    return re.sub(
        r"\s+",
        " ",
        text.lower()
    ).strip()


# ============================================================
# LEXICAL SCORE
# ============================================================

def lexical_score(question, document):

    question = normalize_text(question)
    document = normalize_text(document)

    score = 0

    words = re.findall(
        r"\b[a-zA-Z][a-zA-Z0-9_-]*\b",
        question
    )

    for word in words:

        if len(word) < 3:
            continue

        if re.search(
            rf"\b{re.escape(word)}\b",
            document,
            re.IGNORECASE
        ):

            score += 20

    if question in document:
        score += 50

    definition_patterns = [

        r"skuid\s*\|",

        r"skuid\s*:",

        r"skuid\s*-\s*",

        r"skuid\s+is\s+",

        r"skuid\s+means\s+",

        r"definition\s+of\s+skuid"
    ]

    for pattern in definition_patterns:

        if re.search(
            pattern,
            document,
            re.IGNORECASE
        ):

            score += 50

            break

    return score


# ============================================================
# RERANK RESULTS
# ============================================================

def rerank_results(question, results):

    reranked = []

    for result in results:

        lexical = lexical_score(
            question,
            result["content"]
        )

        distance = result["distance"]

        semantic = max(
            0,
            50 - (distance * 20)
        )

        final_score = (
            lexical * 10
            + semantic
        )

        result["lexical_score"] = lexical
        result["semantic_score"] = semantic
        result["final_score"] = final_score

        reranked.append(result)

    reranked.sort(
        key=lambda x: x["final_score"],
        reverse=True
    )

    return reranked[:TOP_K]


# ============================================================
# BUILD CONTEXT
# ============================================================

def build_context(results):

    context_parts = []

    for index, result in enumerate(
        results,
        start=1
    ):

        title = result["metadata"].get(
            "title",
            "Unknown"
        )

        url = result["metadata"].get(
            "url",
            ""
        )

        content = result["content"]

        context_parts.append(
            f"""
SOURCE {index}

Title:
{title}

URL:
{url}

Content:
{content}
"""
        )

    return "\n".join(
        context_parts
    )


# ============================================================
# GENERATE ANSWER
# ============================================================

def generate_answer(question, context):

    prompt = f"""
You are a documentation assistant.

Answer the user's question using ONLY the documentation
inside CONTEXT.

USER QUESTION:
{question}

CONTEXT:
{context}

INSTRUCTIONS:

- Give a direct answer to the question.
- Look carefully at the documentation before answering.
- If the documentation contains an exact definition,
  use that definition.
- Do not answer with only the name of the field.
- Explain what the field means.
- Do not invent information.
- Do not use outside knowledge.
- Keep the answer short and clear.

ANSWER:
"""

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response["message"]["content"]


# ============================================================
# MAIN RAG FUNCTION
# ============================================================

def get_rag_answer(question):

    results = search_documents(
        question
    )

    results = rerank_results(
        question,
        results
    )

    context = build_context(
        results
    )

    answer = generate_answer(
        question,
        context
    )

    return {
        "answer": answer,
        "sources": [
            {
                "title": result["metadata"].get(
                    "title",
                    "Unknown"
                ),
                "url": result["metadata"].get(
                    "url",
                    ""
                ),
                "score": round(
                    result["final_score"],
                    2
                )
            }
            for result in results
        ]
    }


# ============================================================
# TERMINAL CHAT MODE
# ============================================================

if __name__ == "__main__":

    while True:

        print("\n")

        question = input(
            "You: "
        ).strip()

        if not question:
            continue

        if question.lower() in [
            "exit",
            "quit",
            "bye"
        ]:

            print("\nGoodbye!")

            break

        print("\n")
        print("Search question:")
        print(question)

        result = get_rag_answer(
            question
        )

        print("\n")
        print("Retrieved sources:")

        for index, source in enumerate(
            result["sources"],
            start=1
        ):

            print("-" * 60)

            print(
                f"Rank: {index}"
            )

            print(
                f"Score: {source['score']}"
            )

            print(
                "Title:",
                source["title"]
            )

            print(
                "URL:",
                source["url"]
            )

        print("\n")
        print("Generating answer...")

        print("\n")
        print("AI:")

        print(
            result["answer"]
        )
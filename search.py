import re
import chromadb
from sentence_transformers import SentenceTransformer


# ==========================================
# SETTINGS
# ==========================================

VECTOR_DB_PATH = "data/chroma_db"
COLLECTION_NAME = "web_scraper_rag"

# Number of semantic candidates to retrieve
SEMANTIC_K = 30

# Number of final results to display
FINAL_K = 10


# ==========================================
# LOAD EMBEDDING MODEL
# ==========================================

print("Loading embedding model...")

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


# ==========================================
# CONNECT TO CHROMADB
# ==========================================

print("Connecting to ChromaDB...")

chroma_client = chromadb.PersistentClient(
    path=VECTOR_DB_PATH
)

collection = chroma_client.get_collection(
    name=COLLECTION_NAME
)

print("Search system ready.")


# ==========================================
# TEXT NORMALIZATION
# ==========================================

def normalize_text(text):
    """
    Convert text into a simple lowercase form
    for exact keyword matching.
    """

    if not text:
        return ""

    text = str(text).lower()

    return text


# ==========================================
# GET SEARCH TERMS
# ==========================================

def get_search_terms(question):
    """
    Extract useful words from the user's question.
    """

    question = normalize_text(question)

    terms = re.findall(
        r"[a-zA-Z0-9_]+",
        question
    )

    # Remove very common question words
    stop_words = {
        "what",
        "is",
        "are",
        "the",
        "a",
        "an",
        "of",
        "for",
        "to",
        "how",
        "does",
        "do",
        "can",
        "and",
        "or",
        "in",
        "on",
        "with",
        "this",
        "that"
    }

    terms = [
        term
        for term in terms
        if term not in stop_words
    ]

    return terms


# ==========================================
# LEXICAL SCORE
# ==========================================

def calculate_lexical_score(
    question,
    document
):
    """
    Give higher scores to documents that contain
    the exact words from the question.

    This helps distinguish:

        skuId
        sku_ids
        SKU Ids

    from a purely semantic match.
    """

    question = normalize_text(question)
    document = normalize_text(document)

    terms = get_search_terms(question)

    if not terms:
        return 0

    score = 0

    for term in terms:

        # ----------------------------------
        # Exact phrase match
        # ----------------------------------

        exact_count = document.count(term)

        if exact_count > 0:
            score += 10 * exact_count

        # ----------------------------------
        # Word-boundary exact match
        # ----------------------------------

        pattern = r"\b" + re.escape(term) + r"\b"

        exact_word_matches = re.findall(
            pattern,
            document
        )

        if exact_word_matches:
            score += 20 * len(exact_word_matches)

    # ======================================
    # DEFINITION BONUS
    # ======================================

    # Give additional importance to text that
    # looks like a definition.

    for term in terms:

        definition_patterns = [

            term + " ->",

            term + ":",

            term + " -",

            term + " is ",

            term + " means ",

            "definition of " + term,

        ]

        for pattern in definition_patterns:

            if pattern in document:
                score += 50

    return score


# ==========================================
# SEMANTIC SEARCH
# ==========================================

def semantic_search(question):

    question_embedding = embedding_model.encode(
        question
    ).tolist()

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=SEMANTIC_K
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    semantic_results = []

    for i in range(len(documents)):

        semantic_results.append({
            "document": documents[i],
            "metadata": metadatas[i],
            "distance": distances[i]
        })

    return semantic_results


# ==========================================
# EXACT SEARCH THROUGH ALL DOCUMENTS
# ==========================================

def exact_search(question):

    # Get every document stored in ChromaDB.
    #
    # Our current database contains only a few
    # hundred chunks, so scanning them is fine.

    all_data = collection.get(
        include=[
            "documents",
            "metadatas"
        ]
    )

    documents = all_data["documents"]
    metadatas = all_data["metadatas"]

    exact_results = []

    for i in range(len(documents)):

        document = documents[i]

        lexical_score = calculate_lexical_score(
            question,
            document
        )

        if lexical_score > 0:

            exact_results.append({
                "document": document,
                "metadata": metadatas[i],
                "lexical_score": lexical_score
            })

    return exact_results


# ==========================================
# HYBRID SEARCH
# ==========================================

def hybrid_search(question):

    print("\nPerforming semantic search...")

    semantic_results = semantic_search(
        question
    )

    print(
        f"Semantic candidates found: "
        f"{len(semantic_results)}"
    )

    print("\nPerforming exact keyword search...")

    exact_results = exact_search(
        question
    )

    print(
        f"Exact-match candidates found: "
        f"{len(exact_results)}"
    )

    # ======================================
    # COMBINE RESULTS
    # ======================================

    combined = {}

    # --------------------------------------
    # Add semantic results
    # --------------------------------------

    for rank, result in enumerate(
        semantic_results
    ):

        document = result["document"]

        key = document

        combined[key] = {
            "document": document,
            "metadata": result["metadata"],
            "distance": result["distance"],
            "lexical_score": 0,
            "semantic_rank": rank + 1
        }

    # --------------------------------------
    # Add exact results
    # --------------------------------------

    for result in exact_results:

        document = result["document"]

        key = document

        if key not in combined:

            combined[key] = {
                "document": document,
                "metadata": result["metadata"],
                "distance": 999,
                "lexical_score": result["lexical_score"],
                "semantic_rank": 999
            }

        else:

            combined[key]["lexical_score"] = (
                result["lexical_score"]
            )

    # ======================================
    # FINAL RANKING
    # ======================================

    results = list(
        combined.values()
    )

    for result in results:

        lexical_score = result[
            "lexical_score"
        ]

        semantic_rank = result[
            "semantic_rank"
        ]

        # Semantic ranking contribution
        if semantic_rank < 999:

            semantic_score = (
                SEMANTIC_K - semantic_rank + 1
            )

        else:

            semantic_score = 0

        # Exact matching is intentionally
        # given much more importance.

        final_score = (
            lexical_score * 10
            + semantic_score
        )

        result["semantic_score"] = (
            semantic_score
        )

        result["final_score"] = (
            final_score
        )

    # Highest score first
    results.sort(
        key=lambda x: x["final_score"],
        reverse=True
    )

    return results[:FINAL_K]


# ==========================================
# DISPLAY RESULTS
# ==========================================

while True:

    question = input(
        "\nAsk a question: "
    ).strip()

    if question.lower() == "exit":
        print("\nGoodbye!")
        break

    if not question:
        continue

        print("\n")
    print("=" * 60)
    print("HYBRID SEARCH RESULTS")
    print("=" * 60)

    results = hybrid_search(question)

    # Save results to a text file
    with open(
        "search_results.txt",
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            "HYBRID SEARCH RESULTS\n"
        )

        file.write(
            "=" * 60 + "\n\n"
        )

        for i, result in enumerate(
            results,
            start=1
        ):

            metadata = result["metadata"]

            output = f"""
------------------------------------------------------------
Result {i}
------------------------------------------------------------
Final score: {result['final_score']}
Lexical score: {result['lexical_score']}
Semantic score: {result['semantic_score']}
Semantic distance: {result['distance']}

Title: {metadata.get('title', '')}

URL: {metadata.get('url', '')}

Content:

{result['document']}

"""

            print(output)

            file.write(output)

    print("\n")
    print("=" * 60)
    print("SEARCH RESULTS SAVED")
    print("=" * 60)

    print("\nFile created:")
    print("search_results.txt")

    for i, result in enumerate(
        results,
        start=1
    ):

        metadata = result["metadata"]

        print("\n")
        print("-" * 60)
        print(f"Result {i}")
        print("-" * 60)

        print(
            f"Final score: "
            f"{result['final_score']}"
        )

        print(
            f"Lexical score: "
            f"{result['lexical_score']}"
        )

        print(
            f"Semantic score: "
            f"{result['semantic_score']}"
        )

        print(
            f"Semantic distance: "
            f"{result['distance']}"
        )

        print(
            f"Title: "
            f"{metadata.get('title', '')}"
        )

        print(
            f"URL: "
            f"{metadata.get('url', '')}"
        )

        print("\nContent:")

        print(
            result["document"][:1500]
        )
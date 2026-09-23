import chromadb
import ollama

from sentence_transformers import SentenceTransformer


# =========================================================
# 1. SETTINGS
# =========================================================

VECTOR_DB_PATH = "data/chroma_db"

COLLECTION_NAME = "web_scraper_rag"

# Chroma retrieves this many candidates
TOP_K = 10

# After filtering, send this many chunks to Llama
FINAL_CONTEXT_SIZE = 5


# =========================================================
# 2. LOAD EMBEDDING MODEL
# =========================================================

print("Loading embedding model...")

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


# =========================================================
# 3. CONNECT TO CHROMADB
# =========================================================

print("Connecting to ChromaDB...")

chroma_client = chromadb.PersistentClient(
    path=VECTOR_DB_PATH
)


# =========================================================
# 4. GET COLLECTION
# =========================================================

collection = chroma_client.get_collection(
    name=COLLECTION_NAME
)


print("RAG system ready.")


# =========================================================
# 5. CONVERSATION MEMORY
# =========================================================

conversation_history = []


# =========================================================
# 6. SIMPLE EXACT-TERM BOOST
# =========================================================

def calculate_relevance(question, document):
    """
    Gives an additional score when important words from
    the question appear directly inside the document.

    This helps distinguish terms such as:

        skuId
        sku

    """

    question_words = question.lower().split()

    document_lower = document.lower()

    score = 0

    for word in question_words:

        # Remove simple punctuation
        word = word.strip(
            ".,?!:;()[]{}\"'"
        )

        if not word:
            continue

        if word in document_lower:
            score += 1

    return score


# =========================================================
# 7. CHATBOT LOOP
# =========================================================

while True:

    question = input("\nYou: ").strip()


    # -----------------------------------------------------
    # EXIT
    # -----------------------------------------------------

    if question.lower() == "exit":

        print("\nGoodbye!")

        break


    # -----------------------------------------------------
    # IGNORE EMPTY QUESTIONS
    # -----------------------------------------------------

    if not question:

        continue


    # =====================================================
    # 8. REWRITE FOLLOW-UP QUESTION
    # =====================================================

    history_text = ""

    for message in conversation_history:

        history_text += f"""
{message["role"].upper()}:
{message["content"]}
"""


    # If there is no previous conversation, don't waste
    # an LLM call rewriting an already standalone question.

    if len(conversation_history) == 0:

        standalone_question = question

    else:

        rewrite_prompt = f"""
You rewrite questions for a documentation search system.

Rewrite the CURRENT QUESTION into a standalone search
question using the conversation history.

If the question is already standalone, keep its important
technical terms unchanged.

IMPORTANT:
Do not replace technical terms such as skuId, listingId,
seller SKU ID, orderItemId, listing ID, or API names.

Do not answer the question.

CONVERSATION:
{history_text}

CURRENT QUESTION:
{question}

STANDALONE SEARCH QUESTION:
"""


        rewrite_response = ollama.chat(
            model="llama3.2:3b",
            messages=[
                {
                    "role": "user",
                    "content": rewrite_prompt
                }
            ]
        )


        standalone_question = (
            rewrite_response["message"]["content"].strip()
        )


    print("\nSearch question:")
    print(standalone_question)


    # =====================================================
    # 9. CREATE QUESTION EMBEDDING
    # =====================================================

    question_embedding = embedding_model.encode(
        standalone_question
    ).tolist()


    # =====================================================
    # 10. SEARCH CHROMADB
    # =====================================================

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=TOP_K
    )


    # =====================================================
    # 11. GET RETRIEVED DOCUMENTS
    # =====================================================

    documents = results["documents"][0]

    metadatas = results["metadatas"][0]

    distances = results["distances"][0]


    # =====================================================
    # 12. RERANK RETRIEVED DOCUMENTS
    # =====================================================

    ranked_results = []


    for i in range(len(documents)):

        exact_score = calculate_relevance(
            standalone_question,
            documents[i]
        )

        ranked_results.append(
            {
                "document": documents[i],
                "metadata": metadatas[i],
                "distance": distances[i],
                "exact_score": exact_score
            }
        )


    # First prioritize exact-term matches.
    # Then use Chroma distance as the secondary signal.

    ranked_results.sort(
        key=lambda item: (
            -item["exact_score"],
            item["distance"]
        )
    )


    # Keep only the strongest evidence.

    final_results = ranked_results[
        :FINAL_CONTEXT_SIZE
    ]


    # =====================================================
    # 13. DISPLAY RETRIEVAL DEBUG INFORMATION
    # =====================================================

    print("\nRetrieved and reranked sources:")


    for i, result in enumerate(final_results):

        print("\n--------------------------------------")

        print(
            f"Rank: {i + 1}"
        )

        print(
            f"Exact-term score: {result['exact_score']}"
        )

        print(
            f"Distance: {result['distance']}"
        )

        print(
            f"Title: {result['metadata']['title']}"
        )

        print(
            f"URL: {result['metadata']['url']}"
        )


    # =====================================================
    # 14. BUILD FINAL DOCUMENTATION CONTEXT
    # =====================================================

    context_parts = []


    for i, result in enumerate(final_results):

        source_text = f"""
SOURCE {i + 1}

TITLE:
{result["metadata"]["title"]}

URL:
{result["metadata"]["url"]}

DOCUMENTATION:
{result["document"]}
"""

        context_parts.append(
            source_text
        )


    context = "\n\n".join(
        context_parts
    )


    # =====================================================
    # 15. FINAL ANSWER PROMPT
    # =====================================================

    prompt = f"""
You are a documentation question-answering assistant.

Answer the user's question using ONLY the documentation
sources provided below.

IMPORTANT RULES:

1. Find the exact technical term asked about.

2. If the question asks:
   "What is X?"
   look for a direct definition of X.

3. Prefer a definition where the exact term appears.

4. Do NOT confuse similar technical terms.

For example:

skuId
is different from
sku

listingId
is different from
orderItemId

5. If the documentation contains a direct definition,
use that definition.

6. Do not combine definitions of different fields.

7. Do not use outside knowledge.

8. Do not invent information.

9. Keep the answer short and direct.

10. If the documentation truly does not contain the answer,
say:

"I could not find that information in the provided documentation."

USER QUESTION:
{question}

DOCUMENTATION:
{context}

Now answer the USER QUESTION.

ANSWER:
"""


    # =====================================================
    # 16. GENERATE ANSWER
    # =====================================================

    print("\nGenerating answer...\n")


    response = ollama.chat(
        model="llama3.2:3b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )


    # =====================================================
    # 17. GET ANSWER
    # =====================================================

    answer = response["message"]["content"].strip()


    print("AI:")
    print(answer)


    # =====================================================
    # 18. SAVE CONVERSATION
    # =====================================================

    conversation_history.append(
        {
            "role": "user",
            "content": question
        }
    )


    conversation_history.append(
        {
            "role": "assistant",
            "content": answer
        }
    )


    # =====================================================
    # 19. DISPLAY FINAL SOURCES
    # =====================================================

    print("\nFinal Sources:")


    for i, result in enumerate(final_results):

        print(
            f"{i + 1}. {result['metadata']['title']}"
        )

        print(
            f"   {result['metadata']['url']}"
        )
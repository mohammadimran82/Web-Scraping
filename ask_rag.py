import chromadb
import ollama

from sentence_transformers import SentenceTransformer


# ---------------------------------------------------------
# 1. Settings
# ---------------------------------------------------------

VECTOR_DB_PATH = "data/chroma_db"

COLLECTION_NAME = "web_scraper_rag"

TOP_K = 3


# ---------------------------------------------------------
# 2. Load embedding model
# ---------------------------------------------------------

print("Loading embedding model...")

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


# ---------------------------------------------------------
# 3. Connect to ChromaDB
# ---------------------------------------------------------

print("Connecting to ChromaDB...")

chroma_client = chromadb.PersistentClient(
    path=VECTOR_DB_PATH
)


# ---------------------------------------------------------
# 4. Get collection
# ---------------------------------------------------------

collection = chroma_client.get_collection(
    name=COLLECTION_NAME
)


# ---------------------------------------------------------
# 5. Conversation memory
# ---------------------------------------------------------

conversation_history = []


# ---------------------------------------------------------
# 6. Chatbot loop
# ---------------------------------------------------------

while True:

    question = input(
        "\nYou: "
    ).strip()


    # -----------------------------------------------------
    # Exit chatbot
    # -----------------------------------------------------

    if question.lower() == "exit":

        print("\nGoodbye!")

        break


    # -----------------------------------------------------
    # Ignore empty questions
    # -----------------------------------------------------

    if not question:

        continue


    # -----------------------------------------------------
# 7. Rewrite follow-up question
# -----------------------------------------------------

history_text = ""

for message in conversation_history:

    history_text += f"""
{message["role"].upper()}:
{message["content"]}
"""


rewrite_prompt = f"""
You are helping a RAG system understand follow-up questions.

Look at the conversation history and rewrite the
CURRENT QUESTION into a standalone question.

The rewritten question must contain all the important
information needed to search the documentation.

Do not answer the question.

CONVERSATION HISTORY:
{history_text}

CURRENT QUESTION:
{question}

STANDALONE QUESTION:
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


standalone_question = rewrite_response["message"]["content"].strip()


print("\nSearch question:")
print(standalone_question)


    # -----------------------------------------------------
    # 8. Search ChromaDB
    # -----------------------------------------------------

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=TOP_K
    )


    # -----------------------------------------------------
    # 9. Get retrieved documents
    # -----------------------------------------------------

    documents = results["documents"][0]

    metadatas = results["metadatas"][0]


    # -----------------------------------------------------
    # 10. Build documentation context
    # -----------------------------------------------------

    context_parts = []


    for i in range(len(documents)):

        source_text = f"""
SOURCE {i + 1}

Title:
{metadatas[i]["title"]}

URL:
{metadatas[i]["url"]}

Content:
{documents[i]}
"""

        context_parts.append(
            source_text
        )


    context = "\n\n".join(
        context_parts
    )


    # -----------------------------------------------------
    # 11. Build conversation history
    # -----------------------------------------------------

    history_text = ""


    for message in conversation_history:

        history_text += f"""
{message["role"].upper()}:
{message["content"]}

"""


    # -----------------------------------------------------
    # 12. Create prompt
    # -----------------------------------------------------

    prompt = f"""
You are a helpful documentation assistant.

Answer the user's question using ONLY the
documentation context provided below.

You may use the conversation history to
understand what the user is referring to.

Do not use outside knowledge.

If the answer cannot be found in the
documentation, say:

"I could not find that information in the
provided documentation."

Do not invent information.

CONVERSATION HISTORY:
{history_text}

CURRENT USER QUESTION:
{question}

DOCUMENTATION CONTEXT:
{context}
"""


    # -----------------------------------------------------
    # 13. Send prompt to Llama
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # 14. Get AI answer
    # -----------------------------------------------------

    answer = response["message"]["content"]


    print("AI:")
    print(answer)


    # -----------------------------------------------------
    # 15. Save conversation
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # 16. Display sources
    # -----------------------------------------------------

    print("\nSources:")


    for i, metadata in enumerate(metadatas):

        print(
            f"{i + 1}. {metadata['title']}"
        )

        print(
            f"   {metadata['url']}"
        )
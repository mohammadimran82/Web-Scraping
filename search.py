import chromadb

from sentence_transformers import SentenceTransformer


# ---------------------------------------------------------
# 1. Settings
# ---------------------------------------------------------

VECTOR_DB_PATH = "data/chroma_db"

COLLECTION_NAME = "web_scraper_rag"

TOP_K = 10


# ---------------------------------------------------------
# 2. Load embedding model
# ---------------------------------------------------------

print("Loading embedding model...")

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


# ---------------------------------------------------------
# 3. Connect to ChromaDB
# ---------------------------------------------------------

client = chromadb.PersistentClient(
    path=VECTOR_DB_PATH
)


# ---------------------------------------------------------
# 4. Open our collection
# ---------------------------------------------------------

collection = client.get_collection(
    name=COLLECTION_NAME
)


# ---------------------------------------------------------
# 5. Ask the user for a question
# ---------------------------------------------------------

question = input(
    "\nAsk a question: "
).strip()


# ---------------------------------------------------------
# 6. Convert question into embedding
# ---------------------------------------------------------

question_embedding = model.encode(
    question
).tolist()


# ---------------------------------------------------------
# 7. Search ChromaDB
# ---------------------------------------------------------

results = collection.query(
    query_embeddings=[question_embedding],
    n_results=TOP_K
)


# ---------------------------------------------------------
# 8. Display results
# ---------------------------------------------------------

print()
print("======================================")
print("SEARCH RESULTS")
print("======================================")


documents = results["documents"][0]

metadatas = results["metadatas"][0]

distances = results["distances"][0]


for i in range(len(documents)):

    print()
    print("--------------------------------------")

    print(
        f"Result {i + 1}"
    )

    print("--------------------------------------")

    print(
        "Title:",
        metadatas[i]["title"]
    )

    print(
        "URL:",
        metadatas[i]["url"]
    )

    print(
        "Distance:",
        distances[i]
    )

    print()

    print(
        documents[i]
    )
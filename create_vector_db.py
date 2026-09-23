import json
import os

import chromadb


# ---------------------------------------------------------
# 1. File paths
# ---------------------------------------------------------

INPUT_FILE = "data/embeddings.json"
VECTOR_DB_PATH = "data/chroma_db"


# ---------------------------------------------------------
# 2. Load embeddings
# ---------------------------------------------------------

with open(
    INPUT_FILE,
    "r",
    encoding="utf-8"
) as file:

    embedded_chunks = json.load(file)


# ---------------------------------------------------------
# 3. Create ChromaDB client
# ---------------------------------------------------------

client = chromadb.PersistentClient(
    path=VECTOR_DB_PATH
)


# ---------------------------------------------------------
# 4. Delete old collection
# ---------------------------------------------------------

try:

    client.delete_collection(
        name="web_scraper_rag"
    )

    print("Old vector collection deleted.")

except Exception:

    print("No old collection found.")


# ---------------------------------------------------------
# 5. Create a fresh collection
# ---------------------------------------------------------

collection = client.create_collection(
    name="web_scraper_rag"
)


# ---------------------------------------------------------
# 6. Prepare data
# ---------------------------------------------------------

ids = []
documents = []
embeddings = []
metadatas = []


for chunk in embedded_chunks:

    ids.append(
        chunk["chunk_id"]
    )

    documents.append(
        chunk["text"]
    )

    embeddings.append(
        chunk["embedding"]
    )

    metadatas.append(
        chunk["metadata"]
    )


# ---------------------------------------------------------
# 7. Add data to ChromaDB
# ---------------------------------------------------------

collection.upsert(
    ids=ids,
    documents=documents,
    embeddings=embeddings,
    metadatas=metadatas
)


# ---------------------------------------------------------
# 8. Check database
# ---------------------------------------------------------

total_chunks = collection.count()


print()
print("======================================")
print("VECTOR DATABASE CREATED")
print("======================================")

print(
    "Chunks in embeddings.json:",
    len(embedded_chunks)
)

print(
    "Chunks stored:",
    total_chunks
)

print(
    "Database location:",
    VECTOR_DB_PATH
)
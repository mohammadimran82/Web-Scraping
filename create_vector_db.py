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
# 4. Create or open collection
# ---------------------------------------------------------

collection = client.get_or_create_collection(
    name="web_scraper_rag"
)


# ---------------------------------------------------------
# 5. Prepare data
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
# 6. Add data to ChromaDB
# ---------------------------------------------------------

collection.upsert(
    ids=ids,
    documents=documents,
    embeddings=embeddings,
    metadatas=metadatas
)


# ---------------------------------------------------------
# 7. Check database
# ---------------------------------------------------------

total_chunks = collection.count()


print()
print("======================================")
print("VECTOR DATABASE CREATED")
print("======================================")

print(
    "Chunks stored:",
    total_chunks
)

print(
    "Database location:",
    VECTOR_DB_PATH
)
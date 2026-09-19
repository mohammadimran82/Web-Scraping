import json
import os

from sentence_transformers import SentenceTransformer


# ---------------------------------------------------------
# 1. File paths
# ---------------------------------------------------------

INPUT_FILE = "data/chunks.json"
OUTPUT_FILE = "data/embeddings.json"


# ---------------------------------------------------------
# 2. Load chunks
# ---------------------------------------------------------

with open(
    INPUT_FILE,
    "r",
    encoding="utf-8"
) as file:

    chunks = json.load(file)


# ---------------------------------------------------------
# 3. Load embedding model
# ---------------------------------------------------------

print("Loading embedding model...")

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


# ---------------------------------------------------------
# 4. Extract text from chunks
# ---------------------------------------------------------

texts = []

for chunk in chunks:

    texts.append(
        chunk["text"]
    )


# ---------------------------------------------------------
# 5. Generate embeddings
# ---------------------------------------------------------

print("Creating embeddings...")

embeddings = model.encode(
    texts,
    show_progress_bar=True
)


# ---------------------------------------------------------
# 6. Create output
# ---------------------------------------------------------

embedded_chunks = []


for chunk, embedding in zip(
    chunks,
    embeddings
):

    embedded_chunk = {

        "chunk_id": chunk["chunk_id"],

        "text": chunk["text"],

        "metadata": chunk["metadata"],

        "embedding": embedding.tolist()

    }

    embedded_chunks.append(
        embedded_chunk
    )


# ---------------------------------------------------------
# 7. Create data directory
# ---------------------------------------------------------

os.makedirs(
    "data",
    exist_ok=True
)


# ---------------------------------------------------------
# 8. Save embeddings
# ---------------------------------------------------------

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        embedded_chunks,
        file,
        indent=4,
        ensure_ascii=False
    )


# ---------------------------------------------------------
# 9. Finished
# ---------------------------------------------------------

print()
print("======================================")
print("EMBEDDING CREATION COMPLETED")
print("======================================")

print(
    "Chunks processed:",
    len(chunks)
)

print(
    "Output saved to:",
    OUTPUT_FILE
)
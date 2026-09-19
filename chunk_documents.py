import json
import os


# ---------------------------------------------------------
# 1. Settings
# ---------------------------------------------------------

INPUT_FILE = "data/documents.json"
OUTPUT_FILE = "data/chunks.json"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


# ---------------------------------------------------------
# 2. Load documents
# ---------------------------------------------------------

with open(
    INPUT_FILE,
    "r",
    encoding="utf-8"
) as file:

    documents = json.load(file)


# ---------------------------------------------------------
# 3. Create chunks
# ---------------------------------------------------------

chunks = []


# ---------------------------------------------------------
# 4. Process every document
# ---------------------------------------------------------

for document_index, document in enumerate(documents):

    text = document["text"]

    metadata = document["metadata"]


    # -----------------------------------------------------
    # Starting position
    # -----------------------------------------------------

    start = 0

    chunk_number = 0


    # -----------------------------------------------------
    # Split document
    # -----------------------------------------------------

    while start < len(text):

        end = start + CHUNK_SIZE

        chunk_text = text[start:end]


        # -------------------------------------------------
        # Store chunk
        # -------------------------------------------------

        chunk = {

            "chunk_id": (
                f"doc_{document_index}_"
                f"chunk_{chunk_number}"
            ),

            "text": chunk_text,

            "metadata": {

                "title": metadata["title"],

                "url": metadata["url"],

                "document_id": document_index,

                "chunk_number": chunk_number

            }

        }


        chunks.append(chunk)


        # -------------------------------------------------
        # Move forward with overlap
        # -------------------------------------------------

        start = end - CHUNK_OVERLAP

        chunk_number += 1


# ---------------------------------------------------------
# 5. Create data folder
# ---------------------------------------------------------

os.makedirs(
    "data",
    exist_ok=True
)


# ---------------------------------------------------------
# 6. Save chunks
# ---------------------------------------------------------

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        chunks,
        file,
        indent=4,
        ensure_ascii=False
    )


# ---------------------------------------------------------
# 7. Finished
# ---------------------------------------------------------

print()
print("======================================")
print("CHUNKING COMPLETED")
print("======================================")

print(
    "Documents:",
    len(documents)
)

print(
    "Chunks created:",
    len(chunks)
)

print(
    "Output saved to:",
    OUTPUT_FILE
)
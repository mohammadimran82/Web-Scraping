import subprocess
import sys


# =========================================================
# Run one Python script
# =========================================================

def run_step(script_name, *arguments):

    print("\n")
    print("=" * 60)
    print(f"RUNNING: {script_name}")
    print("=" * 60)

    command = [
        sys.executable,
        script_name
    ]

    command.extend(arguments)

    result = subprocess.run(command)

    if result.returncode != 0:

        print("\n")
        print(f"ERROR: {script_name} failed.")

        sys.exit(1)


# =========================================================
# Ask for website URL
# =========================================================

website_url = input(
    "Enter website URL: "
).strip()


if not website_url:

    print("\nERROR: Website URL cannot be empty.")

    sys.exit(1)


# =========================================================
# Start pipeline
# =========================================================

print("\n")
print("=" * 60)
print("STARTING RAG PIPELINE")
print("=" * 60)


# =========================================================
# 1. Scrape website
# =========================================================

run_step(
    "scraper.py",
    website_url
)


# =========================================================
# 2. Prepare documents
# =========================================================

run_step(
    "prepare_documents.py"
)


# =========================================================
# 3. Create chunks
# =========================================================

run_step(
    "chunk_documents.py"
)


# =========================================================
# 4. Create embeddings
# =========================================================

run_step(
    "create_embeddings.py"
)


# =========================================================
# 5. Create vector database
# =========================================================

run_step(
    "create_vector_db.py"
)


# =========================================================
# Finished
# =========================================================

print("\n")
print("=" * 60)
print("RAG PIPELINE COMPLETED SUCCESSFULLY")
print("=" * 60)


print("\nYou can now run:")

print(
    "python ask_rag.py"
)
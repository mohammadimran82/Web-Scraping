import json
import os


# ============================================================
# SETTINGS
# ============================================================

INPUT_FILE = "data/scraped_data.json"
OUTPUT_FILE = "data/documents.json"


# ============================================================
# LOAD SCRAPED DATA
# ============================================================

print()
print("=" * 60)
print("LOADING SCRAPED DATA")
print("=" * 60)

with open(
    INPUT_FILE,
    "r",
    encoding="utf-8"
) as file:

    data = json.load(file)


# ============================================================
# GET PAGES
# ============================================================

pages = data.get(
    "pages",
    []
)

print()
print(
    "Pages found:",
    len(pages)
)


# ============================================================
# CREATE DOCUMENTS
# ============================================================

documents = []

for index, page in enumerate(pages):

    print()
    print(
        f"Processing page {index + 1}/{len(pages)}"
    )

    # --------------------------------------------------------
    # Make sure page itself is a dictionary
    # --------------------------------------------------------

    if not isinstance(page, dict):

        print(
            "Skipping invalid page:"
        )

        print(
            page
        )

        continue

    # --------------------------------------------------------
    # Get title
    # --------------------------------------------------------

    title = page.get(
        "title",
        ""
    )

    # --------------------------------------------------------
    # Get URL
    # --------------------------------------------------------

    url = page.get(
        "url",
        ""
    )

    # --------------------------------------------------------
    # Get content
    # --------------------------------------------------------

    content = page.get(
        "content",
        ""
    )

    # --------------------------------------------------------
    # Make sure content is a string
    # --------------------------------------------------------

    if isinstance(content, list):

        content = "\n".join(
            str(item)
            for item in content
        )

    elif not isinstance(content, str):

        content = str(content)

    # --------------------------------------------------------
    # Clean content
    # --------------------------------------------------------

    content = content.strip()

    # --------------------------------------------------------
    # Skip empty pages
    # --------------------------------------------------------

    if not content:

        print(
            "Skipping empty page."
        )

        continue

    # --------------------------------------------------------
    # Create document
    # --------------------------------------------------------

    document = {
        "text": content,

        "metadata": {
            "title": str(title),
            "url": str(url)
        }
    }

    documents.append(
        document
    )


# ============================================================
# SAVE DOCUMENTS
# ============================================================

os.makedirs(
    "data",
    exist_ok=True
)

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        documents,
        file,
        indent=2,
        ensure_ascii=False
    )


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 60)
print("DOCUMENT PREPARATION COMPLETED")
print("=" * 60)

print()

print(
    "Pages found:",
    len(pages)
)

print(
    "Documents created:",
    len(documents)
)

print()

print(
    "Output file:"
)

print(
    OUTPUT_FILE
)

print()

print(
    "prepare_documents.py completed successfully."
)
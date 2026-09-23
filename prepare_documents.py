import json
import os


# ============================================================
# FILE PATHS
# ============================================================

INPUT_FILE = "data/scraped_data.json"
OUTPUT_FILE = "data/documents.json"


# ============================================================
# LOAD SCRAPED DATA
# ============================================================

with open(
    INPUT_FILE,
    "r",
    encoding="utf-8"
) as f:

    scraped_data = json.load(f)


# ============================================================
# PREPARE DOCUMENTS
# ============================================================

documents = []


for page in scraped_data["pages"]:

    title = page.get(
        "title",
        ""
    )

    url = page.get(
        "url",
        ""
    )

    content_items = page.get(
        "content",
        []
    )

    text_parts = []


    # ========================================================
    # PROCESS EACH CONTENT ITEM
    # ========================================================

    for item in content_items:

        item_type = item.get(
            "type",
            ""
        )

        item_text = item.get(
            "text",
            ""
        )


        # ----------------------------------------------------
        # HEADING
        # ----------------------------------------------------

        if item_type == "heading":

            if item_text:
                text_parts.append(
                    f"\n{item_text}\n"
                )


        # ----------------------------------------------------
        # PARAGRAPH
        # ----------------------------------------------------

        elif item_type == "paragraph":

            if item_text:
                text_parts.append(
                    item_text
                )


        # ----------------------------------------------------
        # CODE
        # ----------------------------------------------------

        elif item_type == "code":

            if item_text:
                text_parts.append(
                    f"\nCODE:\n{item_text}\n"
                )


        # ----------------------------------------------------
        # LIST
        # ----------------------------------------------------

        elif item_type == "list":

            if item_text:
                text_parts.append(
                    f"- {item_text}"
                )


        # ----------------------------------------------------
        # TABLE
        # ----------------------------------------------------

        elif item_type == "table":

            if item_text:
                text_parts.append(
                    f"\nTABLE:\n{item_text}\n"
                )


        # ----------------------------------------------------
        # UNKNOWN TYPE
        # ----------------------------------------------------

        else:

            if item_text:
                text_parts.append(
                    item_text
                )


    # ========================================================
    # COMBINE PAGE CONTENT
    # ========================================================

    page_text = "\n".join(
        text_parts
    ).strip()


    # ========================================================
    # SAVE DOCUMENT
    # ========================================================

    if page_text:

        documents.append(
            {
                "text": page_text,

                "metadata": {
                    "title": title,
                    "url": url
                }
            }
        )


# ============================================================
# CREATE DATA DIRECTORY
# ============================================================

os.makedirs(
    "data",
    exist_ok=True
)


# ============================================================
# SAVE DOCUMENTS
# ============================================================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        documents,
        f,
        indent=2,
        ensure_ascii=False
    )


# ============================================================
# OUTPUT
# ============================================================

print(
    "======================================"
)

print(
    "DOCUMENT PREPARATION COMPLETED"
)

print(
    "======================================"
)

print(
    f"Pages scraped: {len(scraped_data['pages'])}"
)

print(
    f"Documents created: {len(documents)}"
)

print(
    f"JSON saved to: {OUTPUT_FILE}"
)
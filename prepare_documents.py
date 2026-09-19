import json
import os


# ---------------------------------------------------------
# 1. Input and output files
# ---------------------------------------------------------

INPUT_FILE = "data/scraped_data.json"
OUTPUT_FILE = "data/documents.json"


# ---------------------------------------------------------
# 2. Load scraped JSON
# ---------------------------------------------------------

with open(
    INPUT_FILE,
    "r",
    encoding="utf-8"
) as file:

    scraped_data = json.load(file)


# ---------------------------------------------------------
# 3. Create empty document list
# ---------------------------------------------------------

documents = []


# ---------------------------------------------------------
# 4. Process every scraped page
# ---------------------------------------------------------

for page in scraped_data["pages"]:

    page_url = page["url"]
    page_title = page["title"]

    text_parts = []


    # -----------------------------------------------------
    # Process page content
    # -----------------------------------------------------

    for item in page["content"]:

        content_type = item["type"]


        # ---------------------------------------------
        # Heading
        # ---------------------------------------------

        if content_type == "heading":

            text_parts.append(
                item["text"]
            )


        # ---------------------------------------------
        # Paragraph
        # ---------------------------------------------

        elif content_type == "paragraph":

            text_parts.append(
                item["text"]
            )


        # ---------------------------------------------
        # Code
        # ---------------------------------------------

        elif content_type == "code":

            text_parts.append(
                item["text"]
            )


        # ---------------------------------------------
        # List
        # ---------------------------------------------

        elif content_type == "list":

            for list_item in item["items"]:

                text_parts.append(
                    "- " + list_item
                )


        # ---------------------------------------------
        # Table
        # ---------------------------------------------

        elif content_type == "table":

            for row in item["rows"]:

                text_parts.append(
                    " | ".join(row)
                )


    # -----------------------------------------------------
    # Combine all content
    # -----------------------------------------------------

    page_text = "\n\n".join(
        text_parts
    )


    # -----------------------------------------------------
    # Create document
    # -----------------------------------------------------

    document = {

        "text": page_text,

        "metadata": {

            "title": page_title,

            "url": page_url

        }

    }


    documents.append(
        document
    )


# ---------------------------------------------------------
# 5. Create data folder if needed
# ---------------------------------------------------------

os.makedirs(
    "data",
    exist_ok=True
)


# ---------------------------------------------------------
# 6. Save documents
# ---------------------------------------------------------

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        documents,
        file,
        indent=4,
        ensure_ascii=False
    )


# ---------------------------------------------------------
# 7. Finished
# ---------------------------------------------------------

print()
print("======================================")
print("DOCUMENT PREPARATION COMPLETED")
print("======================================")

print(
    "Documents created:",
    len(documents)
)

print(
    "Output saved to:",
    OUTPUT_FILE
)

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import os


# ==========================================
# SETTINGS
# ==========================================

MAX_PAGES = 10


# ==========================================
# ASK FOR START URL
# ==========================================

start_url = input("Enter website URL: ").strip()


# ==========================================
# FIND WEBSITE DOMAIN
# ==========================================

domain = urlparse(start_url).netloc


# ==========================================
# STORAGE
# ==========================================

visited_urls = set()
pages = []


# ==========================================
# SCRAPE ONE PAGE
# ==========================================

def scrape_page(url):

    try:

        print()
        print("Scraping:", url)

        response = requests.get(
            url,
            timeout=20
        )

        response.raise_for_status()

    except requests.RequestException as error:

        print("Failed:", error)

        return None


    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )


    # ======================================
    # PAGE TITLE
    # ======================================

    title = ""

    if soup.title:

        title = soup.title.get_text(
            " ",
            strip=True
        )


    # ======================================
    # CONTENT
    # ======================================

    content = []


    # --------------------------------------
    # Find important HTML elements
    # --------------------------------------

    elements = soup.find_all(
        [
            "h1",
            "h2",
            "h3",
            "h4",
            "p",
            "table"
        ]
    )


    # ======================================
    # PROCESS ELEMENTS IN PAGE ORDER
    # ======================================

    for element in elements:


        # ----------------------------------
        # HEADINGS
        # ----------------------------------

        if element.name in [
            "h1",
            "h2",
            "h3",
            "h4"
        ]:

            text = element.get_text(
                " ",
                strip=True
            )

            if text:

                content.append({

                    "type": "heading",

                    "level": int(
                        element.name[1]
                    ),

                    "text": text

                })


        # ----------------------------------
        # PARAGRAPHS
        # ----------------------------------

        elif element.name == "p":

            text = element.get_text(
                " ",
                strip=True
            )

            if text:

                content.append({

                    "type": "paragraph",

                    "text": text

                })


        # ----------------------------------
        # TABLES
        # ----------------------------------

        elif element.name == "table":

            rows = []


            for row in element.find_all("tr"):

                cells = row.find_all(
                    ["th", "td"]
                )

                row_data = []


                for cell in cells:

                    cell_text = cell.get_text(
                        " ",
                        strip=True
                    )

                    row_data.append(
                        cell_text
                    )


                if row_data:

                    rows.append(
                        row_data
                    )


            if rows:

                content.append({

                    "type": "table",

                    "rows": rows

                })


    # ======================================
    # EXTRACT LINKS
    # ======================================

    links = []


    for link in soup.find_all("a"):

        href = link.get("href")

        text = link.get_text(
            " ",
            strip=True
        )


        if not href:

            continue


        absolute_url = urljoin(
            url,
            href
        )


        if absolute_url.startswith(
            ("http://", "https://")
        ):

            links.append({

                "text": text,

                "url": absolute_url

            })


    # ======================================
    # RETURN PAGE
    # ======================================

    return {

        "url": url,

        "title": title,

        "content": content,

        "links": links

    }


# ==========================================
# CRAWLER
# ==========================================

urls_to_visit = [start_url]


while (
    urls_to_visit
    and len(visited_urls) < MAX_PAGES
):

    current_url = urls_to_visit.pop(0)


    # --------------------------------------
    # Skip already visited URLs
    # --------------------------------------

    if current_url in visited_urls:

        continue


    visited_urls.add(
        current_url
    )


    # --------------------------------------
    # Scrape page
    # --------------------------------------

    page_data = scrape_page(
        current_url
    )


    if page_data is None:

        continue


    pages.append(
        page_data
    )


    # ======================================
    # ADD NEW LINKS
    # ======================================

    for link in page_data["links"]:

        next_url = link["url"]


        next_domain = urlparse(
            next_url
        ).netloc


        # Only same website

        if next_domain != domain:

            continue


        if next_url in visited_urls:

            continue


        if next_url in urls_to_visit:

            continue


        urls_to_visit.append(
            next_url
        )


# ==========================================
# FINAL DATASET
# ==========================================

output = {

    "start_url": start_url,

    "pages_scraped": len(pages),

    "pages": pages

}


# ==========================================
# SAVE
# ==========================================

os.makedirs(
    "data",
    exist_ok=True
)


with open(
    "data/scraped_data.json",
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        output,
        file,
        indent=4,
        ensure_ascii=False
    )


# ==========================================
# RESULT
# ==========================================

print()
print("======================================")
print("CRAWLING COMPLETED")
print("======================================")

print(
    "Pages scraped:",
    len(pages)
)

print(
    "JSON saved to:",
    "data/scraped_data.json"
)
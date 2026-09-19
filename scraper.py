import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
import json
import os


# Maximum number of pages the crawler will scrape
MAX_PAGES = 10


# ---------------------------------------------------------
# 1. Normalize URL
# ---------------------------------------------------------
def normalize_url(url):
    # Remove #section fragments from URLs
    url, fragment = urldefrag(url)

    # Remove trailing /
    return url.rstrip("/")


# ---------------------------------------------------------
# 2. Check whether a URL should be crawled
# ---------------------------------------------------------
def should_crawl(url, start_domain, allowed_path):

    parsed = urlparse(url)

    # Only allow HTTP and HTTPS
    if parsed.scheme not in ["http", "https"]:
        return False

    # Only crawl the same domain
    if parsed.netloc != start_domain:
        return False

    # Only crawl inside the documentation path
    if not parsed.path.startswith(allowed_path):
        return False

    # File types that we don't want to scrape
    blocked_extensions = [
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".zip",
        ".css",
        ".js",
        ".mp4",
        ".mp3"
    ]

    path = parsed.path.lower()

    for extension in blocked_extensions:
        if path.endswith(extension):
            return False

    return True


# ---------------------------------------------------------
# 3. Scrape one webpage
# ---------------------------------------------------------
def scrape_page(url):

    try:

        print()
        print("Scraping:", url)

        response = requests.get(
            url,
            timeout=20,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        response.raise_for_status()

    except requests.RequestException as error:

        print("Failed:", error)

        return None


    # Convert HTML into BeautifulSoup object
    soup = BeautifulSoup(response.text, "html.parser")


    # -----------------------------------------------------
    # Page title
    # -----------------------------------------------------

    title = ""

    if soup.title:
        title = soup.title.get_text(" ", strip=True)


    # -----------------------------------------------------
    # Page content
    # -----------------------------------------------------

    content = []


    # Find important HTML elements
    elements = soup.find_all([
        "h1",
        "h2",
        "h3",
        "h4",
        "p",
        "table",
        "pre",
        "code",
        "ul",
        "ol"
    ])


    for element in elements:

        # ---------------------------------------------
        # Headings
        # ---------------------------------------------

        if element.name in ["h1", "h2", "h3", "h4"]:

            text = element.get_text(" ", strip=True)

            if text:

                content.append({
                    "type": "heading",
                    "level": int(element.name[1]),
                    "text": text
                })


        # ---------------------------------------------
        # Paragraphs
        # ---------------------------------------------

        elif element.name == "p":

            text = element.get_text(" ", strip=True)

            if text:

                content.append({
                    "type": "paragraph",
                    "text": text
                })
                
        # ---------------------------------------------
        # Code blocks
        # ---------------------------------------------

        elif element.name == "pre":

            text = element.get_text(
                "\n",
                strip=True
            )

            if text:

                content.append({
                    "type": "code",
                    "text": text
                })


        elif element.name == "code":

            # Skip code elements that are already
            # inside a <pre> block
            if element.parent.name == "pre":
                continue

            text = element.get_text(
                " ",
                strip=True
            )

            if text:

                content.append({
                    "type": "code",
                    "text": text
                })
                
                
                # ---------------------------------------------
        # Lists
        # ---------------------------------------------

        elif element.name in ["ul", "ol"]:

            items = []

            for item in element.find_all("li", recursive=False):

                text = item.get_text(
                    " ",
                    strip=True
                )

                if text:
                    items.append(text)

            if items:

                content.append({
                    "type": "list",
                    "items": items
                })


        # ---------------------------------------------
        # Tables
        # ---------------------------------------------

        elif element.name == "table":

            rows = []


            for row in element.find_all("tr"):

                cells = row.find_all(["th", "td"])

                row_data = []


                for cell in cells:

                    cell_text = cell.get_text(
                        " ",
                        strip=True
                    )

                    row_data.append(cell_text)


                if row_data:

                    rows.append(row_data)


            if rows:

                content.append({
                    "type": "table",
                    "rows": rows
                })


    # -----------------------------------------------------
    # Extract links
    # -----------------------------------------------------

    links = []


    for link in soup.find_all("a"):

        href = link.get("href")

        text = link.get_text(
            " ",
            strip=True
        )


        # Ignore empty links
        if not href:
            continue


        # Convert relative URL to absolute URL
        absolute_url = urljoin(
            url,
            href
        )


        # Only keep HTTP/HTTPS links
        if absolute_url.startswith(
            ("http://", "https://")
        ):

            absolute_url = normalize_url(
                absolute_url
            )


            links.append({
                "text": text,
                "url": absolute_url
            })


    # -----------------------------------------------------
    # Return scraped page
    # -----------------------------------------------------

    return {

        "url": url,

        "title": title,

        "content": content,

        "links": links

    }


# =========================================================
# MAIN PROGRAM
# =========================================================


# ---------------------------------------------------------
# 4. Ask user for URL
# ---------------------------------------------------------

start_url = input(
    "Enter website URL: "
).strip()


# Normalize starting URL
start_url = normalize_url(
    start_url
)


# ---------------------------------------------------------
# 5. Extract domain and allowed path
# ---------------------------------------------------------

parsed_start_url = urlparse(
    start_url
)


domain = parsed_start_url.netloc


# Example:
#
# https://seller.flipkart.com/api-docs/glossary.html
#
# allowed_path becomes:
#
# /api-docs/

allowed_path = (
    parsed_start_url.path
    .rsplit("/", 1)[0]
    + "/"
)


# ---------------------------------------------------------
# 6. Create crawler storage
# ---------------------------------------------------------

visited_urls = set()

pages = []

urls_to_visit = [
    start_url
]


# ---------------------------------------------------------
# 7. Start crawling
# ---------------------------------------------------------

while (
    urls_to_visit
    and len(visited_urls) < MAX_PAGES
):

    # Take first URL from queue
    current_url = urls_to_visit.pop(0)


    # Skip if already visited
    if current_url in visited_urls:
        continue


    # Mark URL as visited
    visited_urls.add(
        current_url
    )


    # Scrape page
    page_data = scrape_page(
        current_url
    )


    # If scraping failed
    if page_data is None:
        continue


    # Store page
    pages.append(
        page_data
    )


    # -----------------------------------------------------
    # Find links from current page
    # -----------------------------------------------------

    for link in page_data["links"]:

        next_url = normalize_url(
            link["url"]
        )


        # Check crawler rules
        if not should_crawl(
            next_url,
            domain,
            allowed_path
        ):
            continue


        # Skip already visited URLs
        if next_url in visited_urls:
            continue


        # Skip URLs already waiting in queue
        if next_url in urls_to_visit:
            continue


        # Add URL to queue
        urls_to_visit.append(
            next_url
        )


# ---------------------------------------------------------
# 8. Prepare final JSON
# ---------------------------------------------------------

output = {

    "start_url": start_url,

    "domain": domain,

    "allowed_path": allowed_path,

    "pages_scraped": len(pages),

    "pages": pages

}


# ---------------------------------------------------------
# 9. Create data folder
# ---------------------------------------------------------

os.makedirs(
    "data",
    exist_ok=True
)


# ---------------------------------------------------------
# 10. Save JSON
# ---------------------------------------------------------

output_file = (
    "data/scraped_data.json"
)


with open(
    output_file,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        output,
        file,
        indent=4,
        ensure_ascii=False
    )


# ---------------------------------------------------------
# 11. Finished
# ---------------------------------------------------------

print()

print(
    "======================================"
)

print(
    "CRAWLING COMPLETED"
)

print(
    "======================================"
)

print(
    "Pages scraped:",
    len(pages)
)

print(
    "JSON saved to:",
    output_file
)
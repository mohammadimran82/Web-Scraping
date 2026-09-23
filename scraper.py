import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
from collections import deque
import json
import os
import time


# ============================================================
# SETTINGS
# ============================================================

OUTPUT_FILE = "data/scraped_data.json"

# None = crawl all allowed pages
MAX_PAGES = None

# Delay between requests
REQUEST_DELAY = 0.2

# Browser-like headers
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/153.0.0.0 Safari/537.36"
    )
}


# ============================================================
# URL NORMALIZATION
# ============================================================

def normalize_url(url):
    """
    Clean and normalize a URL.

    Removes:
    - #fragments
    - unnecessary trailing slash
    """

    url = urldefrag(url)[0]

    parsed = urlparse(url)

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    path = parsed.path

    if not path:
        path = "/"

    # Remove trailing slash except for root
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    normalized = f"{scheme}://{netloc}{path}"

    if parsed.query:
        normalized += f"?{parsed.query}"

    return normalized


# ============================================================
# FLIPKART URL CONVERSION
# ============================================================

def convert_flipkart_url(url, start_domain):
    """
    Flipkart documentation has some links that point to paths
    outside /api-docs.

    Example:

        /FMSAPI.html

    becomes:

        /api-docs/FMSAPI.html
    """

    parsed = urlparse(url)

    # Only modify Flipkart URLs
    if parsed.netloc.lower() != start_domain.lower():
        return url

    path = parsed.path

    # Already inside /api-docs
    if path == "/api-docs" or path.startswith("/api-docs/"):
        return url

    flipkart_doc_paths = [
        "/FMPlatOverview.html",
        "/FMSAPI.html",
        "/errors.html",
        "/best_practices.html",
        "/listing-api-docs/",
        "/order-api-docs/",
        "/reports-api-docs/",
        "/changelog.html",
        "/FAQ.html",
        "/contact_tech.html",
        "/contact.html",
        "/api-tou.html",
    ]

    should_convert = False

    for doc_path in flipkart_doc_paths:

        if path == doc_path:
            should_convert = True
            break

        if path.startswith(doc_path):
            should_convert = True
            break

    if not should_convert:
        return url

    new_path = "/api-docs" + path

    converted_url = (
        f"{parsed.scheme}://"
        f"{parsed.netloc}"
        f"{new_path}"
    )

    if parsed.query:
        converted_url += f"?{parsed.query}"

    return converted_url


# ============================================================
# CHECK WHETHER URL SHOULD BE CRAWLED
# ============================================================

def should_crawl(url, start_domain):
    """
    Decide whether a URL is allowed to be crawled.
    """

    try:
        parsed = urlparse(url)
    except ValueError:
        return False

    # Only HTTP / HTTPS
    if parsed.scheme not in ["http", "https"]:
        return False

    # Same domain only
    if parsed.netloc.lower() != start_domain.lower():
        return False

    path = parsed.path.lower()

    # Only documentation pages
    if not (
        path == "/api-docs"
        or path.startswith("/api-docs/")
    ):
        return False

    # Ignore Sphinx source files
    if path.startswith("/api-docs/_sources/"):
        return False

    # Ignore files/assets
    blocked_extensions = [
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".webp",
        ".zip",
        ".css",
        ".js",
        ".mp4",
        ".mp3",
        ".woff",
        ".woff2",
        ".ttf",
        ".ico",
    ]

    for extension in blocked_extensions:

        if path.endswith(extension):
            return False

    return True


# ============================================================
# SCRAPE ONE PAGE
# ============================================================

def scrape_page(url):
    """
    Download and extract useful documentation content
    from one webpage.
    """

    print()
    print("-" * 70)
    print("Scraping:")
    print(url)
    print("-" * 70)

    # --------------------------------------------------------
    # DOWNLOAD PAGE
    # --------------------------------------------------------

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        print(
            "Status code:",
            response.status_code
        )

        response.raise_for_status()

    except requests.RequestException as error:

        print("Request failed:")
        print(error)

        return None

    # --------------------------------------------------------
    # PARSE HTML
    # --------------------------------------------------------

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    # --------------------------------------------------------
    # PAGE TITLE
    # --------------------------------------------------------

    if soup.title:

        title = soup.title.get_text(
            " ",
            strip=True
        )

    else:

        title = url

    # --------------------------------------------------------
    # FIND MAIN DOCUMENTATION CONTENT
    # --------------------------------------------------------

    main_content = (
        soup.find("main")
        or soup.find("article")
        or soup.find("div", class_="document")
        or soup.find("body")
    )

    if main_content is None:

        print(
            "No main content found."
        )

        return None

    # --------------------------------------------------------
    # REMOVE UNWANTED HTML
    # --------------------------------------------------------

    for element in main_content.find_all(
        [
            "script",
            "style",
            "noscript",
            "nav",
            "footer"
        ]
    ):

        element.decompose()

    # --------------------------------------------------------
    # EXTRACT CONTENT
    # --------------------------------------------------------

    content_parts = []

    # ========================================================
    # HEADINGS
    # ========================================================

    for heading in main_content.find_all(
        [
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6"
        ]
    ):

        text = heading.get_text(
            " ",
            strip=True
        )

        if text:

            content_parts.append(
                f"\n{text}\n"
            )

    # ========================================================
    # PARAGRAPHS
    # ========================================================

    for paragraph in main_content.find_all(
        "p"
    ):

        text = paragraph.get_text(
            " ",
            strip=True
        )

        if text:

            content_parts.append(
                text
            )

    # ========================================================
    # CODE BLOCKS
    # ========================================================

    for code in main_content.find_all(
        [
            "pre",
            "code"
        ]
    ):

        text = code.get_text(
            "\n",
            strip=True
        )

        if text:

            content_parts.append(
                f"\nCODE:\n{text}\n"
            )

    # ========================================================
    # LIST ITEMS
    # ========================================================

    for item in main_content.find_all(
        "li"
    ):

        text = item.get_text(
            " ",
            strip=True
        )

        if text:

            content_parts.append(
                f"- {text}"
            )

    # ========================================================
    # TABLES
    # ========================================================

    for table in main_content.find_all(
        "table"
    ):

        rows = []

        for row in table.find_all(
            "tr"
        ):

            cells = row.find_all(
                [
                    "th",
                    "td"
                ]
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
                    " | ".join(row_data)
                )

        if rows:

            content_parts.append(
                "\nTABLE:\n"
                + "\n".join(rows)
                + "\n"
            )

    # ========================================================
    # COMBINE CONTENT
    # ========================================================

    content = "\n".join(
        content_parts
    )

    # --------------------------------------------------------
    # CLEAN EXCESSIVE BLANK LINES
    # --------------------------------------------------------

    lines = content.splitlines()

    cleaned_lines = []

    previous_blank = False

    for line in lines:

        line = line.strip()

        if not line:

            if not previous_blank:

                cleaned_lines.append("")

            previous_blank = True

        else:

            cleaned_lines.append(
                line
            )

            previous_blank = False

    content = "\n".join(
        cleaned_lines
    ).strip()

    # ========================================================
    # EXTRACT LINKS
    # ========================================================

    links = []

    for anchor in main_content.find_all(
        "a",
        href=True
    ):

        href = anchor.get(
            "href"
        )

        if not href:
            continue

        href = href.strip()

        # ----------------------------------------------------
        # Ignore placeholder links
        # ----------------------------------------------------

        if "your-website" in href.lower():
            continue

        # ----------------------------------------------------
        # Ignore JavaScript links
        # ----------------------------------------------------

        if href.lower().startswith(
            "javascript:"
        ):
            continue

        # ----------------------------------------------------
        # Ignore email links
        # ----------------------------------------------------

        if href.lower().startswith(
            "mailto:"
        ):
            continue

        # ----------------------------------------------------
        # Ignore telephone links
        # ----------------------------------------------------

        if href.lower().startswith(
            "tel:"
        ):
            continue

        # ----------------------------------------------------
        # Convert relative URL to absolute URL
        # ----------------------------------------------------

        try:

            absolute_url = urljoin(
                url,
                href
            )

            absolute_url = normalize_url(
                absolute_url
            )

        except ValueError:

            print(
                "Skipping invalid link:",
                href
            )

            continue

        # ----------------------------------------------------
        # Store link
        # ----------------------------------------------------

        links.append(
            absolute_url
        )

    # ========================================================
    # REMOVE DUPLICATE LINKS
    # ========================================================

    unique_links = []

    seen_links = set()

    for link in links:

        if link not in seen_links:

            seen_links.add(
                link
            )

            unique_links.append(
                link
            )

    # ========================================================
    # PRINT PAGE INFORMATION
    # ========================================================

    print(
        "Content length:",
        len(content)
    )

    print(
        "Links found:",
        len(unique_links)
    )

    # ========================================================
    # RETURN PAGE
    # ========================================================

    return {
        "title": title,
        "url": url,
        "content": content,
        "links": unique_links
    }


# ============================================================
# CRAWL WEBSITE
# ============================================================

def crawl_website(start_url):

    # --------------------------------------------------------
    # Normalize starting URL
    # --------------------------------------------------------

    start_url = normalize_url(
        start_url
    )

    parsed_start = urlparse(
        start_url
    )

    start_domain = parsed_start.netloc

    # --------------------------------------------------------
    # Validate starting URL
    # --------------------------------------------------------

    if not (
        parsed_start.path == "/api-docs"
        or parsed_start.path.startswith(
            "/api-docs/"
        )
    ):

        print()
        print("=" * 70)
        print("ERROR")
        print("=" * 70)

        print(
            "This scraper currently expects a Flipkart"
        )

        print(
            "documentation URL inside /api-docs."
        )

        print()

        print(
            "Example:"
        )

        print(
            "https://seller.flipkart.com/api-docs"
        )

        print()

        return

    # ========================================================
    # CREATE QUEUE
    # ========================================================

    queue = deque()

    queue.append(
        start_url
    )

    # ========================================================
    # VISITED URLS
    # ========================================================

    visited = set()

    # ========================================================
    # SCRAPED PAGES
    # ========================================================

    pages = []

    # ========================================================
    # START CRAWLER
    # ========================================================

    print()
    print("=" * 70)
    print("STARTING WEBSITE CRAWLER")
    print("=" * 70)

    print()

    print(
        "Starting URL:"
    )

    print(
        start_url
    )

    print()

    print(
        "Domain:"
    )

    print(
        start_domain
    )

    print()

    print(
        "Documentation path:"
    )

    print(
        "/api-docs"
    )

    print()

    # ========================================================
    # BREADTH-FIRST SEARCH CRAWLER
    # ========================================================

    while queue:

        # ----------------------------------------------------
        # Check page limit
        # ----------------------------------------------------

        if (
            MAX_PAGES is not None
            and len(pages) >= MAX_PAGES
        ):

            print()
            print(
                "Maximum page limit reached."
            )

            break

        # ----------------------------------------------------
        # Get next URL
        # ----------------------------------------------------

        current_url = queue.popleft()

        # ----------------------------------------------------
        # Skip already visited
        # ----------------------------------------------------

        if current_url in visited:

            continue

        visited.add(
            current_url
        )

        # ----------------------------------------------------
        # Convert Flipkart URL
        # ----------------------------------------------------

        current_url = convert_flipkart_url(
            current_url,
            start_domain
        )

        current_url = normalize_url(
            current_url
        )

        # ----------------------------------------------------
        # Check whether URL can be crawled
        # ----------------------------------------------------

        if not should_crawl(
            current_url,
            start_domain
        ):

            continue

        # ----------------------------------------------------
        # Scrape page
        # ----------------------------------------------------

        page = scrape_page(
            current_url
        )

        # ----------------------------------------------------
        # If page failed, continue
        # ----------------------------------------------------

        if page is None:

            continue

        # ----------------------------------------------------
        # Validate final URL
        # ----------------------------------------------------

        final_url = normalize_url(
            page["url"]
        )

        final_url = convert_flipkart_url(
            final_url,
            start_domain
        )

        if not should_crawl(
            final_url,
            start_domain
        ):

            print(
                "Skipping final URL:"
            )

            print(
                final_url
            )

            continue

        # ----------------------------------------------------
        # Save page
        # ----------------------------------------------------

        pages.append(
            page
        )

        print()

        print(
            "Pages scraped:",
            len(pages)
        )

        # ====================================================
        # ADD DISCOVERED LINKS TO QUEUE
        # ====================================================

        for link in page["links"]:

            link = convert_flipkart_url(
                link,
                start_domain
            )

            link = normalize_url(
                link
            )

            if should_crawl(
                link,
                start_domain
            ):

                if link not in visited:

                    if link not in queue:

                        queue.append(
                            link
                        )

        # ----------------------------------------------------
        # Delay before next request
        # ----------------------------------------------------

        time.sleep(
            REQUEST_DELAY
        )

    # ========================================================
    # SAVE SCRAPED DATA
    # ========================================================

    print()
    print("=" * 70)
    print("SAVING SCRAPED DATA")
    print("=" * 70)

    os.makedirs(
        "data",
        exist_ok=True
    )

    data = {
        "start_url": start_url,
        "domain": start_domain,
        "pages_scraped": len(pages),
        "pages": pages
    }

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False
        )

    # ========================================================
    # COMPLETION
    # ========================================================

    print()
    print("=" * 70)
    print("SCRAPING COMPLETED")
    print("=" * 70)

    print()

    print(
        "Starting URL:",
        start_url
    )

    print(
        "Domain:",
        start_domain
    )

    print(
        "Pages scraped:",
        len(pages)
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
        "Crawler finished successfully."
    )


# ============================================================
# MAIN PROGRAM
# ============================================================

if __name__ == "__main__":

    import sys

    # --------------------------------------------------------
    # URL supplied by run_pipeline.py
    #
    # Example:
    #
    # python scraper.py https://seller.flipkart.com/api-docs
    # --------------------------------------------------------

    if len(sys.argv) > 1:

        start_url = sys.argv[1].strip()

    # --------------------------------------------------------
    # Direct execution
    #
    # Example:
    #
    # python scraper.py
    # --------------------------------------------------------

    else:

        start_url = input(
            "Enter website URL: "
        ).strip()

    # --------------------------------------------------------
    # Check empty URL
    # --------------------------------------------------------

    if not start_url:

        print()

        print(
            "ERROR: Website URL cannot be empty."
        )

        sys.exit(1)

    # --------------------------------------------------------
    # Display URL information
    # --------------------------------------------------------

    print()

    print(
        f"Starting URL: {start_url}"
    )

    parsed = urlparse(
        start_url
    )

    print(
        f"Domain: {parsed.netloc}"
    )

    print(
        "Documentation path: /api-docs"
    )

    # --------------------------------------------------------
    # Start crawler
    # --------------------------------------------------------

    crawl_website(
        start_url
    )
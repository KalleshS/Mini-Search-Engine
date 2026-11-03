
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlsplit, urlunsplit
import ipaddress
import re


# ==========================================
# STEP 1: URL VALIDATION
# ==========================================

def is_valid_url(url):

    if not isinstance(url, str) or not url:
        return False

    if len(url) > 2048:
        return False

    if any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in url):
        return False

    if "\\" in url:
        return False

    try:
        parsed = urlsplit(url)

        # Allow only HTTP and HTTPS
        if parsed.scheme.lower() not in ("http", "https"):
            return False

        hostname = parsed.hostname

        if not hostname:
            return False

        # Reject username and password
        if parsed.username is not None or parsed.password is not None:
            return False

        # Validate port
        port = parsed.port

        if port is not None and not (1 <= port <= 65535):
            return False

        # Validate IP address
        try:
            ip = ipaddress.ip_address(hostname)

            if not ip.is_global:
                return False

        except ValueError:

            # Validate domain name
            hostname = hostname.rstrip(".")

            if (
                not hostname
                or len(hostname) > 253
                or hostname.lower() == "localhost"
                or hostname.lower().endswith((".localhost", ".local"))
            ):
                return False

            try:
                hostname = hostname.encode("idna").decode("ascii")
            except UnicodeError:
                return False

            labels = hostname.split(".")

            for label in labels:

                if (
                    not label
                    or len(label) > 63
                    or not re.fullmatch(
                        r"[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?",
                        label
                    )
                ):
                    return False

        return True

    except (ValueError, UnicodeError):
        return False


# ==========================================
# STEP 2: URL NORMALIZATION
# ==========================================

def normalize_url(url):

    if not is_valid_url(url):
        return None

    try:
        parsed = urlsplit(url)

        scheme = parsed.scheme.lower()
        hostname = parsed.hostname.lower().rstrip(".")

        port = parsed.port

        # Remove default ports
        if (scheme == "http" and port == 80) or \
           (scheme == "https" and port == 443):
            port = None

        # Handle IPv6 addresses
        if ":" in hostname:
            hostname = f"[{hostname}]"

        # Reconstruct domain
        netloc = hostname

        if port is not None:
            netloc += f":{port}"

        # Add trailing slash if path is empty
        path = parsed.path if parsed.path else "/"

        # Remove URL fragments
        normalized = urlunsplit((
            scheme,
            netloc,
            path,
            parsed.query,
            ""
        ))

        return normalized

    except (ValueError, UnicodeError):
        return None


# ==========================================
# STEP 3: FETCH WEBPAGE
# ==========================================

def fetch_page(url):

    # Validate initial URL
    if not is_valid_url(url):
        raise ValueError(f"Invalid URL: {url}")

    # Normalize initial URL
    url = normalize_url(url)

    # Send HTTP GET request
    response = httpx.get(
        url,
        timeout=15,
        follow_redirects=True,
        headers={"User-Agent": "MiniSearchEngine/1.0"}
    )

    # Check HTTP errors
    response.raise_for_status()

    # Parse HTML
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract page title
    title_tag = soup.find("title")

    title = (
        title_tag.get_text(strip=True)
        if title_tag else "No title"
    )
    # Extract readable webpage text
    page_text = soup.get_text(separator=" ", strip=True)

    # ======================================
    # STEP 4: EXTRACT UNIQUE LINKS
    # ======================================

    links = []

    # Store unique links from current webpage
    seen_links = set()

    for tag in soup.find_all("a", href=True):

        # Convert relative URL to absolute URL
        absolute_url = urljoin(url, tag["href"])

        # Normalize extracted URL
        normalized_url = normalize_url(absolute_url)

        # Add only valid and unique URLs
        if normalized_url and normalized_url not in seen_links:

            seen_links.add(normalized_url)
            links.append(normalized_url)

    return title, links, page_text

# ==========================================
# TESTING
# ==========================================

if __name__ == "__main__":

    # TEST 1: URL NORMALIZATION

    print("\n--- URL NORMALIZATION TEST ---")

    test_urls = [
        "HTTPS://GOOGLE.COM",
        "https://google.com:443/",
        "https://google.com/#about",
        "http://example.com"
    ]

    for url in test_urls:
        print(url, "->", normalize_url(url))


    # TEST 2: DUPLICATE PREVENTION

    print("\n--- DUPLICATE URL TEST ---")

    urls = [
        "https://google.com",
        "https://google.com/",
        "https://GOOGLE.COM",
        "https://google.com/#about"
    ]

    unique_urls = set()

    for url in urls:

        normalized = normalize_url(url)

        if normalized:
            unique_urls.add(normalized)

    print("Original URLs:", len(urls))
    print("Unique URLs:", len(unique_urls))
    print("Unique URL list:", unique_urls)


    # TEST 3: INVALID URL

    print("\n--- URL VALIDATION TEST ---")

    invalid_test_urls = [
        "invalid-url",
        "ftp://example.com",
        "https://",
        "https://localhost"
    ]

    for url in invalid_test_urls:
        print(url, "->", is_valid_url(url))


    # TEST 4: ACTUAL WEB CRAWLING

    print("\n--- WEB CRAWLER TEST ---")

    url = "https://www.python.org"

    try:

        title, links = fetch_page(url)

        print("Page title:", title)
        print("Total unique links:", len(links))

        print("\nFirst 10 unique links:")

        for link in links[:10]:
            print(link)

    except (httpx.HTTPError, ValueError) as error:
        print("Error:", error)

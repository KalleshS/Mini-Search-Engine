import threading
import httpx
import socket
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlsplit, urlunsplit
import ipaddress
import re
import urllib.robotparser
# Robots.txt cache
robots_cache = {}

# Lock protects the shared cache
robots_lock = threading.Lock()


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
# STEP 5: DNS AND IP VALIDATION
# ==========================================

def is_public_host(url):

    try:
        parsed = urlsplit(url)

        hostname = parsed.hostname
        port = parsed.port or (
            443 if parsed.scheme == "https" else 80
        )

        # Resolve hostname into IP addresses
        addresses = socket.getaddrinfo(
            hostname,
            port,
            type=socket.SOCK_STREAM
        )

        # Check every resolved IP
        for address in addresses:

            ip = ipaddress.ip_address(address[4][0])

            if not ip.is_global:
                return False

        return bool(addresses)

    except (ValueError, socket.gaierror, OSError):
        return False
# ==========================================
# STEP 3: FETCH WEBPAGE
# ==========================================

def fetch_page(url):

    if not is_valid_url(url):
        raise ValueError(f"Invalid URL: {url}")

    url = normalize_url(url)

    max_retries = 3
    max_redirects = 5

    redirect_count = 0

    while True:

        # NETWORK RETRY LOOP
        for attempt in range(max_retries):

            try:
                if not is_public_host(url):
                    raise ValueError(
                    "Private or unsafe IP address detected"
                    )
                response = httpx.get(
                    url,
                    timeout=15,
                    follow_redirects=False,
                    headers={"User-Agent": "MiniSearchEngine/1.0"}
                )

                break

            except (httpx.TimeoutException, httpx.NetworkError) as error:

                print(f"Attempt {attempt + 1} failed: {error}")

                if attempt == max_retries - 1:
                    raise

        # REDIRECT HANDLING
        if response.is_redirect:

            if redirect_count >= max_redirects:
                raise ValueError("Too many redirects")

            redirect_url = response.headers.get("location")

            if not redirect_url:
                raise ValueError("Redirect location missing")

            redirect_url = urljoin(url, redirect_url)

            if not is_valid_url(redirect_url):
                raise ValueError("Unsafe redirect URL")

            url = normalize_url(redirect_url)

            redirect_count += 1

            print(f"Following redirect {redirect_count}: {url}")

            continue

        # CHECK HTTP ERRORS
        response.raise_for_status()

        # PARSE HTML
        soup = BeautifulSoup(response.text, "html.parser")

        title_tag = soup.find("title")

        title = (
            title_tag.get_text(strip=True)
            if title_tag else "No title"
        )

        page_text = soup.get_text(
            separator=" ",
            strip=True
        )

        # EXTRACT UNIQUE LINKS
        links = []
        seen_links = set()

        for tag in soup.find_all("a", href=True):

            absolute_url = urljoin(url, tag["href"])

            normalized_url = normalize_url(absolute_url)

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

        title, links,page_text = fetch_page(url)

        print("Page title:", title)
        print("Total unique links:", len(links))
        print("Total text characters:",len(page_text))

        print("\nFirst 10 unique links:")

        for link in links[:10]:
            print(link)

    except (httpx.HTTPError, ValueError) as error:
        print("Error:", error)
    print("\n--- REDIRECT TEST ---")

url = "https://httpbin.org/redirect/2"

try:
    title, links, page_text = fetch_page(url)

    print("Redirect successful!")
    print("Final page title:", title)

except (httpx.HTTPError, ValueError) as error:
    print("Redirect test failed:", error)
print("\n--- DNS AND IP TEST ---")

print(
    "Google:",
    is_public_host("https://www.google.com")
)

print(
    "Localhost:",
    is_public_host("http://127.0.0.1")
)

print(
    "Private IP:",
    is_public_host("http://192.168.1.1")
)


def can_fetch(url, user_agent="MiniSearchEngine/1.0"):

    parsed_url = urlsplit(url)

    robots_url = (
        f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
    )

    # Use website origin as the cache key
    domain = f"{parsed_url.scheme}://{parsed_url.netloc}"

    try:
        with robots_lock:

            # Check whether rules are already cached
            if domain not in robots_cache:

                robot_parser = urllib.robotparser.RobotFileParser()

                robot_parser.set_url(robots_url)
                robot_parser.read()

                # Store rules in cache
                robots_cache[domain] = robot_parser

                print(f"Robots.txt downloaded: {domain}")

            else:
                robot_parser = robots_cache[domain]

        # Check permission using cached rules
        allowed = robot_parser.can_fetch(user_agent, url)

        print(
            f"Robots check: {url} -> "
            f"{'Allowed' if allowed else 'Blocked'}"
        )

        return allowed

    except Exception as error:
        print("Robots.txt check failed:", error)
        return False
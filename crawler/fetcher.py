
import threading
import httpx
import socket
import ipaddress
import re
import time
import urllib.robotparser

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlsplit, urlunsplit


# ==========================================
# ROBOTS.TXT CACHE
# ==========================================

robots_cache = {}
robots_lock = threading.Lock()


# ==========================================
# URL VALIDATION
# ==========================================

def is_valid_url(url):

    if not isinstance(url, str) or not url:
        return False

    if len(url) > 2048:
        return False

    if re.search(r"[\s\x00-\x1f\x7f]", url):
        return False

    if "\\" in url:
        return False

    try:
        parsed = urlsplit(url)

        if parsed.scheme.lower() not in {"http", "https"}:
            return False

        if not parsed.hostname:
            return False

        if parsed.username or parsed.password:
            return False

        port = parsed.port

        if port is not None and not (1 <= port <= 65535):
            return False

        hostname = parsed.hostname

        try:
            ip = ipaddress.ip_address(hostname)
            return ip.is_global
        except ValueError:
            pass

        hostname = hostname.encode("idna").decode("ascii")

        if hostname == "localhost" or hostname.endswith(
            (".localhost", ".local")
        ):
            return False

        if len(hostname) > 253:
            return False

        labels = hostname.split(".")

        for label in labels:
            if not re.fullmatch(
                r"[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?",
                label
            ):
                return False

        return True

    except (ValueError, UnicodeError):
        return False


# ==========================================
# URL NORMALIZATION
# ==========================================

def normalize_url(url):

    if not is_valid_url(url):
        raise ValueError(f"Invalid URL: {url}")

    parsed = urlsplit(url)

    scheme = parsed.scheme.lower()
    hostname = parsed.hostname.lower()

    try:
        ip = ipaddress.ip_address(hostname)

        if ip.version == 6:
            hostname = f"[{hostname}]"

    except ValueError:
        pass

    port = parsed.port

    if port is not None:
        if not (
            (scheme == "http" and port == 80)
            or (scheme == "https" and port == 443)
        ):
            hostname = f"{hostname}:{port}"

    path = parsed.path or "/"

    normalized = urlunsplit((
        scheme,
        hostname,
        path,
        parsed.query,
        ""
    ))

    return normalized


# ==========================================
# PUBLIC HOST CHECK
# ==========================================

def is_public_host(url):

    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == "https" else 80)

        addresses = socket.getaddrinfo(
            hostname,
            port,
            type=socket.SOCK_STREAM
        )

        if not addresses:
            return False

        for address in addresses:
            ip = ipaddress.ip_address(address[4][0])

            if not ip.is_global:
                return False

        return True

    except (socket.gaierror, ValueError, OSError):
        return False


# ==========================================
# ROBOTS.TXT CHECK
# ==========================================

def can_fetch(url, user_agent="MiniSearchEngine/1.0"):

    try:
        parsed = urlsplit(url)

        robots_url = urlunsplit((
            parsed.scheme,
            parsed.netloc,
            "/robots.txt",
            "",
            ""
        ))

        domain = f"{parsed.scheme}://{parsed.netloc}"

        with robots_lock:
            parser = robots_cache.get(domain)

        if parser is None:

            if not is_public_host(robots_url):
                return False

            response = httpx.get(
                robots_url,
                timeout=10,
                follow_redirects=False,
                headers={"User-Agent": user_agent}
            )

            if response.status_code >= 400:
                return False

            parser = urllib.robotparser.RobotFileParser()
            parser.set_url(robots_url)
            parser.parse(response.text.splitlines())

            with robots_lock:
                robots_cache[domain] = parser

        return parser.can_fetch(user_agent, url)

    except Exception as error:
        print(f"Robots.txt check failed: {error}")
        return False


# ==========================================
# FETCH PAGE
# ==========================================

def fetch_page(url):

    if not is_valid_url(url):
        raise ValueError(f"Invalid URL: {url}")

    url = normalize_url(url)

    max_retries = 3
    max_redirects = 5
    redirect_count = 0

    while True:

        if not is_valid_url(url):
            raise ValueError(f"Invalid redirect URL: {url}")

        url = normalize_url(url)

        if not is_public_host(url):
            raise ValueError("Private or unsafe IP address detected")

        response = None

        # NETWORK RETRY LOOP
        for attempt in range(max_retries):

            try:
                response = httpx.get(
                    url,
                    timeout=15,
                    follow_redirects=False,
                    headers={
                        "User-Agent": "MiniSearchEngine/1.0"
                    }
                )

                if response.status_code in {
                    429, 500, 502, 503, 504
                }:
                    response.raise_for_status()

                break

            except (
                httpx.TimeoutException,
                httpx.NetworkError,
                httpx.HTTPStatusError
            ) as error:

                print(
                    f"Attempt {attempt + 1} failed: {error}"
                )

                if attempt == max_retries - 1:
                    raise

                time.sleep(2 ** attempt)

        # REDIRECT HANDLING
        if response.is_redirect:

            if redirect_count >= max_redirects:
                raise ValueError("Too many redirects")

            redirect_url = response.headers.get("location")

            if not redirect_url:
                raise ValueError("Redirect location missing")

            url = urljoin(url, redirect_url)

            if not is_valid_url(url):
                raise ValueError("Invalid redirect URL")

            redirect_count += 1
            continue

        # CHECK FINAL HTTP STATUS
        response.raise_for_status()

        # HTML PARSING
        soup = BeautifulSoup(response.text, "html.parser")

        # EXTRACT TITLE
        title = (
            soup.title.get_text(strip=True)
            if soup.title
            else "No Title"
        )

        # REMOVE UNNECESSARY ELEMENTS
        for element in soup([
            "script",
            "style",
            "noscript",
            "header",
            "footer"
        ]):
            element.decompose()

        # EXTRACT PAGE TEXT
        page_text = soup.get_text(
            separator=" ",
            strip=True
        )

        # EXTRACT LINKS
        links = set()

        for anchor in soup.find_all("a", href=True):

            absolute_url = urljoin(
                url,
                anchor["href"]
            )

            if is_valid_url(absolute_url):

                normalized_link = normalize_url(
                    absolute_url
                )

                links.add(normalized_link)

        return title, list(links), page_text

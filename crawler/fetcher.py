
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def fetch_page(url):
    # Step 1: Send an HTTP GET request
    response = httpx.get(
        url,
        timeout=15,
        follow_redirects=True,
        headers={"User-Agent": "MiniSearchEngine/1.0"}
    )

    # Step 2: Check for HTTP errors
    response.raise_for_status()

    # Step 3: Parse the HTML
    soup = BeautifulSoup(response.text, "html.parser")

    # Step 4: Extract the page title
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else "No title"

    # Step 5: Extract webpage links
    links = []

    for tag in soup.find_all("a", href=True):
        absolute_url = urljoin(url, tag["href"])

        if absolute_url.startswith(("http://", "https://")):
            links.append(absolute_url)

    # Step 6: Return extracted information
    return title, links


if __name__ == "__main__":
    url = "https://www.python.org"

    try:
        title, links = fetch_page(url)

        print("Page title:", title)
        print("Total links:", len(links))

        print("\nFirst 10 links:")
        for link in links[:10]:
            print(link)

    except httpx.HTTPError as error:
        print("HTTP error:", error)

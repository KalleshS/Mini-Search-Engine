
import time
from urllib.parse import urlsplit
import queue
import threading
import httpx

from crawler.fetcher import fetch_page, normalize_url, can_fetch


# ==========================================
# MULTITHREADED WEB CRAWLER
# ==========================================

def crawl(seed_url, max_workers=4, max_pages=10):

    url_queue = queue.Queue()

    discovered = set()
    visited = set()
    results = {}
    errors = {}

    lock = threading.Lock()

    # Domain-level request throttling
    last_request_time = {}
    domain_locks = {}
    domain_locks_guard = threading.Lock()

    # ======================================
    # DOMAIN THROTTLING
    # ======================================

    def wait_for_domain(url, delay=1.0):

        domain = urlsplit(url).netloc.lower()

        with domain_locks_guard:

            if domain not in domain_locks:
                domain_locks[domain] = threading.Lock()

            domain_lock = domain_locks[domain]

        with domain_lock:

            current_time = time.monotonic()

            previous_time = last_request_time.get(domain, 0)

            elapsed = current_time - previous_time

            if elapsed < delay:
                time.sleep(delay - elapsed)

            last_request_time[domain] = time.monotonic()

    # ======================================
    # ADD URL TO QUEUE
    # ======================================

    def add_url(url):

        try:
            normalized = normalize_url(url)

        except ValueError:
            return

        with lock:

            if normalized in discovered:
                return

            if len(discovered) >= max_pages:
                return

            discovered.add(normalized)

        url_queue.put(normalized)

    add_url(seed_url)

    # ======================================
    # WORKER FUNCTION
    # ======================================

    def worker():

        while True:

            url = url_queue.get()

            try:

                # Stop signal
                if url is None:
                    return

                with lock:

                    if len(visited) >= max_pages:
                        continue

                    if url in visited:
                        continue

                    visited.add(url)

                try:

                    print(
                        f"[{threading.current_thread().name}] "
                        f"Crawling: {url}"
                    )

                    # Check robots.txt
                    if not can_fetch(url):
                        print(f"Blocked by robots.txt: {url}")
                        continue

                    # Apply domain throttling
                    wait_for_domain(url)

                    # Fetch webpage
                    title, links, page_text = fetch_page(url)

                    # Save result
                    with lock:

                        results[url] = {
                            "title": title,
                            "links": links,
                            "content": page_text
                        }

                    print(f"Successfully crawled: {url}")

                    # Add discovered links
                    for link in links:
                        add_url(link)

                except (httpx.HTTPError, ValueError) as error:

                    with lock:
                        errors[url] = str(error)

                    print(f"Failed: {url} -> {error}")

                except Exception as error:

                    with lock:
                        errors[url] = str(error)

                    print(f"Unexpected error: {url} -> {error}")

            finally:

                # Mark task as completed
                url_queue.task_done()

    # ======================================
    # CREATE WORKER THREADS
    # ======================================

    threads = []

    for i in range(max_workers):

        thread = threading.Thread(
            target=worker,
            name=f"Worker-{i + 1}"
        )

        threads.append(thread)
        thread.start()

    # Wait for crawling tasks
    url_queue.join()

    # Stop worker threads
    for _ in range(max_workers):
        url_queue.put(None)

    url_queue.join()

    for thread in threads:
        thread.join()

    # ======================================
    # CRAWLING SUMMARY
    # ======================================

    print("\n========== CRAWLING SUMMARY ==========")

    print("Total discovered URLs:", len(discovered))
    print("Total attempted URLs:", len(visited))
    print("Successfully crawled:", len(results))
    print("Failed URLs:", len(errors))

    print("\n========== CRAWLED WEBPAGES ==========")

    for url, data in results.items():

        print("\nURL:", url)
        print("Title:", data["title"])
        print("Links found:", len(data["links"]))

    return results


# ==========================================
# MAIN PROGRAM
# ==========================================

if __name__ == "__main__":

    seed_url = "https://www.python.org"

    crawl(
        seed_url=seed_url,
        max_workers=4,
        max_pages=10
    )

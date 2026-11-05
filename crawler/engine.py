
import queue
import threading
import httpx

from crawler.fetcher import fetch_page, normalize_url,can_fetch


# ==========================================
# MULTITHREADED WEB CRAWLER
# ==========================================

def crawl(seed_url, max_workers=4, max_pages=10):

    # Queue containing URLs waiting to be crawled
    url_queue = queue.Queue()

    # Shared data structures
    discovered = set()
    visited = set()
    results = {}
    errors = {}

    # Lock protects shared data structures
    lock = threading.Lock()

    # ======================================
    # ADD URL TO QUEUE
    # ======================================

    def add_url(url):

        normalized = normalize_url(url)

        if not normalized:
            return

        with lock:

            # Avoid duplicate URLs
            if normalized in discovered:
                return

            # Limit total discovered URLs
            if len(discovered) >= max_pages:
                return

            discovered.add(normalized)

        url_queue.put(normalized)

    # Add starting URL
    add_url(seed_url)

    # ======================================
    # WORKER FUNCTION
    # ======================================

    def worker():

        while True:

            # Get URL from queue
            url = url_queue.get()

            # Stop signal
            if url is None:
                url_queue.task_done()
                break

            with lock:
                visited.add(url)

            try:

                print(
                    f"[{threading.current_thread().name}] "
                    f"Crawling: {url}"
                )
                if not can_fetch(url):
                    print(f"Blocked by robots.txt:{url}")
                    continue
                # Fetch webpage
                title, links, page_text = fetch_page(url)
                # Save result
                with lock:
                    results[url] = {
                        "title": title,
                        "links": links,
                        "content":page_text
                    }

                # Add discovered links to queue
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

                # Mark current task as completed
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

    # Wait until all crawling tasks are completed
    url_queue.join()

    # Send stop signals to workers
    for _ in range(max_workers):
        url_queue.put(None)

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    # ======================================
    # DISPLAY RESULTS
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

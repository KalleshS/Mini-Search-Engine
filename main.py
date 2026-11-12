
from crawler.engine import crawl
from crawler.indexer import build_index, search, display_results

from database.db import create_table, insert_page, get_all_pages

from crawler.index_cache import save_index, load_index


# ==========================================
# MINI SEARCH ENGINE
# ==========================================

if __name__ == "__main__":

    seed_url = "https://www.python.org"

    # ======================================
    # STEP 1: INITIALIZE DATABASE
    # ======================================

    print("\nInitializing SQLite Database...")

    create_table()

    # ======================================
    # STEP 2: LOAD STORED WEBPAGES
    # ======================================

    print("\nChecking SQLite Database...")

    stored_pages = get_all_pages()

    crawled_pages = {}

    for page in stored_pages:

        url = page[1]
        title = page[2]
        content = page[3]

        crawled_pages[url] = {
            "title": title,
            "content": content,
            "links": []
        }

    # ======================================
    # STEP 3: CRAWL IF DATABASE IS EMPTY
    # ======================================

    if not crawled_pages:

        print("\nNo saved webpages found.")
        print("\nStarting Web Crawler...\n")

        crawled_pages = crawl(
            seed_url=seed_url,
            max_workers=4,
            max_pages=10
        )

        print("\nSaving webpages to SQLite...")

        for url, data in crawled_pages.items():

            insert_page(
                url,
                data["title"],
                data["content"]
            )

    else:

        print("Loading previously stored webpages...")
        print("Total webpages loaded:", len(crawled_pages))

    # ======================================
    # STEP 4: REBUILD INDEX FUNCTION
    # ======================================

    def rebuild_index():

        global inverted_index
        global documents
        global document_frequency
        global total_documents

        print("\nBuilding Inverted Index...")

        (
            inverted_index,
            documents,
            document_frequency,
            total_documents
        ) = build_index(crawled_pages)

        # Save index to JSON cache
        save_index(
            inverted_index,
            documents,
            document_frequency,
            total_documents
        )

        print("Indexing completed!")
        print("Total indexed documents:", len(documents))
        print("Total unique words:", len(inverted_index))

    # ======================================
    # STEP 5: LOAD INDEX CACHE
    # ======================================

    print("\nChecking Search Index Cache...")

    cached_index = load_index()

    if cached_index is not None:

        (
            inverted_index,
            documents,
            document_frequency,
            total_documents
        ) = cached_index

        print("Search index loaded from cache!")

        print("Total indexed documents:", len(documents))
        print("Total unique words:", len(inverted_index))

    else:

        print("No valid search index cache found.")

        rebuild_index()

    # ======================================
    # STEP 6: SEARCH AND REFRESH LOOP
    # ======================================

    while True:

        query = input(
            "\nEnter search query (or type refresh / exit): "
        ).strip()

        # EXIT
        if query.lower() == "exit":

            print("Search engine closed.")
            break

        # REFRESH
        elif query.lower() == "refresh":

            print("\nRefreshing webpages...")

            new_pages = crawl(
                seed_url=seed_url,
                max_workers=4,
                max_pages=10
            )

            print("\nUpdating SQLite Database...")

            for url, data in new_pages.items():

                insert_page(
                    url,
                    data["title"],
                    data["content"]
                )

            # Reload all webpages from database
            crawled_pages.clear()

            for page in get_all_pages():

                url = page[1]
                title = page[2]
                content = page[3]

                crawled_pages[url] = {
                    "title": title,
                    "content": content,
                    "links": []
                }

            print("Database updated!")
            print("Total webpages:", len(crawled_pages))

            # Rebuild and save updated index
            rebuild_index()

            print("\nRefresh completed!")

        # SEARCH
        else:

            results = search(
                query,
                inverted_index,
                documents,
                document_frequency,
                total_documents
            )

            display_results(results)

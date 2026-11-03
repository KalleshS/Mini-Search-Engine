
from crawler.engine import crawl
from crawler.indexer import build_index, search, display_results


# ==========================================
# MINI SEARCH ENGINE
# ==========================================

if __name__ == "__main__":

    seed_url = "https://www.python.org"

    # STEP 1: Crawl webpages
    print("\nStarting Web Crawler...\n")

    crawled_pages = crawl(
        seed_url=seed_url,
        max_workers=4,
        max_pages=10
    )

    # STEP 2: Build inverted index
    print("\nBuilding Inverted Index...")

    inverted_index, documents, document_frequency, total_documents = build_index(crawled_pages)

    print("Indexing completed!")

    print("Total indexed documents:", len(documents))
    print("Total unique words:", len(inverted_index))

    # STEP 3: Search
    while True:

        query = input(
            "\nEnter search query (or type exit): "
        )

        if query.lower() == "exit":
            print("Search engine closed.")
            break

        results = search(
    query,
    inverted_index,
    documents,
    document_frequency,
    total_documents
)

        display_results(results)

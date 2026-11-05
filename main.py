
from crawler.engine import crawl
from crawler.indexer import build_index, search, display_results
from database.db import create_table, insert_page, get_all_pages

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
        # STEP 1.5: Store crawled webpages in SQLite
    print("\nSaving webpages to SQLite Database...")

    create_table()

    for url, data in crawled_pages.items():

        insert_page(
            url,
            data["title"],
            data["content"]
        )

    print("All crawled webpages saved successfully!")
        # Verify stored webpages
    print("\nVerifying SQLite Database...")

    stored_pages = get_all_pages()

    print("Total webpages stored:", len(stored_pages))

    for page in stored_pages:
        print("\nURL:", page[1])
        print("Title:", page[2])

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

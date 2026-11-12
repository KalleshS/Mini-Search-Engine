
from crawler.storage import create_table, save_pages, load_pages

create_table()

sample_pages = {
    "https://example.com": {
        "title": "Example Website",
        "content": "This is a sample webpage.",
        "links": []
    }
}

save_pages(sample_pages)

pages = load_pages()

print("\nLoaded pages:")

for url, data in pages.items():
    print("URL:", url)
    print("Title:", data["title"])
    print("Content:", data["content"])

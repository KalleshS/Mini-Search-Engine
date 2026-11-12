
import json
import os


CACHE_FILE = "search_index.json"


# ==========================================
# SAVE SEARCH INDEX
# ==========================================

def save_index(
    inverted_index,
    documents,
    document_frequency,
    total_documents
):

    index_data = {
        "inverted_index": inverted_index,
        "documents": documents,
        "document_frequency": document_frequency,
        "total_documents": total_documents
    }

    with open(CACHE_FILE, "w", encoding="utf-8") as file:

        json.dump(
            index_data,
            file,
            ensure_ascii=False
        )

    print("Search index saved successfully!")


# ==========================================
# LOAD SEARCH INDEX
# ==========================================

def load_index():

    if not os.path.exists(CACHE_FILE):
        return None

    try:

        with open(CACHE_FILE, "r", encoding="utf-8") as file:
            index_data = json.load(file)

        return (
            index_data["inverted_index"],
            index_data["documents"],
            index_data["document_frequency"],
            index_data["total_documents"]
        )

    except (json.JSONDecodeError, KeyError, OSError, TypeError):

        print("Invalid index cache. Rebuilding index...")
        return None

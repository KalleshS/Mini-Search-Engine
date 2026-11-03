
import re
import math
from collections import defaultdict


# ==========================================
# STEP 1: STOP WORDS
# ==========================================

STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were",
    "in", "on", "at", "to", "for", "of", "and",
    "or", "but", "with", "by", "this", "that",
    "it", "as", "be", "from", "has", "have"
}


# ==========================================
# STEP 2: TOKENIZATION
# ==========================================

def tokenize(text):

    # Convert text to lowercase
    text = text.lower()

    # Extract words
    words = re.findall(r"\b[a-z0-9]+\b", text)

    # Remove stop words
    words = [
        word for word in words
        if word not in STOP_WORDS
    ]

    return words


# ==========================================
# STEP 3: BUILD INVERTED INDEX
# ==========================================

def build_index(crawled_pages):
    inverted_index = defaultdict(dict)
    documents = {}
    document_frequency = defaultdict(int)

    total_documents = len(crawled_pages)

    for url, data in crawled_pages.items():
        title = data["title"]
        content = data["content"]
        words = tokenize(title + " " + content)

        documents[url] = {
            "title": title,
            "url": url,
            "content":content,
            "total_words":len(words)  
        }

        

        for word in words:
            inverted_index[word][url] = (
                inverted_index[word].get(url, 0) + 1
            )

        # Count each word only once per document
        for word in set(words):
            document_frequency[word] += 1

    return inverted_index, documents, document_frequency, total_documents

# ==========================================
# STEP 4: SEARCH ENGINE
# ==========================================
def generate_snippet(content, query_words, context_chars=60):

    content_lower = content.lower()

    for word in query_words:

        position = content_lower.find(word.lower())

        if position != -1:

            start = max(0, position - context_chars)
            end = min(
                len(content),
                position + len(word) + context_chars
            )

            snippet = content[start:end].strip()

            if start > 0:
                snippet = "..." + snippet

            if end < len(content):
                snippet += "..."

            return snippet

    return content[:120] + "..."

def search(query, inverted_index, documents,
           document_frequency, total_documents):

    query_words = tokenize(query)
    scores = defaultdict(float)

    for word in query_words:

        if word in inverted_index:

            # Calculate IDF
            df = document_frequency[word]

            idf = math.log(
                (total_documents + 1) / (df + 1)
            ) + 1

            # Calculate TF-IDF for each webpage
            for url, frequency in inverted_index[word].items():
                total_words = documents[url]["total_words"]



                tf = frequency / total_words

                tf_idf = tf * idf

                scores[url] += tf_idf

    ranked_results = sorted(
        scores.items(),
        key=lambda item: item[1],
        reverse=True
    )

    results = []

    for url, score in ranked_results:
        results.append({
            "title": documents[url]["title"],
            "url": url,
            "score": round(score, 4),
            "snippet":generate_snippet(documents[url]["content"],query_words)
        })

    return results

# ==========================================
# STEP 5: DISPLAY SEARCH RESULTS
# ==========================================

def display_results(results):

    if not results:
        print("\nNo matching webpages found.")
        return

    print("\n========== SEARCH RESULTS ==========")

    for i, result in enumerate(results, start=1):

        print(f"\nResult {i}")
        print("Title:", result["title"])
        print("URL:", result["url"])
        print("Relevance score:", result["score"])
        print("Snippet:",result["snippet"])

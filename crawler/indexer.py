
import re
import math

from collections import defaultdict
from colorama import Fore, Style, init

# Initialize terminal colors
init(autoreset=True)


# ==========================================
# STOP WORDS
# ==========================================

STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were",
    "in", "on", "at", "to", "for", "of", "and",
    "or", "but", "with", "by", "this", "that",
    "it", "as", "be", "from", "has", "have"
}


# ==========================================
# TOKENIZATION
# ==========================================

def tokenize(text):

    text = text.lower()

    words = re.findall(r"\b[a-z0-9]+\b", text)

    words = [
        word for word in words
        if word not in STOP_WORDS
    ]

    return words


# ==========================================
# BUILD INVERTED INDEX
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
            "content": content,
            "total_words": len(words)
        }

        for word in words:

            inverted_index[word][url] = (
                inverted_index[word].get(url, 0) + 1
            )

        for word in set(words):
            document_frequency[word] += 1

    return (
        inverted_index,
        documents,
        document_frequency,
        total_documents
    )


# ==========================================
# GENERATE SEARCH SNIPPET
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


# ==========================================
# EXACT PHRASE MATCHING
# ==========================================

def phrase_matches(text, phrase):

    text_words = re.findall(
        r"\b[a-z0-9]+\b",
        text.lower()
    )

    phrase_words = re.findall(
        r"\b[a-z0-9]+\b",
        phrase.lower()
    )

    if not phrase_words:
        return False

    phrase_length = len(phrase_words)

    for i in range(
        len(text_words) - phrase_length + 1
    ):

        if text_words[i:i + phrase_length] == phrase_words:
            return True

    return False


# ==========================================
# SEARCH FUNCTION
# ==========================================

def search(query, inverted_index, documents,
           document_frequency, total_documents):

    query = query.strip()

    # Detect exact phrase search
    is_phrase_search = (
        len(query) >= 2
        and query.startswith('"')
        and query.endswith('"')
    )

    # Detect AND search
    is_and_search = (
        not is_phrase_search
        and re.search(r"\s+AND\s+", query, re.IGNORECASE)
    )

    # Detect explicit OR search
    is_or_search = (
        not is_phrase_search
        and not is_and_search
        and re.search(r"\s+OR\s+", query, re.IGNORECASE)
    )

    if is_phrase_search:

        phrase = query[1:-1].strip()
        query_words = tokenize(phrase)

    elif is_and_search:

        phrase = None

        parts = re.split(
            r"\s+AND\s+",
            query,
            flags=re.IGNORECASE
        )

        query_words = tokenize(" ".join(parts))

    elif is_or_search:

        phrase = None

        parts = re.split(
            r"\s+OR\s+",
            query,
            flags=re.IGNORECASE
        )

        query_words = tokenize(" ".join(parts))

    else:

        phrase = None
        query_words = tokenize(query)

    query_words = list(dict.fromkeys(query_words))

    scores = defaultdict(float)

    # Find matching documents
    if is_and_search:

        if not query_words:
            return []

        matching_urls = set(
            inverted_index.get(query_words[0], {})
        )

        for word in query_words[1:]:

            matching_urls &= set(
                inverted_index.get(word, {})
            )

    else:

        matching_urls = set()

        for word in query_words:

            matching_urls.update(
                inverted_index.get(word, {}).keys()
            )

    # Calculate relevance scores
    for url in matching_urls:

        document = documents[url]

        # Exact phrase filtering
        if is_phrase_search:

            combined_text = (
                document["title"] + " " +
                document["content"]
            )

            if not phrase_matches(combined_text, phrase):
                continue

        for word in query_words:

            if word not in inverted_index:
                continue

            if url not in inverted_index[word]:
                continue

            frequency = inverted_index[word][url]
            df = document_frequency[word]

            idf = math.log(
                (total_documents + 1) / (df + 1)
            ) + 1

            total_words = document["total_words"]

            if total_words == 0:
                continue

            tf = frequency / total_words

            scores[url] += tf * idf

        # Handle phrases containing only stop words
        if is_phrase_search and not query_words:
            scores[url] = 1.0

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
            "snippet": generate_snippet(
                documents[url]["content"],
                query_words if query_words else [phrase]
            )
        })

    return results


# ==========================================
# HIGHLIGHT SEARCH TERMS
# ==========================================

def highlight_text(text, query):

    clean_query = re.sub(
        r"\b(AND|OR)\b",
        " ",
        query,
        flags=re.IGNORECASE
    ).replace('"', ' ')

    words = tokenize(clean_query)

    if not words:
        return text

    pattern = re.compile(
        r"\b(" +
        "|".join(re.escape(word) for word in words) +
        r")\b",
        re.IGNORECASE
    )

    return pattern.sub(
        lambda match:
            Fore.YELLOW + match.group(0) + Style.RESET_ALL,
        text
    )


# ==========================================
# DISPLAY SEARCH RESULTS
# ==========================================

def display_results(results, query=""):

    if not results:

        print("\nNo matching webpages found.")
        return

    print("\n========== SEARCH RESULTS ==========")

    for i, result in enumerate(results, start=1):

        print(f"\nResult {i}")

        title = highlight_text(
            result["title"],
            query
        )

        snippet = highlight_text(
            result["snippet"],
            query
        )

        print("Title:", title)
        print("URL:", result["url"])
        print("Relevance score:", result["score"])
        print("Snippet:", snippet)

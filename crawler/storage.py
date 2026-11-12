
import sqlite3


DATABASE_NAME = "search_engine.db"


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_connection():

    conn = sqlite3.connect(DATABASE_NAME)

    return conn


# ==========================================
# CREATE DATABASE TABLE
# ==========================================

def create_table():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS webpages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            title TEXT,
            content TEXT
        )
    """)

    conn.commit()
    conn.close()

    print("Database table created successfully!")


# ==========================================
# SAVE CRAWLED PAGES
# ==========================================

def save_pages(crawled_pages):

    conn = get_connection()
    cursor = conn.cursor()

    for url, data in crawled_pages.items():

        cursor.execute("""
            INSERT INTO webpages (url, title, content)
            VALUES (?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                title = excluded.title,
                content = excluded.content
        """, (
            url,
            data["title"],
            data["content"]
        ))

    conn.commit()
    conn.close()

    print("Webpages saved successfully!")


# ==========================================
# LOAD CRAWLED PAGES
# ==========================================

def load_pages():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT url, title, content
        FROM webpages
    """)

    rows = cursor.fetchall()

    conn.close()

    crawled_pages = {}

    for url, title, content in rows:

        crawled_pages[url] = {
            "title": title,
            "content": content,
            "links": []
        }

    return crawled_pages

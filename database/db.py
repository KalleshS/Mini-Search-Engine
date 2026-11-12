
import sqlite3


DATABASE_NAME = "search_engine.db"


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_connection():

    connection = sqlite3.connect(DATABASE_NAME)

    return connection


# ==========================================
# CREATE TABLE
# ==========================================

def create_table():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS webpages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            title TEXT,
            content TEXT,
            crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()

    print("Database table ready!")


# ==========================================
# INSERT OR UPDATE WEBPAGE
# ==========================================

def insert_page(url, title, content):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO webpages (url, title, content)
        VALUES (?, ?, ?)
        ON CONFLICT(url) DO UPDATE SET
            title = excluded.title,
            content = excluded.content,
            crawled_at = CURRENT_TIMESTAMP
    """, (url, title, content))

    connection.commit()
    connection.close()


# ==========================================
# GET ALL WEBPAGES
# ==========================================

def get_all_pages():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM webpages
    """)

    pages = cursor.fetchall()

    connection.close()

    return pages


# ==========================================
# DELETE ALL WEBPAGES
# ==========================================

def delete_all_pages():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM webpages")

    connection.commit()
    connection.close()

    print("All webpages deleted!")


# ==========================================
# MAIN TEST
# ==========================================

if __name__ == "__main__":

    create_table()

    insert_page(
        "https://www.python.org/",
        "Python",
        "Python is a programming language."
    )

    pages = get_all_pages()

    print("\nStored Webpages:")

    for page in pages:
        print(page)

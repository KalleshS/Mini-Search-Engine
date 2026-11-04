import sqlite3


def get_connection():
    connection = sqlite3.connect("search_engine.db")
    return connection


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


def insert_page(url, title, content):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO webpages (url, title, content)
        VALUES (?, ?, ?)
    """, (url, title, content))

    connection.commit()
    connection.close()

    print("Webpage insertion attempted!")


def get_all_pages():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM webpages")
    pages = cursor.fetchall()

    connection.close()
    return pages


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

# Mini Search Engine

A simple search engine built using Python. It crawls web pages, extracts content, creates an inverted index, and retrieves relevant results for user queries.

## Project Overview

The goal of this project is to understand how search engines work internally by implementing a web crawler, an inverted index, and a ranking algorithm.

## Features

- [ ] Web crawling
- [ ] Extract webpage titles and links
- [ ] Store webpage data using SQLite
- [ ] Build an inverted index
- [ ] Implement BM25 ranking
- [ ] Search API using FastAPI
- [ ] Display search results through a simple web interface

## Tech Stack

- **Language:** Python
- **Web Requests:** HTTPX
- **HTML Parsing:** BeautifulSoup
- **Database:** SQLite
- **Backend API:** FastAPI
- **Frontend:** HTML, CSS, JavaScript
- **Testing:** Pytest
- **Version Control:** Git and GitHub

## Project Structure

```text
mini-search-engine/
│
├── crawler/
├── index/
├── api/
├── tests/
├── data/
├── requirements.txt
└── README.md
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/acc1/mini-search-engine.git
cd mini-search-engine
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the environment

Windows PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

## Usage

Instructions for running the crawler and search engine will be added as development progresses.

## Current Progress

- [x] Initial project setup
- [x] Basic webpage fetching
- [x] Extract webpage title and links
- [ ] Advanced crawler implementation
- [ ] Inverted index
- [ ] BM25 ranking
- [ ] Search API and frontend

## Future Improvements

- Improve search relevance
- Add more efficient crawling
- Add automated testing
- Deploy the application

## Author

Kallesh S

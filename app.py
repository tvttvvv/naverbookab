from flask import Flask, render_template, request, jsonify
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import urllib.parse
import time
import re

app = Flask(__name__)

playwright = sync_playwright().start()
browser = playwright.chromium.launch(
    headless=True,
    args=["--no-sandbox"]
)

def classify_naver_book(html):
    soup = BeautifulSoup(html, "html.parser")

    # 🔴 대표 카드 구조 먼저 차단
    page_text = soup.get_text(" ", strip=True)
    if re.search(r"판매처\s*\d+", page_text):
        return "B", 1

    # 🟢 실제 도서 리스트 영역 찾기
    book_list = soup.select("ul.list_book > li")

    real_count = len(book_list)

    if real_count <= 2:
        return "A", real_count
    else:
        return "B", real_count


def crawl(keyword):
    start_time = time.time()

    url = f"https://search.naver.com/search.naver?where=book&query={urllib.parse.quote(keyword)}"

    page = browser.new_page()
    page.goto(url, wait_until="networkidle")
    time.sleep(1.5)

    html = page.content()
    page.close()

    cls, count = classify_naver_book(html)

    end_time = time.time()

    return {
        "keyword": keyword,
        "class": cls,
        "count": count,
        "url": url,
        "time": round(end_time - start_time, 2)
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search", methods=["POST"])
def search():
    try:
        data = request.get_json(force=True)
        keyword = data.get("keyword")

        if not keyword:
            return jsonify({"error": "keyword missing"})

        result = crawl(keyword)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/health")
def health():
    return jsonify({"status": "naverbookab running"})

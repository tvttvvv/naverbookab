from flask import Flask, render_template, request, jsonify
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import urllib.parse
import time

app = Flask(__name__)

# Playwright 전역 실행
playwright = sync_playwright().start()
browser = playwright.chromium.launch(
    headless=True,
    args=["--no-sandbox"]
)

def classify_naver_book(html):
    soup = BeautifulSoup(html, "html.parser")

    # 네이버 도서 카드 개수
    cards = soup.select("li.bx")
    count = len(cards)

    # A는 최대 2개
    if count <= 2:
        return "A", count
    else:
        return "B", count


def crawl(keyword):
    url = f"https://search.naver.com/search.naver?where=book&query={urllib.parse.quote(keyword)}"

    page = browser.new_page()
    page.goto(url, wait_until="networkidle")
    time.sleep(1.5)
    html = page.content()
    page.close()

    cls, count = classify_naver_book(html)

    return {
        "keyword": keyword,
        "class": cls,
        "count": count,
        "url": url
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

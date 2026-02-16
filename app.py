from flask import Flask, render_template, request, jsonify
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import urllib.parse
import time

app = Flask(__name__)

# 🔥 전역 브라우저 유지
playwright = sync_playwright().start()
browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])

def classify_naver_book(html):
    soup = BeautifulSoup(html, 'html.parser')
    result_cards = soup.select("li.bx")
    count = len(result_cards)

    if count <= 2:
        return "A", count
    else:
        return "B", count


def crawl_naver_book(keyword):
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
        data = request.json
        keyword = data.get("keyword")
        result = crawl_naver_book(keyword)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/health")
def health():
    return jsonify({"status": "naverbookab running"})

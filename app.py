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
    full_text = soup.get_text(" ", strip=True)

    # 1️⃣ 대표 단일 상품형 감지
    if re.search(r"도서\s*판매처\s*\d+", full_text):
        return "B", 1

    # 2️⃣ 반복 제목 링크 세기 (안정적 기준)
    title_links = soup.find_all("a", href=re.compile(r"/search.naver\?where=book"))

    count = len(title_links)

    # 너무 많이 잡히는 경우 방지
    if count > 20:
        count = 20

    if count <= 2:
        return "A", count
    else:
        return "B", count


def crawl(keyword):
    start = time.time()

    url = f"https://search.naver.com/search.naver?where=book&query={urllib.parse.quote(keyword)}"

    page = browser.new_page()
    page.goto(url, wait_until="networkidle")
    time.sleep(1.2)

    html = page.content()
    page.close()

    cls, count = classify_naver_book(html)

    end = time.time()

    return {
        "keyword": keyword,
        "class": cls,
        "count": count,
        "url": url,
        "time": round(end - start, 2)
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

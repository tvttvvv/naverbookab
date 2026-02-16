from flask import Flask, render_template, request, jsonify
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import urllib.parse
import time

app = Flask(__name__)

# 🔥 핵심 분류 함수 (A ≤ 2 기준)
def classify_naver_book(html):
    soup = BeautifulSoup(html, 'html.parser')

    # 네이버 도서 검색 결과 카드 선택
    # 일반적으로 li.bx 구조 사용
    result_cards = soup.select("li.bx")

    count = len(result_cards)

    if count <= 2:
        return "A", count
    else:
        return "B", count


def crawl_naver_book(keyword):
    url = f"https://search.naver.com/search.naver?where=book&query={urllib.parse.quote(keyword)}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
        )
        page.goto(url, wait_until="networkidle")
        time.sleep(2)  # 과부하 방지
        html = page.content()
        browser.close()

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
    data = request.json
    keyword = data.get("keyword")
    result = crawl_naver_book(keyword)
    return jsonify(result)


@app.route("/health")
def health():
    return jsonify({"status": "naverbookab running"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

from flask import Flask, render_template, request
import requests
import os
import time
import urllib.parse
from difflib import SequenceMatcher

app = Flask(__name__)

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")


def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def classify_keyword(keyword):
    url = "https://openapi.naver.com/v1/search/book.json"

    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }

    params = {
        "query": keyword,
        "display": 20
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)

        if response.status_code != 200:
            return 0, "B"

        data = response.json()
        items = data.get("items", [])

        count = len(items)

        # 1차 필터: 개수 기준
        if count > 5:
            return count, "B"

        # 2차 필터: 제목 유사도 검사
        high_similarity_count = 0

        for item in items:
            title = item.get("title", "")
            clean_title = title.replace("<b>", "").replace("</b>", "")
            if similarity(keyword, clean_title) >= 0.8:
                high_similarity_count += 1

        if high_similarity_count == 1:
            return count, "A"
        else:
            return count, "B"

    except:
        return 0, "B"


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/search", methods=["POST"])
def search():
    keywords_raw = request.form.get("keywords", "")
    keywords = [k.strip() for k in keywords_raw.split("\n") if k.strip()]

    results = []
    start_time = time.time()

    for keyword in keywords[:100]:
        count, classification = classify_keyword(keyword)

        naver_link = (
            "https://search.naver.com/search.naver?where=book&query="
            + urllib.parse.quote(keyword)
        )

        results.append({
            "keyword": keyword,
            "count": count,
            "class": classification,
            "link": naver_link
        })

    total_time = round(time.time() - start_time, 2)

    return render_template(
        "index.html",
        results=results,
        total_time=total_time
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

from flask import Flask, render_template, request, jsonify
import requests
import os
import time

app = Flask(__name__)

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

def search_naver_book_api(keyword):
    start_time = time.time()

    url = "https://openapi.naver.com/v1/search/book.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }

    params = {
        "query": keyword,
        "display": 100  # 최대 100개
    }

    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    total = data.get("total", 0)

    # A는 2개 이하
    if total <= 2:
        classification = "A"
    else:
        classification = "B"

    elapsed = round(time.time() - start_time, 2)

    return {
        "keyword": keyword,
        "count": total,
        "class": classification,
        "time": elapsed,
        "url": f"https://search.naver.com/search.naver?where=book&query={keyword}"
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search", methods=["POST"])
def search():
    keywords = request.json.get("keywords", [])

    results = []

    for keyword in keywords:
        try:
            result = search_naver_book_api(keyword)
            results.append(result)
        except Exception as e:
            results.append({
                "keyword": keyword,
                "count": 0,
                "class": "ERROR",
                "time": 0,
                "url": ""
            })

    return jsonify(results)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

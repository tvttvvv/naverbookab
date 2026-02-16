import os
import time
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")


@app.route("/ping")
def ping():
    return "OK"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search", methods=["POST"])
def search():
    start_time = time.time()

    data = request.json
    keywords = data.get("keywords", [])

    results = []

    for keyword in keywords:
        keyword = keyword.strip()
        if not keyword:
            continue

        try:
            url = "https://openapi.naver.com/v1/search/book.json"

            headers = {
                "X-Naver-Client-Id": NAVER_CLIENT_ID,
                "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
            }

            params = {
                "query": keyword,
                "display": 100
            }

            response = requests.get(url, headers=headers, params=params, timeout=5)
            data = response.json()

            total = data.get("total", 0)

            classification = "A" if total <= 2 else "B"

            results.append({
                "keyword": keyword,
                "count": total,
                "class": classification,
                "link": f"https://search.naver.com/search.naver?where=book&query={keyword}"
            })

        except Exception as e:
            results.append({
                "keyword": keyword,
                "count": 0,
                "class": "ERROR",
                "link": "",
                "error": str(e)
            })

    elapsed_time = round(time.time() - start_time, 2)

    return jsonify({
        "results": results,
        "time": elapsed_time
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

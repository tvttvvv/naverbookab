from flask import Flask, render_template, request
import requests
import os
import time
import urllib.parse

app = Flask(__name__)

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

def search_book(keyword):
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
            return 0

        data = response.json()
        return len(data.get("items", []))

    except:
        return 0


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search", methods=["POST"])
def search():
    keywords = request.form["keywords"].split("\n")
    keywords = [k.strip() for k in keywords if k.strip()]

    results = []
    start_time = time.time()

    for keyword in keywords[:100]:
        count = search_book(keyword)

        classification = "A" if count <= 2 else "B"

        naver_link = f"https://search.naver.com/search.naver?where=book&query={urllib.parse.quote(keyword)}"

        results.append({
            "keyword": keyword,
            "count": count,
            "class": classification,
            "link": naver_link
        })

    total_time = round(time.time() - start_time, 2)

    return render_template("index.html", results=results, total_time=total_time)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

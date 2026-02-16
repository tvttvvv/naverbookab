import os
import time
import requests
from flask import Flask, request, render_template_string

app = Flask(__name__)

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

HTML = """
<!doctype html>
<title>naverbookab</title>
<h1>naverbookab</h1>

<form method="post">
<textarea name="keywords" rows="15" cols="50" placeholder="책 제목을 한 줄에 하나씩 입력"></textarea><br><br>
<button type="submit">일괄 분류</button>
</form>

{% if total_time %}
<h3>총 소요시간: {{ total_time }}초</h3>
{% endif %}

{% if results %}
<table border="1" cellpadding="5">
<tr>
<th>키워드</th>
<th>ISBN 종류 수</th>
<th>분류</th>
<th>네이버 링크</th>
</tr>
{% for r in results %}
<tr>
<td>{{ r.keyword }}</td>
<td>{{ r.count }}</td>
<td>{{ r.grade }}</td>
<td><a href="{{ r.link }}" target="_blank">열기</a></td>
</tr>
{% endfor %}
</table>
{% endif %}
"""

def normalize_isbn(isbn_raw):
    """
    네이버 API isbn 예시:
    '9788937460000 893746000X'
    → 13자리 ISBN만 추출
    """
    if not isbn_raw:
        return None

    parts = isbn_raw.split()
    for p in parts:
        if len(p) == 13 and p.isdigit():
            return p
    return None


def check_keyword(keyword):
    url = "https://openapi.naver.com/v1/search/book.json"

    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }

    params = {
        "query": keyword,
        "display": 100
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return 0, "B"

    items = data.get("items", [])

    isbn_set = set()

    for item in items:
        isbn = normalize_isbn(item.get("isbn"))
        if isbn:
            isbn_set.add(isbn)

    unique_count = len(isbn_set)

    # 분류 기준
    if unique_count <= 1:
        grade = "A"
    else:
        grade = "B"

    return unique_count, grade


@app.route("/", methods=["GET", "POST"])
def home():
    results = []
    total_time = None

    if request.method == "POST":
        start_time = time.time()

        keywords_text = request.form.get("keywords", "")
        keywords = [k.strip() for k in keywords_text.split("\n") if k.strip()]

        for keyword in keywords:
            count, grade = check_keyword(keyword)

            results.append({
                "keyword": keyword,
                "count": count,
                "grade": grade,
                "link": f"https://search.naver.com/search.naver?query={keyword}"
            })

        total_time = round(time.time() - start_time, 2)

    return render_template_string(HTML, results=results, total_time=total_time)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

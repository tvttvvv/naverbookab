from flask import Flask, render_template_string, request
import requests
import os
import time

app = Flask(__name__)

NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET")

HTML = """
<!doctype html>
<title>naverbookab</title>
<h1>naverbookab</h1>

<form method="post">
<textarea name="keywords" rows="10" cols="50" placeholder="책 제목을 한 줄에 하나씩 입력"></textarea><br><br>
<button type="submit">일괄 분류</button>
</form>

{% if results %}
<p><b>총 소요시간:</b> {{ total_time }}초</p>
<table border="1" cellpadding="5">
<tr>
<th>키워드</th>
<th>판매처 없는 개수</th>
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

def check_keyword(keyword):
    url = "https://openapi.naver.com/v1/search/book.json"

    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }

    params = {
        "query": keyword,
        "display": 50
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return 0, "B"

    items = data.get("items", [])
    no_seller_count = 0

    for item in items:
        price = item.get("price")

        # 판매처 없는 상품
        if not price or price == "0":
            no_seller_count += 1

    # 기준: 판매처 없는 상품이 1개 이하 → A
    if no_seller_count <= 1:
        grade = "A"
    else:
        grade = "B"

    return no_seller_count, grade


@app.route("/", methods=["GET", "POST"])
def home():
    results = []
    total_time = 0

    if request.method == "POST":
        start = time.time()

        keywords = request.form.get("keywords", "").splitlines()

        for keyword in keywords:
            keyword = keyword.strip()
            if not keyword:
                continue

            count, grade = check_keyword(keyword)

            results.append({
                "keyword": keyword,
                "count": count,
                "grade": grade,
                "link": f"https://search.naver.com/search.naver?query={keyword}"
            })

        total_time = round(time.time() - start, 2)

    return render_template_string(HTML, results=results, total_time=total_time)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

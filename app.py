from flask import Flask, render_template_string, request
import requests
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)

NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET")

MAX_WORKERS = 25
MAX_DISPLAY = 50


HTML = """
<!doctype html>
<html>
<head>
<title>naverbookab</title>
<script>
function updateCount() {
    let text = document.getElementById("keywords").value;
    let lines = text.split("\\n").filter(l => l.trim() !== "");
    document.getElementById("countDisplay").innerText = "총 입력 건수: " + lines.length + "건";
}
</script>
</head>

<body>
<h1>naverbookab</h1>

<form method="post">
<textarea id="keywords" name="keywords" rows="15" cols="70"
oninput="updateCount()"
placeholder="책 제목을 한 줄에 하나씩 입력 (최대 1000개)"></textarea>
<br>
<p id="countDisplay">총 입력 건수: 0건</p>

<select name="sort_option">
<option value="original">원본순</option>
<option value="best">A 우선 정렬</option>
<option value="worst">B 우선 정렬</option>
</select>

<br><br>
<button type="submit">일괄 분류</button>
</form>

{% if results %}
<p><b>총 소요시간:</b> {{ total_time }}초</p>
<table border="1" cellpadding="5">
<tr>
<th>키워드</th>
<th>판매처 개수</th>
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
</body>
</html>
"""


def check_keyword(keyword):
    url = "https://openapi.naver.com/v1/search/book.json"

    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }

    params = {
        "query": keyword,
        "display": MAX_DISPLAY
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        data = response.json()
    except:
        return {
            "keyword": keyword,
            "count": 999,
            "grade": "B",
            "link": f"https://search.naver.com/search.naver?query={keyword}"
        }

    items = data.get("items", [])
    seller_count = 0

    for item in items:
        price = item.get("price")

        if price and price != "0":
            seller_count += 1

    grade = "A" if seller_count == 0 else "B"

    return {
        "keyword": keyword,
        "count": seller_count,
        "grade": grade,
        "link": f"https://search.naver.com/search.naver?query={keyword}"
    }


@app.route("/", methods=["GET", "POST"])
def home():
    results = []
    total_time = 0

    if request.method == "POST":
        start = time.time()

        keywords = request.form.get("keywords", "").splitlines()
        keywords = [k.strip() for k in keywords if k.strip()][:1000]

        sort_option = request.form.get("sort_option", "original")

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(check_keyword, kw) for kw in keywords]

            for future in as_completed(futures):
                results.append(future.result())

        total_time = round(time.time() - start, 2)

        keyword_order = {k: i for i, k in enumerate(keywords)}

        if sort_option == "original":
            results.sort(key=lambda x: keyword_order.get(x["keyword"], 0))

        elif sort_option == "best":
            results.sort(key=lambda x: (x["grade"] != "A", x["count"]))

        elif sort_option == "worst":
            results.sort(key=lambda x: (x["grade"] != "B", -x["count"]))

    return render_template_string(HTML, results=results, total_time=total_time)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

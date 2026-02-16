from flask import Flask, render_template_string, request
import requests
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)

NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET")

MAX_WORKERS = 10
TIMEOUT = 2

HTML = """
<!doctype html>
<title>naverbookab</title>
<h1>naverbookab</h1>

<form method="post">
<textarea name="keywords" rows="15" cols="60"
placeholder="책 제목 한 줄에 하나씩 입력"
oninput="updateCount(this)"></textarea><br>
<p>입력 개수: <span id="count">0</span></p>

<select name="sort_option">
<option value="original">원본순</option>
<option value="a_top">A 위로</option>
<option value="a_bottom">A 아래로</option>
</select>

<br><br>
<button type="submit">일괄 분류</button>
</form>

{% if results %}
<p><b>총 입력:</b> {{ total_count }}개</p>
<p><b>총 소요시간:</b> {{ total_time }}초</p>

<table border="1" cellpadding="5">
<tr>
<th>키워드</th>
<th>판매중 여부</th>
<th>분류</th>
<th>링크</th>
</tr>

{% for r in results %}
<tr {% if r.grade == 'A' %}style="background-color:#eaffea;"{% endif %}>
<td>{{ r.keyword }}</td>
<td>{{ r.selling }}</td>
<td>{{ r.grade }}</td>
<td><a href="{{ r.link }}" target="_blank">열기</a></td>
</tr>
{% endfor %}
</table>
{% endif %}

<script>
function updateCount(textarea){
let lines = textarea.value.split("\\n").filter(x=>x.trim()!=="");
document.getElementById("count").innerText = lines.length;
}
</script>
"""

def check_keyword(keyword, index):
    url = "https://openapi.naver.com/v1/search/book.json"

    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }

    params = {
        "query": keyword,
        "display": 1
    }

    try:
        res = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
        data = res.json()
    except:
        return {
            "keyword": keyword,
            "selling": "오류",
            "grade": "B",
            "link": f"https://search.naver.com/search.naver?where=book&query={keyword}",
            "index": index
        }

    items = data.get("items", [])

    if not items:
        return {
            "keyword": keyword,
            "selling": "없음",
            "grade": "A",
            "link": f"https://search.naver.com/search.naver?where=book&query={keyword}",
            "index": index
        }

    item = items[0]

    price = item.get("price")
    discount = item.get("discount")

    # 🔥 핵심 로직
    # 가격 존재하면 판매중으로 판단
    if price and price != "0":
        selling = "있음"
        grade = "B"
    else:
        selling = "없음"
        grade = "A"

    return {
        "keyword": keyword,
        "selling": selling,
        "grade": grade,
        "link": item.get("link"),
        "index": index
    }

@app.route("/", methods=["GET","POST"])
def home():
    results = []
    total_time = 0
    total_count = 0

    if request.method == "POST":
        start = time.time()

        keywords = request.form.get("keywords","").splitlines()
        keywords = [k.strip() for k in keywords if k.strip()]
        total_count = len(keywords)

        sort_option = request.form.get("sort_option","original")

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(check_keyword,kw,i) for i,kw in enumerate(keywords)]
            for future in as_completed(futures):
                results.append(future.result())

        total_time = round(time.time() - start, 2)

        if sort_option == "a_top":
            results.sort(key=lambda x:(x["grade"]!="A", x["index"]))
        elif sort_option == "a_bottom":
            results.sort(key=lambda x:(x["grade"]=="A", x["index"]))
        else:
            results.sort(key=lambda x:x["index"])

    return render_template_string(
        HTML,
        results=results,
        total_time=total_time,
        total_count=total_count
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

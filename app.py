from flask import Flask, render_template_string, request
import requests
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote

app = Flask(__name__)

MAX_WORKERS = 20
TIMEOUT = 5

HTML = """
<!doctype html>
<title>naverbookab</title>
<h1>naverbookab</h1>

<form method="post">
<textarea name="keywords" id="kw" rows="15" cols="60"
placeholder="책 제목을 한 줄에 하나씩 입력 (최대 1000개)"
oninput="updateCount()"></textarea><br>
<p>총 입력 건수: <b><span id="count">0</span></b></p>
<select name="sort_type">
<option value="original">원본순</option>
<option value="best">A에 가까운순</option>
</select>
<br><br>
<button type="submit">일괄 분류</button>
</form>

<script>
function updateCount(){
    let text = document.getElementById("kw").value;
    let lines = text.split("\\n").filter(l => l.trim() !== "");
    document.getElementById("count").innerText = lines.length;
}
</script>

{% if results %}
<p><b>총 소요시간:</b> {{ total_time }}초</p>
<p><b>A 조건 충족 개수:</b> {{ a_count }}</p>

<table border="1" cellpadding="5">
<tr>
<th>키워드</th>
<th>판매처 존재 여부</th>
<th>분류</th>
<th>네이버 링크</th>
</tr>

{% for r in results %}
<tr>
<td>{{ r.keyword }}</td>
<td>{{ r.seller }}</td>
<td>{{ r.grade }}</td>
<td><a href="{{ r.link }}" target="_blank">열기</a></td>
</tr>
{% endfor %}
</table>
{% endif %}
"""

def check_keyword(keyword, index):
    link = f"https://search.naver.com/search.naver?where=book&query={quote(keyword)}"

    try:
        response = requests.get(link, timeout=TIMEOUT, headers={
            "User-Agent": "Mozilla/5.0"
        })
        html = response.text
    except:
        return {
            "keyword": keyword,
            "seller": "확인실패",
            "grade": "B",
            "link": link,
            "index": index
        }

    # 🔥 핵심: "판매처 " 텍스트 존재 여부로 판단
    if "판매처" in html:
        seller_exist = "있음"
        grade = "B"
    else:
        seller_exist = "없음"
        grade = "A"

    return {
        "keyword": keyword,
        "seller": seller_exist,
        "grade": grade,
        "link": link,
        "index": index
    }


@app.route("/", methods=["GET", "POST"])
def home():
    results = []
    total_time = 0
    a_count = 0

    if request.method == "POST":
        start = time.time()

        sort_type = request.form.get("sort_type")

        keywords = request.form.get("keywords", "").splitlines()
        keywords = [k.strip() for k in keywords if k.strip()][:1000]

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [
                executor.submit(check_keyword, kw, i)
                for i, kw in enumerate(keywords)
            ]

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

        total_time = round(time.time() - start, 2)

        # A 개수 계산
        a_count = sum(1 for r in results if r["grade"] == "A")

        # 🔥 정렬
        if sort_type == "best":
            results.sort(key=lambda x: (x["grade"] != "A", x["index"]))
        else:
            results.sort(key=lambda x: x["index"])

    return render_template_string(
        HTML,
        results=results,
        total_time=total_time,
        a_count=a_count
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

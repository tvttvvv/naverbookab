from flask import Flask, render_template_string, request
import requests
import time
import re
from urllib.parse import quote

app = Flask(__name__)

MAX_WORKERS = 15
TIMEOUT = 5

HTML = """
<!doctype html>
<title>naverbookab</title>

<h1>naverbookab</h1>

<form method="post">
<textarea name="keywords" rows="15" cols="60"
placeholder="책 제목을 한 줄에 하나씩 입력 (최대 1000개)"
oninput="updateCount(this)"></textarea><br>
<p>입력 개수: <span id="count">0</span></p>

<select name="sort_option">
<option value="original">원본순</option>
<option value="a_top">A 위로 정렬</option>
<option value="a_bottom">A 아래로 정렬</option>
</select>

<br><br>
<button type="submit">일괄 분류</button>
</form>

{% if results %}
<p><b>총 입력 개수:</b> {{ total_count }}개</p>
<p><b>총 소요시간:</b> {{ total_time }}초</p>

<table border="1" cellpadding="5">
<tr>
<th>키워드</th>
<th>판매처 여부</th>
<th>분류</th>
<th>네이버 링크</th>
</tr>

{% for r in results %}
<tr {% if r.grade == 'A' %}style="background-color:#eaffea;"{% endif %}>
<td>{{ r.keyword }}</td>
<td>{{ r.seller }}</td>
<td>{{ r.grade }}</td>
<td><a href="{{ r.link }}" target="_blank">열기</a></td>
</tr>
{% endfor %}
</table>
{% endif %}

<script>
function updateCount(textarea) {
    let lines = textarea.value.split("\\n").filter(x => x.trim() !== "");
    document.getElementById("count").innerText = lines.length;
}
</script>
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

    # 🔥 절대 A에 판매처 있는게 들어가지 않도록
    seller_match = re.search(r"판매처\s*\d+", html)

    if seller_match:
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
    total_count = 0

    if request.method == "POST":
        start = time.time()

        keywords = request.form.get("keywords", "").splitlines()
        keywords = [k.strip() for k in keywords if k.strip()]
        total_count = len(keywords)

        sort_option = request.form.get("sort_option", "original")

        for i, keyword in enumerate(keywords):
            result = check_keyword(keyword, i)
            results.append(result)

        total_time = round(time.time() - start, 2)

        # 정렬 기능
        if sort_option == "a_top":
            results.sort(key=lambda x: (x["grade"] != "A", x["index"]))
        elif sort_option == "a_bottom":
            results.sort(key=lambda x: (x["grade"] == "A", x["index"]))
        else:
            results.sort(key=lambda x: x["index"])

    return render_template_string(
        HTML,
        results=results,
        total_time=total_time,
        total_count=total_count
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

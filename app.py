from flask import Flask, render_template_string, request
import requests
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

app = Flask(__name__)

MAX_WORKERS = 20

HTML = """
<!doctype html>
<title>naverbookab</title>
<h1>naverbookab</h1>

<form method="post">
<textarea name="keywords" rows="15" cols="70"
placeholder="책 제목을 한 줄에 하나씩 입력 (최대 500개)"></textarea>
<br><br>
<button type="submit">일괄 분류</button>
</form>

{% if results %}
<p><b>총 소요시간:</b> {{ total_time }}초</p>
<table border="1" cellpadding="5">
<tr>
<th>키워드</th>
<th>판매처 여부</th>
<th>분류</th>
<th>링크</th>
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

def check_keyword(keyword):
    url = f"https://search.naver.com/search.naver?where=book&query={keyword}"

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=5)
        html = response.text
    except:
        return {
            "keyword": keyword,
            "seller": "확인실패",
            "grade": "B",
            "link": url
        }

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    # 판매처 N 문구 찾기
    seller_match = re.search(r"판매처\s*\d+", text)

    if seller_match:
        grade = "B"
        seller_status = "있음"
    else:
        grade = "A"
        seller_status = "없음"

    return {
        "keyword": keyword,
        "seller": seller_status,
        "grade": grade,
        "link": url
    }

@app.route("/", methods=["GET", "POST"])
def home():
    results = []
    total_time = 0

    if request.method == "POST":
        start = time.time()

        keywords = request.form.get("keywords", "").splitlines()
        keywords = [k.strip() for k in keywords if k.strip()][:500]

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(check_keyword, kw) for kw in keywords]

            for future in as_completed(futures):
                results.append(future.result())

        total_time = round(time.time() - start, 2)

    return render_template_string(HTML, results=results, total_time=total_time)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

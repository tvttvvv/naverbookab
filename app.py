from flask import Flask, render_template_string, request, jsonify
import requests
import os
import time
import re
from urllib.parse import quote
from bs4 import BeautifulSoup

app = Flask(__name__)

NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET")

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

progress_data = {
    "total": 0,
    "current": 0,
    "start_time": 0,
    "results": []
}

HTML = """
<!doctype html>
<title>naverbookab</title>
<h2>naverbookab</h2>

<textarea id="keywords" rows="15" cols="70"
placeholder="책 제목을 한 줄에 하나씩 입력"></textarea>
<br>
<p>총 입력 건수: <span id="count">0</span></p>
<button onclick="startSearch()">일괄 분류 시작</button>

<p id="progress"></p>

정렬:
<select onchange="sortResults(this.value)">
  <option value="original">원본</option>
  <option value="Afirst">A 우선</option>
</select>

<table border="1" cellpadding="5" id="resultTable">
<tr>
<th>키워드</th>
<th>판매처합</th>
<th>분류</th>
<th>링크</th>
</tr>
</table>

<script>
const textarea = document.getElementById("keywords");
textarea.addEventListener("input", () => {
    const lines = textarea.value.split("\\n").filter(l => l.trim() !== "");
    document.getElementById("count").innerText = lines.length;
});

function startSearch(){
    const keywords = textarea.value;
    fetch("/start", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({keywords: keywords})
    });
    pollProgress();
}

function pollProgress(){
    const interval = setInterval(() => {
        fetch("/progress")
        .then(res => res.json())
        .then(data => {
            if(data.total === 0) return;
            document.getElementById("progress").innerText =
                `진행: ${data.current}/${data.total} | 남은 예상시간: ${data.remaining}s`;

            if(data.current >= data.total){
                clearInterval(interval);
                loadResults();
            }
        });
    }, 1000);
}

function loadResults(){
    fetch("/results")
    .then(res => res.json())
    .then(data => {
        const table = document.getElementById("resultTable");
        table.innerHTML = `
        <tr>
        <th>키워드</th>
        <th>판매처합</th>
        <th>분류</th>
        <th>링크</th>
        </tr>`;
        data.forEach(r => {
            table.innerHTML += `
            <tr>
              <td>${r.keyword}</td>
              <td>${r.total}</td>
              <td>${r.grade}</td>
              <td><a href="${r.link}" target="_blank">열기</a></td>
            </tr>`;
        });
    });
}

function sortResults(type){
    fetch("/results")
    .then(res => res.json())
    .then(data => {
        if(type === "Afirst"){
            data.sort((a,b)=> a.grade.localeCompare(b.grade));
        }
        const table = document.getElementById("resultTable");
        table.innerHTML = `
        <tr>
        <th>키워드</th>
        <th>판매처합</th>
        <th>분류</th>
        <th>링크</th>
        </tr>`;
        data.forEach(r => {
            table.innerHTML += `
            <tr>
              <td>${r.keyword}</td>
              <td>${r.total}</td>
              <td>${r.grade}</td>
              <td><a href="${r.link}" target="_blank">열기</a></td>
            </tr>`;
        });
    });
}
</script>
"""

def check_keyword(keyword):
    url = f"https://search.naver.com/search.naver?where=nexearch&query={quote(keyword)}+도서"

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        text = soup.get_text()
    except:
        return {
            "keyword": keyword,
            "total": 0,
            "grade": "B",
            "link": url
        }

    # 🔴 판매처 숫자 모두 찾기
    seller_matches = re.findall(r"판매처\s*(\d+)", text)

    total_seller = sum(int(x) for x in seller_matches)

    # 🔥 판매처 숫자 하나라도 있으면 무조건 B
    if total_seller > 0:
        grade = "B"
    else:
        grade = "A"

    return {
        "keyword": keyword,
        "total": total_seller,
        "grade": grade,
        "link": url
    }

@app.route("/")
def home():
    return HTML

@app.route("/start", methods=["POST"])
def start():
    data = request.get_json()
    keywords = [k.strip() for k in data["keywords"].splitlines() if k.strip()]

    progress_data["total"] = len(keywords)
    progress_data["current"] = 0
    progress_data["start_time"] = time.time()
    progress_data["results"] = []

    for kw in keywords:
        result = check_keyword(kw)
        progress_data["results"].append(result)
        progress_data["current"] += 1

    return jsonify({"status":"started"})

@app.route("/progress")
def progress():
    total = progress_data["total"]
    current = progress_data["current"]

    if current == 0:
        remaining = 0
    else:
        elapsed = time.time() - progress_data["start_time"]
        avg = elapsed / current
        remaining = int(avg * (total - current))

    return jsonify({
        "total": total,
        "current": current,
        "remaining": remaining
    })

@app.route("/results")
def results():
    return jsonify(progress_data["results"])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

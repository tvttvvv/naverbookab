from flask import Flask, render_template_string, request, Response
import requests
import os
import time
import re
from bs4 import BeautifulSoup
from urllib.parse import quote

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

MAX_PARSE = 20        # 각 키워드당 최대 검사 개수
A_MAX_RESULTS = 5     # 결과 5개 이하 + 판매처 0 → A

HTML = """
<!doctype html>
<title>naverbookab</title>
<h1>naverbookab</h1>

<textarea id="keywords" rows="12" cols="60"
placeholder="책 제목 한 줄에 하나씩 입력 (최대 1000개)"></textarea>
<br>
<p>총 입력 건수: <span id="count">0</span></p>
<button onclick="start()">일괄 분류 시작</button>

<hr>
<div id="status"></div>
<br>
<div>
정렬:
<select id="sortSelect" onchange="sortTable()">
<option value="original">원본</option>
<option value="a_first">A 우선</option>
<option value="b_first">B 우선</option>
</select>
</div>

<table border="1" cellpadding="5" id="resultTable">
<thead>
<tr>
<th>키워드</th>
<th>검색결과수</th>
<th>분류</th>
<th>링크</th>
</tr>
</thead>
<tbody></tbody>
</table>

<script>
let originalData = []

document.getElementById("keywords").addEventListener("input", function(){
    let lines = this.value.split("\\n").filter(x=>x.trim()!="")
    document.getElementById("count").innerText = lines.length
})

function start(){
    let text = document.getElementById("keywords").value
    let lines = text.split("\\n").filter(x=>x.trim()!="")

    fetch("/stream",{
        method:"POST",
        headers:{ "Content-Type":"application/json"},
        body: JSON.stringify({keywords: lines})
    }).then(response=>{
        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let received = 0
        let total = lines.length
        let startTime = Date.now()

        function read(){
            reader.read().then(({done,value})=>{
                if(done) return
                let chunk = decoder.decode(value)
                let lines = chunk.split("\\n")
                lines.forEach(line=>{
                    if(line.trim()=="") return
                    let data = JSON.parse(line)
                    originalData.push(data)
                    received++

                    let elapsed = (Date.now()-startTime)/1000
                    let avg = elapsed/received
                    let remain = Math.round(avg*(total-received))

                    document.getElementById("status").innerHTML =
                        "진행: "+received+"/"+total+
                        " | 남은 예상시간: "+remain+"초"

                    addRow(data)
                })
                read()
            })
        }
        read()
    })
}

function addRow(data){
    let tbody = document.querySelector("#resultTable tbody")
    let tr = document.createElement("tr")
    tr.innerHTML = `
        <td>${data.keyword}</td>
        <td>${data.total}</td>
        <td>${data.grade}</td>
        <td><a href="${data.link}" target="_blank">열기</a></td>
    `
    tbody.appendChild(tr)
}

function sortTable(){
    let val = document.getElementById("sortSelect").value
    let tbody = document.querySelector("#resultTable tbody")
    tbody.innerHTML = ""

    let sorted = [...originalData]

    if(val=="a_first"){
        sorted.sort((a,b)=>a.grade.localeCompare(b.grade))
    }
    if(val=="b_first"){
        sorted.sort((a,b)=>b.grade.localeCompare(a.grade))
    }

    sorted.forEach(addRow)
}
</script>
"""

# 🔥 핵심: 판매처 탐지 (절대 통과 금지)
def has_seller_block(card):
    links = card.find_all("a")
    for a in links:
        txt = a.get_text(strip=True)
        if re.search(r"판매처\s*\d+", txt):
            return True
    return False


def check_keyword(keyword):

    url = f"https://search.naver.com/search.naver?where=nexearch&sm=tab_jum&query={quote(keyword)}&tab=book"

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        html = res.text
    except:
        return {
            "keyword": keyword,
            "total": 0,
            "grade": "B",
            "link": url
        }

    soup = BeautifulSoup(html, "html.parser")

    cards = soup.select("li.bx")
    if not cards:
        cards = soup.select("div.book_wrap")

    total = 0
    seller_found = False

    for c in cards[:MAX_PARSE]:
        total += 1

        # 🔴 판매처 n 있으면 즉시 B 확정
        if has_seller_block(c):
            seller_found = True
            break

    if seller_found:
        grade = "B"
    else:
        grade = "A" if total <= A_MAX_RESULTS else "B"

    return {
        "keyword": keyword,
        "total": total,
        "grade": grade,
        "link": url
    }


@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/stream", methods=["POST"])
def stream():

    data = request.get_json()
    keywords = data.get("keywords", [])[:1000]

    def generate():
        for kw in keywords:
            result = check_keyword(kw.strip())
            yield (json_dumps(result) + "\n")

    return Response(generate(), mimetype="text/plain")


def json_dumps(obj):
    import json
    return json.dumps(obj, ensure_ascii=False)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

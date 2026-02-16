from flask import Flask, request, jsonify, render_template_string
import requests
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)

NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET")

MAX_WORKERS = 20
MAX_DISPLAY = 50

job_status = {
    "running": False,
    "total": 0,
    "done": 0,
    "results": [],
    "start_time": 0
}

HTML = """
<!doctype html>
<title>naverbookab</title>
<h1>naverbookab</h1>

<textarea id="keywords" rows="15" cols="60"
placeholder="책 제목을 한 줄에 하나씩 입력 (최대 1000개)"
oninput="updateCount()"></textarea><br>
<p>총 입력 개수: <span id="count">0</span></p>

<button onclick="startJob()">일괄 분류 시작</button>

<select id="sortMode" onchange="applySort()">
<option value="original">원본 순서</option>
<option value="a_first">A에 가까운 순</option>
</select>

<p id="progress"></p>
<p id="eta"></p>

<table border="1" cellpadding="5" id="resultTable" style="display:none;">
<tr>
<th>키워드</th>
<th>판매처없는개수</th>
<th>분류</th>
<th>링크</th>
</tr>
</table>

<script>
let globalResults = [];

function updateCount(){
    let text = document.getElementById("keywords").value;
    let lines = text.split("\\n").filter(x=>x.trim()!="");
    document.getElementById("count").innerText = lines.length;
}

function startJob(){
    let keywords = document.getElementById("keywords").value;

    fetch("/start", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({keywords:keywords})
    });

    checkStatus();
}

function checkStatus(){
    let interval = setInterval(()=>{
        fetch("/status")
        .then(res=>res.json())
        .then(data=>{
            if(data.total==0) return;

            let percent = ((data.done/data.total)*100).toFixed(1);
            document.getElementById("progress").innerText =
                "진행률: " + percent + "% ("+data.done+"/"+data.total+")";

            document.getElementById("eta").innerText =
                "예상 남은 시간: " + data.eta + "초";

            if(!data.running && data.done===data.total){
                clearInterval(interval);
                globalResults = data.results;
                applySort();
            }
        })
    },1000);
}

function applySort(){
    let mode = document.getElementById("sortMode").value;
    let table = document.getElementById("resultTable");
    table.style.display="block";
    table.innerHTML = `
<tr>
<th>키워드</th>
<th>판매처없는개수</th>
<th>분류</th>
<th>링크</th>
</tr>`;

    let results = [...globalResults];

    if(mode==="a_first"){
        results.sort((a,b)=>{
            if(a.grade!==b.grade){
                return a.grade==="A" ? -1 : 1;
            }
            return a.count - b.count;
        });
    }

    results.forEach(r=>{
        let row = table.insertRow();
        row.insertCell(0).innerText = r.keyword;
        row.insertCell(1).innerText = r.count;
        row.insertCell(2).innerText = r.grade;
        row.insertCell(3).innerHTML =
            "<a href='"+r.link+"' target='_blank'>열기</a>";
    });
}
</script>
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
        response = requests.get(url, headers=headers, params=params, timeout=3)
        data = response.json()
    except:
        return {
            "keyword": keyword,
            "count": 0,
            "grade": "B",
            "link": f"https://search.naver.com/search.naver?query={keyword}"
        }

    items = data.get("items", [])
    no_seller = 0

    for item in items:
        price = item.get("price")
        if not price or price == "0":
            no_seller += 1

    grade = "A" if no_seller <= 1 else "B"

    return {
        "keyword": keyword,
        "count": no_seller,
        "grade": grade,
        "link": f"https://search.naver.com/search.naver?query={keyword}"
    }


def background_job(keywords):
    job_status["running"] = True
    job_status["total"] = len(keywords)
    job_status["done"] = 0
    job_status["results"] = []
    job_status["start_time"] = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(check_keyword, kw): kw for kw in keywords}

        for future in as_completed(futures):
            result = future.result()
            job_status["results"].append(result)
            job_status["done"] += 1

    job_status["running"] = False


@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/start", methods=["POST"])
def start():
    if job_status["running"]:
        return jsonify({"status":"already running"})

    data = request.json
    keywords = data.get("keywords","").splitlines()
    keywords = [k.strip() for k in keywords if k.strip()][:1000]

    thread = threading.Thread(target=background_job, args=(keywords,))
    thread.start()

    return jsonify({"status":"started"})


@app.route("/status")
def status():
    if job_status["total"] == 0:
        return jsonify(job_status)

    elapsed = time.time() - job_status["start_time"]
    avg = elapsed / job_status["done"] if job_status["done"] else 0
    remaining = job_status["total"] - job_status["done"]
    eta = int(avg * remaining) if avg else 0

    return jsonify({
        "running": job_status["running"],
        "total": job_status["total"],
        "done": job_status["done"],
        "eta": eta,
        "results": job_status["results"] if not job_status["running"] else []
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

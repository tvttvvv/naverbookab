from flask import Flask, request, jsonify, render_template_string, Response
import os
import time
import uuid
import json
import threading
import queue
import urllib.parse
import re
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# ====== 튜닝 값 ======
MAX_KEYWORDS = 1000
# 동시에 너무 많이 때리면 막히거나 느려져서 워커 타임아웃/메모리 문제가 커집니다.
# "시간 오래 걸려도 정확"이 목표라 낮게 잡습니다.
WORKERS = int(os.environ.get("WORKERS", "6"))
REQUEST_TIMEOUT = float(os.environ.get("REQUEST_TIMEOUT", "8"))
MAX_RESULTS_PARSE = int(os.environ.get("MAX_RESULTS_PARSE", "50"))

UA = os.environ.get(
    "UA",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36",
)

SELLER_RE = re.compile(r"판매처\s*\d+")

# ====== 인메모리 작업 저장소 (Railway 단일 인스턴스 기준) ======
JOBS = {}  # job_id -> dict(state, created_at, total, done, results, q, started, finished, errors)


HTML = r"""
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>naverbookab</title>
  <style>
    body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Apple SD Gothic Neo,Malgun Gothic,sans-serif;margin:18px}
    h1{margin:0 0 12px 0}
    .row{display:flex;gap:16px;align-items:flex-start;flex-wrap:wrap}
    textarea{width:520px;max-width:92vw;height:280px}
    .panel{min-width:260px;max-width:92vw;border:1px solid #ddd;padding:12px;border-radius:10px}
    .muted{color:#666;font-size:13px}
    .btn{padding:8px 12px;border:1px solid #111;border-radius:8px;background:#111;color:#fff;cursor:pointer}
    .btn:disabled{opacity:.55;cursor:not-allowed}
    select{padding:6px 8px;border-radius:8px;border:1px solid #ccc}
    table{border-collapse:collapse;width:min(980px, 96vw);margin-top:12px}
    th,td{border:1px solid #ccc;padding:6px 8px;font-size:14px}
    th{background:#f5f5f5}
    .good{font-weight:700}
    .bad{color:#333}
    .bar{height:10px;background:#eee;border-radius:999px;overflow:hidden}
    .bar > div{height:100%;background:#111;width:0%}
    .topline{display:flex;gap:12px;align-items:center;flex-wrap:wrap}
    .pill{display:inline-block;padding:2px 8px;border:1px solid #ddd;border-radius:999px;font-size:12px}
    .right{margin-left:auto}
  </style>
</head>
<body>
  <div class="topline">
    <h1>naverbookab</h1>
    <div class="right">
      <label class="muted">정렬</label>
      <select id="sortSel">
        <option value="original">원본</option>
        <option value="a_close">A에 가까운순</option>
        <option value="count_asc">결과 적은순</option>
        <option value="count_desc">결과 많은순</option>
      </select>
    </div>
  </div>

  <div class="row">
    <div>
      <textarea id="kw" placeholder="책 제목을 한 줄에 하나씩 입력 (최대 {{max_keywords}}개)"></textarea>
      <div class="muted" style="margin-top:6px">
        총 <b id="kwCount">0</b>건
        <span class="pill">최대 {{max_keywords}}건</span>
      </div>
      <div style="margin-top:10px">
        <button class="btn" id="startBtn">일괄 분류</button>
        <button class="btn" id="stopBtn" disabled style="background:#444;border-color:#444">중지</button>
      </div>

      <div style="margin-top:14px">
        <div class="bar"><div id="barFill"></div></div>
        <div class="muted" style="margin-top:6px">
          진행: <b id="done">0</b>/<b id="total">0</b> ·
          남은시간: <b id="eta">-</b> ·
          경과: <b id="elapsed">-</b>
        </div>
      </div>
    </div>

    <div class="panel">
      <div style="font-weight:700;margin-bottom:6px">A 후보(상단 표시)</div>
      <div class="muted" style="margin-bottom:10px">
        A 조건: <b>판매처 n</b> 텍스트가 결과에 <b>단 1개라도 있으면 무조건 B</b>
      </div>
      <ol id="aList" class="muted" style="margin:0;padding-left:18px;max-height:260px;overflow:auto"></ol>
    </div>
  </div>

  <table>
    <thead>
      <tr>
        <th style="width:360px">키워드</th>
        <th style="width:90px">결과 개수</th>
        <th style="width:120px">판매처 포함</th>
        <th style="width:70px">분류</th>
        <th style="width:110px">소요(초)</th>
        <th style="width:90px">네이버 링크</th>
      </tr>
    </thead>
    <tbody id="tb"></tbody>
  </table>

<script>
  const kw = document.getElementById('kw');
  const kwCount = document.getElementById('kwCount');
  const startBtn = document.getElementById('startBtn');
  const stopBtn = document.getElementById('stopBtn');
  const sortSel = document.getElementById('sortSel');
  const tb = document.getElementById('tb');
  const aList = document.getElementById('aList');

  const doneEl = document.getElementById('done');
  const totalEl = document.getElementById('total');
  const etaEl = document.getElementById('eta');
  const elapsedEl = document.getElementById('elapsed');
  const barFill = document.getElementById('barFill');

  let es = null;
  let jobId = null;
  let startedAt = null;
  let results = []; // {keyword,count,has_seller,grade,sec,link,idx}

  function parseLines() {
    const lines = kw.value.split(/\r?\n/).map(s=>s.trim()).filter(Boolean);
    kwCount.textContent = lines.length;
    return lines;
  }
  kw.addEventListener('input', parseLines);
  parseLines();

  function fmtSec(s){
    if (s == null) return '-';
    return (Math.round(s*100)/100).toFixed(2);
  }

  function render(){
    const mode = sortSel.value;
    let arr = results.slice();

    if (mode === 'a_close') {
      // A에 가까운순: 판매처 포함(false 우선) -> 결과 개수 적은순 -> 원본 인덱스
      arr.sort((a,b)=>{
        if (a.has_seller !== b.has_seller) return (a.has_seller?1:0) - (b.has_seller?1:0);
        if (a.count !== b.count) return a.count - b.count;
        return a.idx - b.idx;
      });
    } else if (mode === 'count_asc') {
      arr.sort((a,b)=> (a.count - b.count) || (a.idx - b.idx));
    } else if (mode === 'count_desc') {
      arr.sort((a,b)=> (b.count - a.count) || (a.idx - b.idx));
    } else {
      arr.sort((a,b)=> a.idx - b.idx);
    }

    tb.innerHTML = '';
    for (const r of arr){
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${escapeHtml(r.keyword)}</td>
        <td style="text-align:center">${r.count}</td>
        <td style="text-align:center">${r.has_seller ? '있음' : '없음'}</td>
        <td style="text-align:center" class="${r.grade==='A'?'good':'bad'}">${r.grade}</td>
        <td style="text-align:center">${fmtSec(r.sec)}</td>
        <td style="text-align:center"><a target="_blank" href="${r.link}">열기</a></td>
      `;
      tb.appendChild(tr);
    }

    // A 후보 리스트 (판매처 없음 + grade A만)
    const aCandidates = arr.filter(x=>x.grade==='A' && !x.has_seller);
    aList.innerHTML = '';
    for (const r of aCandidates.slice(0, 60)){
      const li = document.createElement('li');
      li.innerHTML = `<a target="_blank" href="${r.link}">${escapeHtml(r.keyword)}</a> <span class="muted">(결과 ${r.count})</span>`;
      aList.appendChild(li);
    }
  }

  function escapeHtml(str){
    return str.replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  }

  sortSel.addEventListener('change', render);

  function setProgress(done,total){
    doneEl.textContent = done;
    totalEl.textContent = total;
    const pct = total ? Math.floor((done/total)*100) : 0;
    barFill.style.width = pct + '%';

    const now = Date.now();
    const elapsed = startedAt ? (now - startedAt)/1000 : 0;
    elapsedEl.textContent = startedAt ? fmtSec(elapsed) + 's' : '-';

    if (done > 0 && total > 0) {
      const avg = elapsed / done;
      const remain = (total - done) * avg;
      etaEl.textContent = fmtSec(remain) + 's';
    } else {
      etaEl.textContent = '-';
    }
  }

  async function start(){
    const lines = parseLines();
    if (lines.length === 0) return;
    if (lines.length > {{max_keywords}}) {
      alert('최대 {{max_keywords}}건까지 가능합니다.');
      return;
    }

    startBtn.disabled = true;
    stopBtn.disabled = false;
    results = [];
    render();
    setProgress(0, lines.length);

    const resp = await fetch('/start', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({keywords: lines})
    });

    if (!resp.ok) {
      const t = await resp.text();
      alert('시작 실패: ' + t);
      startBtn.disabled = false;
      stopBtn.disabled = true;
      return;
    }

    const data = await resp.json();
    jobId = data.job_id;
    startedAt = Date.now();

    es = new EventSource(`/stream/${jobId}`);
    es.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);

      if (msg.type === 'progress') {
        // 한 건 결과 추가
        results.push(msg.result);
        setProgress(msg.done, msg.total);
        render();
      } else if (msg.type === 'done') {
        setProgress(msg.total, msg.total);
        render();
        cleanup();
      } else if (msg.type === 'error') {
        alert('오류: ' + msg.message);
        cleanup();
      }
    };

    es.onerror = () => {
      // 네트워크 순간 끊김 등. 그냥 종료 처리.
      cleanup();
    };
  }

  async function stop(){
    if (!jobId) return;
    await fetch(`/stop/${jobId}`, {method:'POST'});
    cleanup();
  }

  function cleanup(){
    if (es) { es.close(); es = null; }
    startBtn.disabled = false;
    stopBtn.disabled = true;
    jobId = null;
  }

  startBtn.addEventListener('click', start);
  stopBtn.addEventListener('click', stop);
</script>
</body>
</html>
"""


def build_search_url(keyword: str) -> str:
    q = urllib.parse.quote(keyword)
    return f"https://search.naver.com/search.naver?where=book&query={q}"


def fetch_html(url: str) -> str:
    headers = {"User-Agent": UA}
    r = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.text


def parse_book_section_counts(html: str):
    """
    네가 말한 '네이버 도서' 검색결과 리스트(2번째 화면)에서:
    - total_count: 결과 항목 개수(최대 MAX_RESULTS_PARSE까지만)
    - has_seller: '판매처 n' 문구가 단 1개라도 있으면 True (A로 절대 못 감)
    """
    soup = BeautifulSoup(html, "html.parser")

    # 1) 흔히 결과 카드가 li.bx 로 잡힘 (네이버 검색 결과 공통)
    cards = soup.select("li.bx")
    if not cards:
        # 방어적으로 다른 후보도 조금 시도
        cards = soup.select("div.book_wrap, div.api_subject_bx, li")  # fallback

    items = []
    for c in cards:
        txt = c.get_text(" ", strip=True)
        # "도서" 결과처럼 보이는 것만 추리기 위한 최소한의 휴리스틱
        # (너무 넓게 잡히면 다른 섹션까지 섞여버려 결과가 틀어짐)
        if ("저자" in txt and ("출판" in txt or "발행" in txt)) or ("네이버 도서" in txt):
            items.append(txt)

    # 너무 적게 잡히면 그냥 li.bx 전체로 재시도 (그래도 판매처 감지는 됨)
    if len(items) < 1:
        items = [c.get_text(" ", strip=True) for c in cards]

    items = items[:MAX_RESULTS_PARSE]

    total_count = len(items)
    has_seller = any(SELLER_RE.search(t) for t in items)

    return total_count, has_seller


def classify(keyword: str):
    """
    A 조건(강제):
    - 판매처 n 문구가 단 1개라도 있으면 무조건 B
    - 그리고 "경쟁 적은 단일 책 키워드" 쪽으로: 총 결과가 적을수록 A에 가깝게
      (여기서는 total_count <= 5 를 A 기준으로 사용. 필요하면 env로 조절)
    """
    t0 = time.time()
    url = build_search_url(keyword)

    try:
        html = fetch_html(url)
        total_count, has_seller = parse_book_section_counts(html)

        # A 기준: 판매처 문구 없어야 함 + 결과가 5개 이하(기본값)
        a_max = int(os.environ.get("A_MAX_RESULTS", "5"))
        grade = "A" if (not has_seller and total_count <= a_max) else "B"

        return {
            "keyword": keyword,
            "count": total_count,
            "has_seller": bool(has_seller),
            "grade": grade,
            "sec": round(time.time() - t0, 2),
            "link": url,
        }
    except Exception:
        # 실패는 B로 처리(안전)
        return {
            "keyword": keyword,
            "count": 0,
            "has_seller": True,   # 실패인데 A로 가면 안 되니까 True로 둠
            "grade": "B",
            "sec": round(time.time() - t0, 2),
            "link": url,
        }


def worker(job_id: str):
    job = JOBS[job_id]
    q = job["q"]
    keywords = job["keywords"]
    total = len(keywords)

    job["state"] = "running"
    job["started"] = time.time()

    # 간단한 워커 풀(스레드) 구현: 큐에 인덱스를 넣고 소비
    idx_q = queue.Queue()
    for i in range(total):
        idx_q.put(i)

    lock = threading.Lock()

    def run_one():
        while True:
            if job.get("stop"):
                return
            try:
                i = idx_q.get_nowait()
            except Exception:
                return
            kw = keywords[i]
            res = classify(kw)
            res["idx"] = i

            with lock:
                job["done"] += 1
                job["results"].append(res)
                done = job["done"]

            q.put({"type": "progress", "done": done, "total": total, "result": res})
            idx_q.task_done()

    threads = []
    for _ in range(WORKERS):
        t = threading.Thread(target=run_one, daemon=True)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    job["finished"] = time.time()
    job["state"] = "done"
    q.put({"type": "done", "total": total})


@app.route("/", methods=["GET"])
def home():
    return render_template_string(HTML, max_keywords=MAX_KEYWORDS)


@app.route("/start", methods=["POST"])
def start():
    data = request.get_json(force=True, silent=True) or {}
    keywords = data.get("keywords", [])

    if not isinstance(keywords, list):
        return "keywords must be a list", 400

    keywords = [str(k).strip() for k in keywords if str(k).strip()]
    if len(keywords) == 0:
        return "no keywords", 400
    if len(keywords) > MAX_KEYWORDS:
        return f"max {MAX_KEYWORDS}", 400

    job_id = uuid.uuid4().hex
    q = queue.Queue()

    JOBS[job_id] = {
        "state": "queued",
        "created_at": time.time(),
        "keywords": keywords,
        "total": len(keywords),
        "done": 0,
        "results": [],
        "q": q,
        "stop": False,
        "started": None,
        "finished": None,
    }

    t = threading.Thread(target=worker, args=(job_id,), daemon=True)
    t.start()

    return jsonify({"job_id": job_id})


@app.route("/stop/<job_id>", methods=["POST"])
def stop(job_id):
    job = JOBS.get(job_id)
    if not job:
        return "no job", 404
    job["stop"] = True
    # 스트림 쪽에 종료 신호
    job["q"].put({"type": "done", "total": job["total"]})
    return "ok"


@app.route("/stream/<job_id>")
def stream(job_id):
    job = JOBS.get(job_id)
    if not job:
        return "no job", 404

    def event_stream():
        q = job["q"]
        while True:
            msg = q.get()
            yield f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"
            if msg.get("type") == "done":
                break

    return Response(event_stream(), mimetype="text/event-stream")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=False)

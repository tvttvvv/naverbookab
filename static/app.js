async function run() {
  const raw = document.getElementById("keywords").value.trim();
  if (!raw) return;

  const keywords = raw.split("\n").map(k => k.trim()).filter(Boolean);
  if (keywords.length > 20) {
    alert("한 번에 20개 이하만 입력하세요");
    return;
  }

  const tbody = document.getElementById("result");
  tbody.innerHTML = "";

  for (let kw of keywords) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="5">검색중: ${kw}</td>`;
    tbody.appendChild(tr);

    try {
      const res = await fetch("/search", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({keyword: kw})
      });

      const data = await res.json();

      if (data.error) {
        tr.innerHTML = `<td colspan="5" style="color:red;">${data.error}</td>`;
        continue;
      }

      tr.innerHTML = `
        <td>${data.class === "A" ? `<input type="checkbox">` : ""}</td>
        <td>${data.keyword}</td>
        <td>${data.count}</td>
        <td>${data.class}</td>
        <td><a href="${data.url}" target="_blank">열기</a></td>
      `;
    } catch (e) {
      tr.innerHTML = `<td colspan="5">네트워크 오류</td>`;
    }
  }
}

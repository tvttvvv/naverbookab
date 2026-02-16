async function searchMany() {
  const raw = document.getElementById("keywords").value.trim();
  if (!raw) return;

  const keywords = raw.split("\n").map(s => s.trim()).filter(Boolean);
  const tbody = document.getElementById("resultBody");
  tbody.innerHTML = "";

  for (const kw of keywords) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>...</td><td>${kw}</td><td>로딩</td><td></td><td></td>`;
    tbody.appendChild(tr);

    try {
      const res = await fetch("/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ keyword: kw })
      });
      const data = await res.json();

      tr.innerHTML = `
        <td>${data.class === "A" ? `<input type="checkbox"/>` : ""}</td>
        <td>${data.keyword}</td>
        <td>${data.count}</td>
        <td class="${data.class}">${data.class}</td>
        <td><a href="${data.url}" target="_blank">열기</a></td>
      `;
    } catch (e) {
      tr.innerHTML = `<td colspan="5">에러: ${kw}</td>`;
    }
  }
}

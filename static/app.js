async function searchMany() {
  const raw = document.getElementById("keywords").value.trim();
  if (!raw) {
    alert("키워드를 입력하세요");
    return;
  }

  const keywords = raw.split("\n").map(s => s.trim()).filter(Boolean);
  const tbody = document.querySelector("#resultTable tbody");
  tbody.innerHTML = "";

  for (const kw of keywords) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>로딩...</td><td>${kw}</td><td>...</td><td>...</td>`;
    tbody.appendChild(tr);

    const res = await fetch("/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ keyword: kw })
    });
    const data = await res.json();

    tr.innerHTML = `
      <td>${data.class === "A" ? `<input type="checkbox" />` : ""}</td>
      <td>${data.keyword}</td>
      <td class="${data.class}">${data.class}</td>
      <td><a href="${data.url}" target="_blank">열기</a></td>
    `;
  }
}
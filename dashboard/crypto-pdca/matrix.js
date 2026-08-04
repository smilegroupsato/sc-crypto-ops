const PCT = new Intl.NumberFormat("ja-JP", {
  maximumFractionDigits: 1,
});

function tagClass(label) {
  if (!label) return "";
  if (label.includes("Entry")) return "buy";
  if (label.includes("小さく") || label.includes("Watch")) return "caution";
  return "stop";
}

function setStatus(text, cls = "") {
  const el = document.getElementById("matrixStatus");
  if (!el) return;
  el.textContent = text;
  el.className = "pill " + cls;
}

function renderBands(bands) {
  const el = document.getElementById("decisionBands");
  el.innerHTML = (bands || [])
    .map((b) => {
      const range = b.min !== undefined && b.max !== undefined
        ? `${b.min} - ${b.max}`
        : b.min !== undefined
          ? `${b.min}以上`
          : `${b.max}以下`;
      return `
        <article class="band-card">
          <strong>${b.label}</strong>
          <span>${range}</span>
          <p>${b.rule}</p>
        </article>
      `;
    })
    .join("");
}

function renderCriteria(criteria) {
  const el = document.getElementById("criteriaGrid");
  el.innerHTML = (criteria || [])
    .map((c) => `
      <article class="criterion">
        <div>
          <strong>${c.label}</strong>
          <span>${c.key}</span>
        </div>
        <em>${c.weight}</em>
        <p>${c.description}</p>
      </article>
    `)
    .join("");
}

function renderMatrix(entryEvaluation) {
  const el = document.getElementById("matrixTable");
  const criteria = entryEvaluation.criteria || [];
  const rows = [...(entryEvaluation.matrix || [])].sort((a, b) => b.totalScore - a.totalScore);
  const scoreHeads = criteria.map((c) => `<th title="${c.description}">${c.label}<br /><span>${c.weight}</span></th>`).join("");
  el.innerHTML = `
    <div class="table-wrap">
      <table class="full-matrix-table">
        <thead>
          <tr>
            <th>銘柄</th>
            <th>点数</th>
            <th>判定</th>
            ${scoreHeads}
            <th>強い根拠</th>
            <th>主なリスク</th>
            <th>次アクション</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map((r) => `
            <tr>
              <td><b>${r.symbol}</b><span>${r.type}</span></td>
              <td><strong>${PCT.format(r.totalScore)}</strong></td>
              <td><em class="tag ${tagClass(r.band || r.decision)}">${r.band || r.decision}</em></td>
              ${criteria.map((c) => `<td>${r.scores?.[c.key] ?? "--"}</td>`).join("")}
              <td class="text-cell">${r.positives || ""}</td>
              <td class="text-cell">${r.risks || ""}</td>
              <td class="text-cell">${r.action || ""}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderList(id, items) {
  const el = document.getElementById(id);
  el.innerHTML = `<ol class="improvement-list">${(items || []).map((item) => `<li>${item}</li>`).join("")}</ol>`;
}

function renderSources(data) {
  const el = document.getElementById("sourceLinks");
  const practice = data.entryEvaluation?.practiceData || [];
  const links = [
    ["Dashboard data", "dashboard/crypto-pdca/data.json"],
    ["Matrix log", data.source?.entryMatrixLog],
    ...practice.map((p, i) => [`Practice data ${i + 1}`, p]),
  ].filter(([, path]) => path);
  el.innerHTML = links
    .map(([label, path]) => `
      <a href="https://github.com/smilegroupsato/sc-crypto-ops/blob/main/${path}" target="_blank" rel="noreferrer">
        <strong>${label}</strong>
        <span>${path}</span>
      </a>
    `)
    .join("");
}

async function init() {
  try {
    const res = await fetch("./data.json?ts=" + Date.now(), { cache: "no-store" });
    if (!res.ok) throw new Error("data.json " + res.status);
    const data = await res.json();
    const ev = data.entryEvaluation;
    if (!ev) throw new Error("entryEvaluation missing");
    document.getElementById("matrixUpdated").textContent = `更新: ${ev.updatedAtJst || data.updatedAtJst || "--"} / ${ev.scoreScale || ""}`;
    renderBands(ev.decisionBands);
    renderCriteria(ev.criteria);
    renderMatrix(ev);
    renderList("improvementLoop", ev.improvementLoop);
    renderList("metricsList", ev.metricsToTrack);
    renderSources(data);
    setStatus("data.json", "good");
  } catch (error) {
    setStatus("error", "bad");
    document.getElementById("matrixUpdated").textContent = "data.jsonを読めませんでした";
  }
}

init();

const JPY = new Intl.NumberFormat("ja-JP", {
  style: "currency",
  currency: "JPY",
  maximumFractionDigits: 0,
});

const USD = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 6,
});

const PCT = new Intl.NumberFormat("ja-JP", {
  signDisplay: "always",
  maximumFractionDigits: 2,
});

const TOTAL_CAPITAL = 1_000_000;
const CORE_CASH = 550_000;
const MEME_BASE_CASH = 550_000;
const MEME_TACTICAL_CASH = 100_000;
const FALLBACK_USD_JPY = 157.75;

const positions = [
  { scenario: "Core", symbol: "AAVE", id: "aave", amountJpy: 75_000, entryUsd: 91.85, rank: 2 },
  { scenario: "Core", symbol: "UNI", id: "uniswap", amountJpy: 75_000, entryUsd: 4.14, rank: 14 },
  { scenario: "Core", symbol: "AERO", id: "aerodrome-finance", amountJpy: 75_000, entryUsd: 0.4056, rank: 9 },
  { scenario: "Core", symbol: "ONDO", id: "ondo-finance", amountJpy: 75_000, entryUsd: 0.3925, rank: 12 },
  { scenario: "Core", symbol: "ENA", id: "ethena", amountJpy: 75_000, entryUsd: 0.08482, rank: 13 },
  { scenario: "Core", symbol: "SOL", id: "solana", amountJpy: 75_000, entryUsd: 73.12, rank: 1 },
  { scenario: "Meme", symbol: "PUMP", id: "pump-fun", amountJpy: 80_000, entryUsd: 0.002236, rank: 3 },
  { scenario: "Meme", symbol: "PEPE", id: "pepe", amountJpy: 70_000, entryUsd: 0.000002912, rank: 4 },
  { scenario: "Meme", symbol: "PENGU", id: "pudgy-penguins", amountJpy: 60_000, entryUsd: 0.006143, rank: 5 },
  { scenario: "Meme", symbol: "BONK", id: "bonk", amountJpy: 50_000, entryUsd: 0.000002858, rank: 6 },
  { scenario: "Meme", symbol: "WIF", id: "dogwifcoin", amountJpy: 35_000, entryUsd: 0.1408, rank: 7 },
  { scenario: "Meme", symbol: "FARTCOIN", id: "fartcoin", amountJpy: 25_000, entryUsd: 0.1311, rank: 8 },
  { scenario: "Meme", symbol: "ANSEM", id: "the-black-bull", amountJpy: 15_000, entryUsd: 0.1764, rank: 10 },
  { scenario: "Meme", symbol: "USELESS", id: "useless-3", amountJpy: 15_000, entryUsd: 0.04869, rank: 11 },
];

const fallbackPrices = {
  aave: { usd: 91.77, jpy: 14461, usd_24h_change: -0.2, usd_24h_vol: 180000000 },
  uniswap: { usd: 2.83, jpy: 446, usd_24h_change: -6.5, usd_24h_vol: 90000000 },
  "aerodrome-finance": { usd: 0.390367, jpy: 62, usd_24h_change: 0.8, usd_24h_vol: 25000000 },
  "ondo-finance": { usd: 0.330863, jpy: 52, usd_24h_change: -4.2, usd_24h_vol: 60000000 },
  ethena: { usd: 0.07605, jpy: 12, usd_24h_change: -3.7, usd_24h_vol: 50000000 },
  solana: { usd: 77.97, jpy: 12299, usd_24h_change: 3.4, usd_24h_vol: 1500000000 },
  "pump-fun": { usd: 0.002236, jpy: 0.352729, usd_24h_change: 7.8, usd_24h_vol: 85918329 },
  pepe: { usd: 0.000002912, jpy: 0.000459368, usd_24h_change: 3.0, usd_24h_vol: 130397128 },
  "pudgy-penguins": { usd: 0.006143, jpy: 0.969058, usd_24h_change: 1.6, usd_24h_vol: 32084544 },
  bonk: { usd: 0.000002858, jpy: 0.00045085, usd_24h_change: 0.59, usd_24h_vol: 22205809 },
  dogwifcoin: { usd: 0.1408, jpy: 22.2112, usd_24h_change: 1.9, usd_24h_vol: 27184954 },
  fartcoin: { usd: 0.1311, jpy: 20.681025, usd_24h_change: 3.7, usd_24h_vol: 14862626 },
  "the-black-bull": { usd: 0.1764, jpy: 27.8271, usd_24h_change: -8.6, usd_24h_vol: 11911489 },
  "useless-3": { usd: 0.04869, jpy: 7.680848, usd_24h_change: -3.5, usd_24h_vol: 5469835 },
};

const recs = [
  { symbol: "AAVE", type: "Core", action: "Entry可", note: "90 USD維持ならCore候補。大きく追わず分割。" },
  { symbol: "SOL", type: "Core", action: "Entry可", note: "Entry基準の再設計対象。強いが過熱確認。" },
  { symbol: "AERO", type: "Core", action: "小さく", note: "高リスクだがDeFi回転枠として監視。" },
  { symbol: "PUMP", type: "Meme", action: "Entry可", note: "勢い枠。出来高低下なら即Reduce。" },
  { symbol: "PEPE", type: "Meme", action: "Entry可", note: "大型ミームの流動性枠。" },
  { symbol: "PENGU", type: "Meme", action: "Entry可", note: "ブランド・Solana Meme枠。" },
  { symbol: "BONK", type: "Meme", action: "小さく", note: "回転枠。弱ければ入替候補。" },
  { symbol: "UNI", type: "Core", action: "見送り", note: "T+1 Stop Hit。Post-mortem優先。" },
];

const state = {
  prices: { ...fallbackPrices },
  usdJpy: FALLBACK_USD_JPY,
  loadedFromApi: false,
};

function yen(value) {
  return JPY.format(Math.round(value || 0));
}

function usd(value) {
  if (!Number.isFinite(value)) return "--";
  return USD.format(value);
}

function pct(value) {
  if (!Number.isFinite(value)) return "--";
  return `${PCT.format(value)}%`;
}

function classByPnl(value) {
  if (value > 0) return "gain";
  if (value < 0) return "loss";
  return "";
}

function loadSpecEntries() {
  try {
    return JSON.parse(localStorage.getItem("sc_crypto_spec_entries") || "{}");
  } catch {
    return {};
  }
}

function saveSpecEntries(entries) {
  localStorage.setItem("sc_crypto_spec_entries", JSON.stringify(entries));
}

function lockSpecEntries() {
  const entries = loadSpecEntries();
  const lockedAt = new Date().toISOString();
  positions
    .filter((p) => p.scenario === "Meme")
    .forEach((p) => {
      const price = state.prices[p.id]?.usd;
      if (Number.isFinite(price)) {
        entries[p.id] = { entryUsd: price, lockedAt };
      }
    });
  saveSpecEntries(entries);
  render();
}

function getEntryUsd(position) {
  if (Number.isFinite(position.entryUsd)) return position.entryUsd;
  const spec = loadSpecEntries()[position.id];
  if (Number.isFinite(spec?.entryUsd)) return spec.entryUsd;
  return state.prices[position.id]?.usd || null;
}

function enrichPosition(position) {
  const price = state.prices[position.id] || {};
  const entryUsd = getEntryUsd(position);
  const currentUsd = price.usd;
  const entryJpy = entryUsd * state.usdJpy;
  const currentJpy = Number.isFinite(price.jpy) ? price.jpy : currentUsd * state.usdJpy;
  const qty = position.amountJpy / entryJpy;
  const valueJpy = qty * currentJpy;
  const pnlJpy = valueJpy - position.amountJpy;
  const pnlPct = (currentUsd / entryUsd - 1) * 100;
  const change24h = price.usd_24h_change;
  const volume24h = price.usd_24h_vol;
  return { ...position, entryUsd, currentUsd, currentJpy, qty, valueJpy, pnlJpy, pnlPct, change24h, volume24h };
}

function judge(p) {
  if (!Number.isFinite(p.pnlPct)) return { label: "Watch", cls: "caution" };
  if (p.symbol === "UNI" && p.pnlPct < -15) return { label: "Stop", cls: "stop" };
  if (p.pnlPct <= -20) return { label: "Stop", cls: "stop" };
  if (p.pnlPct <= -10) return { label: "Reduce", cls: "caution" };
  if (p.pnlPct >= 18 && p.scenario === "Meme") return { label: "Take Profit", cls: "buy" };
  if (p.pnlPct >= 8) return { label: "Hold+", cls: "buy" };
  return { label: "Hold", cls: "buy" };
}

function scenarioSummary(enriched) {
  const corePositions = enriched.filter((p) => p.scenario === "Core");
  const memePositions = enriched.filter((p) => p.scenario === "Meme");
  const coreInvested = corePositions.reduce((sum, p) => sum + p.amountJpy, 0);
  const memeInvested = memePositions.reduce((sum, p) => sum + p.amountJpy, 0);
  const coreValue = corePositions.reduce((sum, p) => sum + (p.valueJpy || p.amountJpy), 0);
  const memeValue = memePositions.reduce((sum, p) => sum + (p.valueJpy || p.amountJpy), 0);
  const coreTotal = CORE_CASH + coreValue;
  const memeTotal = MEME_BASE_CASH + MEME_TACTICAL_CASH + memeValue;
  return {
    core: {
      invested: coreInvested,
      cash: CORE_CASH,
      value: coreValue,
      total: coreTotal,
      pnl: coreTotal - TOTAL_CAPITAL,
      pnlPct: (coreTotal / TOTAL_CAPITAL - 1) * 100,
    },
    meme: {
      invested: memeInvested,
      cash: MEME_BASE_CASH + MEME_TACTICAL_CASH,
      value: memeValue,
      total: memeTotal,
      pnl: memeTotal - TOTAL_CAPITAL,
      pnlPct: (memeTotal / TOTAL_CAPITAL - 1) * 100,
    },
  };
}

function renderMetrics(summary) {
  document.getElementById("coreTotal").textContent = yen(summary.core.total);
  document.getElementById("corePnl").textContent = `${yen(summary.core.pnl)} / ${pct(summary.core.pnlPct)}`;
  document.getElementById("corePnl").className = classByPnl(summary.core.pnl);
  document.getElementById("memeTotal").textContent = yen(summary.meme.total);
  document.getElementById("memePnl").textContent = `${yen(summary.meme.pnl)} / ${pct(summary.meme.pnlPct)}`;
  document.getElementById("memePnl").className = classByPnl(summary.meme.pnl);
}

function renderScenarioList(summary) {
  const el = document.getElementById("scenarioList");
  el.innerHTML = [
    ["Core 45 / Cash 55", summary.core],
    ["Speculative / Meme", summary.meme],
  ]
    .map(
      ([name, s]) => `
        <div class="scenario-card">
          <b>${name}</b>
          <span>現金 ${yen(s.cash)} / 投資評価 ${yen(s.value)}</span><br />
          <span class="${classByPnl(s.pnl)}">総資産損益 ${yen(s.pnl)} / ${pct(s.pnlPct)}</span>
        </div>
      `,
    )
    .join("");
}

function renderPositions(enriched) {
  const body = document.getElementById("positionsBody");
  body.innerHTML = enriched
    .sort((a, b) => a.scenario.localeCompare(b.scenario) || a.rank - b.rank)
    .map((p) => {
      const j = judge(p);
      return `
        <tr>
          <td>${p.scenario}</td>
          <td><b>${p.symbol}</b></td>
          <td>${yen(p.amountJpy)}</td>
          <td>${usd(p.entryUsd)}</td>
          <td>${usd(p.currentUsd)}</td>
          <td>${yen(p.valueJpy)}</td>
          <td class="${classByPnl(p.pnlPct)}">${pct(p.pnlPct)}</td>
          <td><span class="tag ${j.cls}">${j.label}</span></td>
        </tr>
      `;
    })
    .join("");
}

function renderRecommendations() {
  const el = document.getElementById("recommendations");
  el.innerHTML = `<div class="rec-list">${recs
    .map(
      (r) => `
        <div class="rec-item">
          <b>${r.symbol}</b>
          <span>${r.type}<br />${r.note}</span>
          <em class="tag ${r.action === "見送り" ? "stop" : r.action === "小さく" ? "caution" : "buy"}">${r.action}</em>
        </div>
      `,
    )
    .join("")}</div>`;
}

function renderDecision(summary, enriched) {
  const best = [...enriched].sort((a, b) => b.pnlPct - a.pnlPct)[0];
  const worst = [...enriched].sort((a, b) => a.pnlPct - b.pnlPct)[0];
  const memeStops = enriched.filter((p) => p.scenario === "Meme" && judge(p).label === "Stop");
  const decisions = [
    ["資金管理", "現金55万円は固定。Coreは45万円全部、Memeは35万円だけ使い、10万円は戦術現金。"],
    ["比較", `現時点では ${summary.core.total >= summary.meme.total ? "Core" : "Meme"} が総資産評価で優位。`],
    ["強い銘柄", `${best?.symbol || "--"} が相対的に強い。追う場合も分割Entry。`],
    ["弱い銘柄", `${worst?.symbol || "--"} はルール確認。Stop/Reduce条件を優先。`],
    ["新規探索", "日次ルーティンでは保有評価に加え、新規Entry候補を最低3件抽出して記録する。"],
  ];
  if (memeStops.length) decisions.push(["Meme警戒", `${memeStops.map((p) => p.symbol).join(" / ")} は急落・流動性低下を優先確認。`]);
  document.getElementById("decisionBox").innerHTML = decisions
    .map((d) => `<div class="decision"><strong>${d[0]}</strong><span>${d[1]}</span></div>`)
    .join("");
}

function drawAssetChart(summary) {
  const canvas = document.getElementById("assetCanvas");
  const ctx = canvas.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  canvas.width = 720 * dpr;
  canvas.height = 300 * dpr;
  canvas.style.width = "100%";
  canvas.style.height = "auto";
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, 720, 300);
  const rows = [
    ["Core", summary.core.cash, summary.core.value, summary.core.pnl],
    ["Meme", summary.meme.cash, summary.meme.value, summary.meme.pnl],
  ];
  const max = Math.max(...rows.map((r) => r[1] + r[2]), TOTAL_CAPITAL) * 1.08;
  rows.forEach((row, i) => {
    const y = 72 + i * 92;
    const cashW = (row[1] / max) * 500;
    const investW = (row[2] / max) * 500;
    ctx.fillStyle = "#171a1f";
    ctx.font = "700 16px system-ui";
    ctx.fillText(row[0], 20, y + 18);
    ctx.fillStyle = "#d9e7df";
    ctx.fillRect(120, y, cashW, 26);
    ctx.fillStyle = "#255c99";
    ctx.fillRect(120 + cashW, y, investW, 26);
    ctx.fillStyle = "#68707d";
    ctx.font = "13px system-ui";
    ctx.fillText(`現金 ${yen(row[1])}`, 120, y + 50);
    ctx.fillText(`投資評価 ${yen(row[2])}`, 280, y + 50);
    ctx.fillStyle = row[3] >= 0 ? "#167d54" : "#b83232";
    ctx.fillText(`損益 ${yen(row[3])}`, 460, y + 50);
  });
}

function drawMoveChart(enriched) {
  const canvas = document.getElementById("moveCanvas");
  const ctx = canvas.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  canvas.width = 1100 * dpr;
  canvas.height = 280 * dpr;
  canvas.style.width = "100%";
  canvas.style.height = "auto";
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, 1100, 280);
  const data = enriched.filter((p) => Number.isFinite(p.change24h)).sort((a, b) => b.change24h - a.change24h);
  const maxAbs = Math.max(10, ...data.map((p) => Math.abs(p.change24h)));
  const zeroX = 550;
  ctx.strokeStyle = "#dde2dc";
  ctx.beginPath();
  ctx.moveTo(zeroX, 20);
  ctx.lineTo(zeroX, 252);
  ctx.stroke();
  data.slice(0, 14).forEach((p, i) => {
    const y = 26 + i * 17;
    const w = (Math.abs(p.change24h) / maxAbs) * 430;
    ctx.fillStyle = "#171a1f";
    ctx.font = "12px system-ui";
    ctx.fillText(p.symbol, 20, y + 10);
    ctx.fillStyle = p.change24h >= 0 ? "#167d54" : "#b83232";
    const x = p.change24h >= 0 ? zeroX : zeroX - w;
    ctx.fillRect(x, y, w, 11);
    ctx.fillStyle = "#68707d";
    ctx.fillText(`${pct(p.change24h)} / Vol ${compact(p.volume24h)}`, zeroX + 450, y + 10);
  });
}

function compact(value) {
  if (!Number.isFinite(value)) return "--";
  if (value >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(2)}B`;
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  return String(Math.round(value));
}

async function loadPrices() {
  const ids = [...new Set(positions.map((p) => p.id))].join(",");
  const url = `https://api.coingecko.com/api/v3/simple/price?ids=${ids}&vs_currencies=usd,jpy&include_24hr_change=true&include_24hr_vol=true`;
  const status = document.getElementById("apiStatus");
  status.textContent = "loading";
  try {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) throw new Error(`CoinGecko ${res.status}`);
    const data = await res.json();
    state.prices = { ...fallbackPrices, ...data };
    const solUsd = state.prices.solana?.usd;
    const solJpy = state.prices.solana?.jpy;
    if (solUsd && solJpy) state.usdJpy = solJpy / solUsd;
    state.loadedFromApi = true;
    status.textContent = "live";
    status.className = "pill good";
  } catch (error) {
    state.loadedFromApi = false;
    status.textContent = "fallback";
    status.className = "pill bad";
  }
  render();
}

function render() {
  const enriched = positions.map(enrichPosition);
  const summary = scenarioSummary(enriched);
  renderMetrics(summary);
  renderScenarioList(summary);
  renderPositions(enriched);
  renderRecommendations();
  renderDecision(summary, enriched);
  drawAssetChart(summary);
  drawMoveChart(enriched);
  const source = state.loadedFromApi ? "CoinGecko live" : "local fallback";
  const now = new Date();
  document.getElementById("lastUpdated").textContent = `${source} / ${now.toLocaleString("ja-JP", { timeZone: "Asia/Tokyo", hour12: false })} JST`;
}

document.getElementById("refreshBtn").addEventListener("click", loadPrices);
document.getElementById("lockSpecBtn").addEventListener("click", lockSpecEntries);

render();
loadPrices();

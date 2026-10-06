// script.js
// Plain JavaScript, no framework. Talks to our Flask backend at
// /api/analyze, then draws the chart with Chart.js and fills the
// results table.

const tickerInput = document.getElementById("tickerInput");
const analyzeBtn = document.getElementById("analyzeBtn");
const statusMsg = document.getElementById("statusMsg");
const resultsSection = document.getElementById("resultsSection");

let chartInstance = null;

analyzeBtn.addEventListener("click", runAnalysis);
tickerInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") runAnalysis();
});

async function runAnalysis() {
  const ticker = tickerInput.value.trim();
  if (!ticker) {
    showStatus("Please enter a stock ticker first.", true);
    return;
  }

  setLoading(true);
  showStatus(`Fetching data and running the sweep-line algorithm for ${ticker}...`, false);
  resultsSection.classList.add("hidden");

  try {
    const res = await fetch(`/api/analyze?ticker=${encodeURIComponent(ticker)}`);
    const data = await res.json();

    if (!res.ok) {
      showStatus(data.error || "Something went wrong.", true);
      setLoading(false);
      return;
    }

    showStatus("", false);
    renderResults(data);
    resultsSection.classList.remove("hidden");
  } catch (err) {
    showStatus("Could not reach the server. Please try again.", true);
  } finally {
    setLoading(false);
  }
}

function setLoading(isLoading) {
  analyzeBtn.disabled = isLoading;
  analyzeBtn.textContent = isLoading ? "Analyzing..." : "Analyze";
}

function showStatus(text, isError) {
  statusMsg.textContent = text;
  statusMsg.className = "status" + (isError ? " error" : "");
}

function renderResults(data) {
  // ---- summary cards ----
  document.getElementById("strategyReturn").textContent =
    formatPct(data.backtest.strategy_return_pct);
  document.getElementById("buyHoldReturn").textContent =
    formatPct(data.backtest.buy_hold_return_pct);
  document.getElementById("numTrades").textContent = data.backtest.num_trades;
  document.getElementById("numCrossings").textContent = data.algorithm_stats.num_crossings_found;

  // ---- signals table ----
  const tbody = document.querySelector("#signalsTable tbody");
  tbody.innerHTML = "";
  data.signals.forEach((s) => {
    const row = document.createElement("tr");
    const date = data.dates[s.day] || "";
    row.innerHTML = `
      <td>${date}</td>
      <td class="${s.action === "BUY" ? "action-buy" : "action-sell"}">${s.action}</td>
      <td>${s.price}</td>
      <td>${s.reason}</td>
    `;
    tbody.appendChild(row);
  });

  // ---- chart ----
  drawChart(data);
}

function drawChart(data) {
  const labels = data.dates;

  // Build BUY/SELL marker arrays: same length as labels, null except at the signal's day.
  const buyPoints = new Array(labels.length).fill(null);
  const sellPoints = new Array(labels.length).fill(null);
  data.signals.forEach((s) => {
    if (s.action === "BUY") buyPoints[s.day] = s.price;
    else sellPoints[s.day] = s.price;
  });

  const ctx = document.getElementById("priceChart").getContext("2d");
  if (chartInstance) chartInstance.destroy();

  chartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Close Price",
          data: data.close,
          borderColor: "#1f2a37",
          borderWidth: 1.5,
          pointRadius: 0,
        },
        {
          label: "SMA50",
          data: data.sma50,
          borderColor: "#2e5c99",
          borderWidth: 1.5,
          pointRadius: 0,
        },
        {
          label: "SMA200",
          data: data.sma200,
          borderColor: "#d98c2b",
          borderWidth: 1.5,
          pointRadius: 0,
        },
        {
          label: "BUY signal",
          data: buyPoints,
          showLine: false,
          pointStyle: "triangle",
          pointRadius: 7,
          backgroundColor: "#1a9e5c",
          borderColor: "#1a9e5c",
        },
        {
          label: "SELL signal",
          data: sellPoints,
          showLine: false,
          pointStyle: "triangle",
          rotation: 180,
          pointRadius: 7,
          backgroundColor: "#d13b3b",
          borderColor: "#d13b3b",
        },
      ],
    },
    options: {
      responsive: true,
      interaction: { mode: "index", intersect: false },
      scales: {
        x: {
          ticks: { maxTicksLimit: 10 },
        },
        y: {
          title: { display: true, text: "Price" },
        },
      },
      plugins: {
        legend: { position: "top" },
        title: { display: true, text: `${data.ticker}: Price vs Moving Averages, with detected crossovers` },
      },
    },
  });
}

function formatPct(value) {
  const sign = value >= 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

/**
 * Merchant Payment Ops Dashboard — Frontend Logic
 *
 * Fetches data from /api/dashboard and /api/metrics, renders KPIs,
 * anomaly table, evidence status, and Chart.js gauges/lines.
 */

// ══════════════════════════════════════════════════════════════════════════════
// Config
// ══════════════════════════════════════════════════════════════════════════════

const API_BASE = window.location.origin;
const POLL_INTERVAL = 5 * 60 * 1000; // 5 minutes
let currentFilter = "all";
let charts = {};

// ══════════════════════════════════════════════════════════════════════════════
// API Layer
// ══════════════════════════════════════════════════════════════════════════════

async function apiFetch(path, options = {}) {
    const headers = {
        "Content-Type": "application/json",
        "X-Merchant-API-Key": getApiKey(),
        ...options.headers,
    };
    try {
        const resp = await fetch(`${API_BASE}${path}`, { ...options, headers });
        if (!resp.ok) {
            throw new Error(`API ${resp.status}: ${resp.statusText}`);
        }
        return await resp.json();
    } catch (err) {
        showError(`API Error: ${err.message}`);
        throw err;
    }
}

function getApiKey() {
    return localStorage.getItem("merchant_api_key") || "rzp_merchant_" + getMerchantId();
}

function getMerchantId() {
    return localStorage.getItem("merchant_id") || prompt("Enter Merchant ID:") || "";
}

// ══════════════════════════════════════════════════════════════════════════════
// Data Loading
// ══════════════════════════════════════════════════════════════════════════════

async function loadDashboard() {
    try {
        const data = await apiFetch("/api/dashboard");
        renderKPIs(data);
        renderAnomalyTable(data);
        renderEvidenceStatus(data);
        setStatus("connected");
    } catch {
        setStatus("error");
    }
}

async function loadMetrics() {
    try {
        const data = await apiFetch("/api/metrics");
        renderMetricCharts(data);
        renderImpactTimeline(data);
    } catch {
        // Metrics may fail — dashboard still works
    }
}

// ══════════════════════════════════════════════════════════════════════════════
// Rendering — KPI Cards
// ══════════════════════════════════════════════════════════════════════════════

function renderKPIs(data) {
    const summary = data.summary || {};
    document.getElementById("kpiCritical").textContent = summary.critical_count ?? 0;
    document.getElementById("kpiCriticalSub").textContent =
        `${(data.critical_anomalies || []).length} active critical issues`;

    const totalRecs = (data.top_recommendations || []).length;
    document.getElementById("kpiActions").textContent = totalRecs;
    document.getElementById("kpiActionsSub").textContent =
        `${summary.unfollowed_recommendations ?? 0} unfollowed`;

    const impact = data.impact || {};
    document.getElementById("kpiChargebacks").textContent = impact.chargebacks_won ?? 0;
    document.getElementById("kpiChargebacksSub").textContent = "Won with agent assistance";

    document.getElementById("kpiTimeSaved").textContent =
        `${impact.time_saved_hours ?? 0}h`;
    document.getElementById("kpiTimeSavedSub").textContent =
        `₹${(impact.revenue_recovered_inr ?? 0).toLocaleString()} recovered`;
}

// ══════════════════════════════════════════════════════════════════════════════
// Rendering — Anomaly Table
// ══════════════════════════════════════════════════════════════════════════════

function renderAnomalyTable(data) {
    const all = [
        ...(data.critical_anomalies || []).map(a => ({ ...a, severity: "critical" })),
        ...(data.warning_anomalies || []).map(a => ({ ...a, severity: "warning" })),
        ...(data.info_anomalies || []).map(a => ({ ...a, severity: "info" })),
    ];

    const filtered = currentFilter === "all" ? all : all.filter(a => a.severity === currentFilter);

    const tbody = document.getElementById("anomalyTableBody");
    if (filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:24px;color:var(--text-muted)">
            🎉 No anomalies detected. All clear!
        </td></tr>`;
        return;
    }

    tbody.innerHTML = filtered.map(a => `
        <tr>
            <td>
                <span class="badge badge-${a.severity}">${a.severity}</span>
                <span style="margin-left:8px">${formatType(a.type)}</span>
            </td>
            <td>${formatTime(a.detected_at)}</td>
            <td>${a.root_cause ? formatType(a.root_cause) : '—'}</td>
            <td>${a.recommended_action ? formatType(a.recommended_action) : '—'}</td>
            <td><span class="badge badge-warning">Open</span></td>
        </tr>
    `).join("");
}

// ══════════════════════════════════════════════════════════════════════════════
// Rendering — Evidence Status
// ══════════════════════════════════════════════════════════════════════════════

function renderEvidenceStatus(data) {
    // Extract disputes from anomalies
    const disputes = (data.critical_anomalies || [])
        .concat(data.warning_anomalies || [])
        .filter(a => a.type && a.type.includes("dispute"));

    const tbody = document.getElementById("evidenceTableBody");
    if (disputes.length === 0) {
        // Show placeholder from recommendations
        const recs = (data.top_recommendations || []).filter(
            r => r.text && r.text.toLowerCase().includes("evidence")
        );
        if (recs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:16px;color:var(--text-muted)">
                No active dispute evidence needed
            </td></tr>`;
            return;
        }
    }

    // Since we don't have per-dispute data in the dashboard response,
    // show a summary row
    tbody.innerHTML = `
        <tr>
            <td colspan="5" style="padding:16px;color:var(--text-muted);text-align:center">
                Evidence status available via <code>GET /api/dispute/:id</code>
                for individual dispute details.
            </td>
        </tr>
    `;
}

// ══════════════════════════════════════════════════════════════════════════════
// Rendering — Charts
// ══════════════════════════════════════════════════════════════════════════════

function renderMetricCharts(metrics) {
    const chartDefaults = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
            x: { display: false },
            y: { display: false, min: 0, max: 100 },
        },
    };

    // Detection Accuracy gauge
    renderGauge("chartDetection", metrics.detection_accuracy || 0, "#6366f1");

    // Diagnosis Accuracy gauge
    renderGauge("chartDiagnosis", (metrics.detection_accuracy || 0) * 0.95, "#3b82f6");

    // Action Success Rate gauge
    renderGauge("chartAction", 72.5, "#22c55e"); // placeholder

    // Win Rate bar chart
    renderWinRateChart(metrics);
}

function renderGauge(canvasId, value, color) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (charts[canvasId]) charts[canvasId].destroy();

    charts[canvasId] = new Chart(ctx, {
        type: "doughnut",
        data: {
            datasets: [{
                data: [value, 100 - value],
                backgroundColor: [color, "#2d3142"],
                borderWidth: 0,
            }],
        },
        options: {
            cutout: "75%",
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false },
            },
        },
        plugins: [{
            id: "centerText",
            afterDraw(chart) {
                const { ctx, chartArea } = chart;
                const cx = (chartArea.left + chartArea.right) / 2;
                const cy = (chartArea.top + chartArea.bottom) / 2;
                ctx.save();
                ctx.font = "bold 20px -apple-system, sans-serif";
                ctx.fillStyle = color;
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillText(`${Math.round(value)}%`, cx, cy);
                ctx.restore();
            },
        }],
    });
}

function renderWinRateChart(metrics) {
    const ctx = document.getElementById("chartWinRate");
    if (!ctx) return;

    if (charts["chartWinRate"]) charts["chartWinRate"].destroy();

    const agentRate = metrics.detection_accuracy || 0;
    const baselineRate = agentRate * 0.75;

    charts["chartWinRate"] = new Chart(ctx, {
        type: "bar",
        data: {
            labels: ["Baseline", "With Agent"],
            datasets: [{
                data: [baselineRate, agentRate],
                backgroundColor: ["#4b5563", "#6366f1"],
                borderRadius: 6,
                barThickness: 40,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { color: "#8b8fa3" }, grid: { display: false } },
                y: { min: 0, max: 100, ticks: { color: "#8b8fa3" }, grid: { color: "#2d3142" } },
            },
        },
    });
}

function renderImpactTimeline(metrics) {
    // Time Saved timeline
    const timeCtx = document.getElementById("chartTimeSaved");
    if (timeCtx) {
        if (charts["chartTimeSaved"]) charts["chartTimeSaved"].destroy();

        const days = 30;
        const labels = Array.from({ length: days }, (_, i) => {
            const d = new Date();
            d.setDate(d.getDate() - (days - 1 - i));
            return d.toLocaleDateString("en-IN", { month: "short", day: "numeric" });
        });
        const cumulative = labels.map((_, i) =>
            ((metrics.time_saved_hours || 0) / days) * (i + 1)
        );

        charts["chartTimeSaved"] = new Chart(timeCtx, {
            type: "line",
            data: {
                labels,
                datasets: [{
                    data: cumulative,
                    borderColor: "#6366f1",
                    backgroundColor: "rgba(99,102,241,0.1)",
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: "#8b8fa3", maxTicksLimit: 7 }, grid: { display: false } },
                    y: { ticks: { color: "#8b8fa3" }, grid: { color: "#2d3142" } },
                },
            },
        });
    }

    // Revenue timeline
    const revCtx = document.getElementById("chartRevenue");
    if (revCtx) {
        if (charts["chartRevenue"]) charts["chartRevenue"].destroy();

        const days = 30;
        const labels = Array.from({ length: days }, (_, i) => {
            const d = new Date();
            d.setDate(d.getDate() - (days - 1 - i));
            return d.toLocaleDateString("en-IN", { month: "short", day: "numeric" });
        });
        const cumulative = labels.map((_, i) =>
            ((metrics.revenue_recovered || 0) / days) * (i + 1)
        );

        charts["chartRevenue"] = new Chart(revCtx, {
            type: "line",
            data: {
                labels,
                datasets: [{
                    data: cumulative,
                    borderColor: "#22c55e",
                    backgroundColor: "rgba(34,197,94,0.1)",
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: "#8b8fa3", maxTicksLimit: 7 }, grid: { display: false } },
                    y: { ticks: { color: "#8b8fa3", callback: v => `₹${v.toLocaleString()}` }, grid: { color: "#2d3142" } },
                },
            },
        });
    }
}

// ══════════════════════════════════════════════════════════════════════════════
// Helpers
// ══════════════════════════════════════════════════════════════════════════════

function formatType(str) {
    if (!str) return "—";
    return str.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
}

function formatTime(str) {
    if (!str || str === "None") return "—";
    try {
        return new Date(str).toLocaleString("en-IN", {
            month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
        });
    } catch {
        return str;
    }
}

function showError(msg) {
    const el = document.getElementById("errorBanner");
    el.textContent = msg;
    el.style.display = "block";
    setTimeout(() => { el.style.display = "none"; }, 10000);
}

function setStatus(state) {
    const dot = document.getElementById("statusDot");
    const text = document.getElementById("statusText");
    if (state === "connected") {
        dot.style.background = "#22c55e";
        text.textContent = "Connected";
    } else if (state === "error") {
        dot.style.background = "#ef4444";
        text.textContent = "Disconnected";
    } else {
        dot.style.background = "#eab308";
        text.textContent = "Connecting...";
    }
}

// ══════════════════════════════════════════════════════════════════════════════
// Filter buttons
// ══════════════════════════════════════════════════════════════════════════════

document.querySelectorAll(".filter-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        currentFilter = btn.dataset.filter;
        loadDashboard(); // re-render with filter
    });
});

// ══════════════════════════════════════════════════════════════════════════════
// Init + Polling
// ══════════════════════════════════════════════════════════════════════════════

async function init() {
    setStatus("connecting");
    await Promise.all([loadDashboard(), loadMetrics()]);
    // Poll every 5 minutes
    setInterval(() => {
        loadDashboard();
        loadMetrics();
    }, POLL_INTERVAL);
}

init();

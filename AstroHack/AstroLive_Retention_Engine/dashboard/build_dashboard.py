"""
Builds a single self-contained HTML file: the AI Growth Dashboard.
Reads outputs/growth_metrics.json and outputs/churn_predictions.json and
bakes them into the page as embedded JSON, then renders KPI tiles, a
monthly trend chart, a risk-tier breakdown, a feature-importance chart,
a top-astrologers table, and a filterable churn-risk user table — all in
vanilla HTML/CSS/JS (no external chart lib).
"""
import json

with open("/root/astrolive/outputs/growth_metrics.json") as f:
    metrics = json.load(f)
with open("/root/astrolive/outputs/churn_predictions.json") as f:
    predictions = json.load(f)

# only ship the fields the table/detail view actually needs, to keep the file lean
slim_predictions = [{
    "user_id": p["user_id"],
    "risk_tier": p["risk_tier"],
    "churn_probability": p["churn_probability"],
    "days_since_last_consultation": p["days_since_last_consultation"],
    "num_consultations": p["num_consultations"],
    "total_spent": p["total_spent"],
    "last_topic": p["last_topic"],
    "reasons": p["reasons"],
    "recommended_action": p["recommended_action"],
    "suggested_followup_date": p["suggested_followup_date"],
    "followup_due": p["followup_due"],
} for p in predictions]

embedded = {
    "metrics": metrics,
    "predictions": slim_predictions,
}

DATA_JSON = json.dumps(embedded)

HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AstroLive — AI Growth Dashboard</title>
<style>
  .viz-root {
    color-scheme: light;
    --surface-1:      #fcfcfb;
    --page:           #f9f9f7;
    --text-primary:   #0b0b0b;
    --text-secondary: #52514e;
    --text-muted:     #898781;
    --grid:           #e1e0d9;
    --baseline:       #c3c2b7;
    --border:         rgba(11,11,11,0.10);
    --series-1:       #2a78d6;
    --series-2:       #eb6834;
    --series-3:       #1baf7a;
    --series-4:       #eda100;
    --status-good:    #0ca30c;
    --status-warning: #fab219;
    --status-critical:#d03b3b;
    --seq-100: #cde2fb; --seq-250: #86b6ef; --seq-450: #2a78d6; --seq-600: #184f95;
  }
  :root[data-theme="dark"] .viz-root, .viz-root[data-theme="dark"] {
    color-scheme: dark;
    --surface-1:      #1a1a19;
    --page:           #0d0d0d;
    --text-primary:   #ffffff;
    --text-secondary: #c3c2b7;
    --text-muted:     #898781;
    --grid:           #2c2c2a;
    --baseline:       #383835;
    --border:         rgba(255,255,255,0.10);
    --series-1:       #3987e5;
    --series-2:       #d95926;
    --series-3:       #199e70;
    --series-4:       #c98500;
    --status-good:    #0ca30c;
    --status-warning: #fab219;
    --status-critical:#e66767;
    --seq-100: #184f95; --seq-250: #256abf; --seq-450: #3987e5; --seq-600: #9ec5f4;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; }
  body {
    background: var(--page);
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
    color: var(--text-primary);
  }
  .wrap { max-width: 1180px; margin: 0 auto; padding: 28px 20px 64px; }
  header.top { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 22px; }
  .title { font-size: 22px; font-weight: 650; margin: 0 0 4px; }
  .subtitle { color: var(--text-secondary); font-size: 13.5px; margin: 0; }
  .toggle {
    border: 1px solid var(--border); background: var(--surface-1); color: var(--text-secondary);
    border-radius: 8px; padding: 7px 12px; font-size: 12.5px; cursor: pointer;
  }
  .card {
    background: var(--surface-1); border: 1px solid var(--border); border-radius: 14px;
    padding: 18px 20px;
  }
  section { margin-bottom: 22px; }
  h2.section-title { font-size: 14px; font-weight: 650; margin: 0 0 12px; color: var(--text-primary); }
  .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
  @media (max-width: 900px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }
  .kpi { background: var(--surface-1); border: 1px solid var(--border); border-radius: 14px; padding: 16px 18px; }
  .kpi .label { font-size: 12px; color: var(--text-secondary); margin-bottom: 8px; }
  .kpi .value { font-size: 26px; font-weight: 650; letter-spacing: -0.01em; }
  .kpi .delta { font-size: 12px; margin-top: 6px; color: var(--text-muted); }
  .kpi .delta.risk { color: var(--status-critical); font-weight: 600; }
  .grid-2 { display: grid; grid-template-columns: 1.3fr 1fr; gap: 16px; }
  @media (max-width: 900px) { .grid-2 { grid-template-columns: 1fr; } }
  svg text { font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }
  .axis-label { fill: var(--text-muted); font-size: 11px; }
  .grid-line { stroke: var(--grid); stroke-width: 1; }
  .baseline { stroke: var(--baseline); stroke-width: 1; }
  .legend { display: flex; gap: 16px; flex-wrap: wrap; margin-top: 10px; font-size: 12px; color: var(--text-secondary); }
  .legend .swatch { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 6px; vertical-align: -1px; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { text-align: left; padding: 9px 10px; border-bottom: 1px solid var(--border); }
  th { color: var(--text-muted); font-weight: 600; font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.02em; }
  td { color: var(--text-primary); }
  .badge { display: inline-flex; align-items: center; gap: 5px; padding: 3px 9px; border-radius: 999px; font-size: 12px; font-weight: 600; }
  .badge.high { background: color-mix(in srgb, var(--status-critical) 14%, transparent); color: var(--status-critical); }
  .badge.medium { background: color-mix(in srgb, var(--status-warning) 18%, transparent); color: #8a5a00; }
  :root[data-theme="dark"] .badge.medium, .viz-root[data-theme="dark"] .badge.medium { color: var(--status-warning); }
  .badge.low { background: color-mix(in srgb, var(--status-good) 14%, transparent); color: var(--status-good); }
  .reasons { color: var(--text-secondary); font-size: 12px; }
  .controls { display: flex; gap: 8px; align-items: center; margin-bottom: 12px; flex-wrap: wrap; }
  .controls select, .controls input {
    background: var(--surface-1); border: 1px solid var(--border); color: var(--text-primary);
    border-radius: 8px; padding: 7px 10px; font-size: 12.5px; font-family: inherit;
  }
  .controls .count { color: var(--text-muted); font-size: 12px; margin-left: auto; }
  .tbl-scroll { max-height: 420px; overflow-y: auto; }
  .fi-row { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
  .fi-label { width: 190px; font-size: 12.5px; color: var(--text-secondary); flex-shrink: 0; }
  .fi-track { flex: 1; height: 10px; background: var(--grid); border-radius: 5px; overflow: hidden; }
  .fi-fill { height: 100%; background: var(--seq-450); border-radius: 5px; }
  .fi-val { width: 46px; text-align: right; font-size: 12px; color: var(--text-muted); font-variant-numeric: tabular-nums; }
  .tooltip {
    position: fixed; pointer-events: none; background: var(--text-primary); color: var(--surface-1);
    font-size: 11.5px; padding: 6px 9px; border-radius: 7px; opacity: 0; transition: opacity 0.08s;
    z-index: 50; white-space: nowrap;
  }
  footer.note { color: var(--text-muted); font-size: 11.5px; margin-top: 26px; line-height: 1.6; }
</style>
</head>
<body>
<div class="viz-root">
<div class="wrap">

  <header class="top">
    <div>
      <p class="title">AstroLive — AI Growth Dashboard</p>
      <p class="subtitle" id="asof"></p>
    </div>
    <button class="toggle" id="theme-toggle">🌙 Dark mode</button>
  </header>

  <section>
    <div class="kpi-grid" id="kpi-grid"></div>
  </section>

  <section class="grid-2">
    <div class="card">
      <h2 class="section-title">Consultation volume, last 9 months</h2>
      <div id="trend-chart"></div>
      <div class="legend">* current month, partial (data through the 15th)</div>
    </div>
    <div class="card">
      <h2 class="section-title">Users by churn-risk tier</h2>
      <div id="risk-chart"></div>
      <div class="legend" id="risk-legend"></div>
    </div>
  </section>

  <section class="grid-2">
    <div class="card">
      <h2 class="section-title">What drives the churn prediction (model feature importance)</h2>
      <div id="fi-chart"></div>
      <div class="legend" id="model-quality"></div>
    </div>
    <div class="card">
      <h2 class="section-title">Best-performing astrologers</h2>
      <table>
        <thead><tr><th>Astrologer</th><th>Specialization</th><th>Sessions</th><th>Rating</th><th>Repeat %</th></tr></thead>
        <tbody id="astro-tbody"></tbody>
      </table>
    </div>
  </section>

  <section>
    <div class="card">
      <h2 class="section-title">Churn-risk users &amp; recommended actions</h2>
      <div class="controls">
        <select id="filter-tier">
          <option value="all">All risk tiers</option>
          <option value="high">High risk</option>
          <option value="medium">Medium risk</option>
          <option value="low">Low risk</option>
        </select>
        <select id="filter-followup">
          <option value="all">All follow-up timing</option>
          <option value="due">Follow-up due within 7 days</option>
        </select>
        <input id="filter-search" type="text" placeholder="Search user id…">
        <span class="count" id="row-count"></span>
      </div>
      <div class="tbl-scroll">
        <table>
          <thead>
            <tr>
              <th>User</th><th>Risk</th><th>Last topic</th><th>Last consult</th>
              <th>Consultations</th><th>Spent</th><th>Reasons</th><th>Suggested action</th>
            </tr>
          </thead>
          <tbody id="user-tbody"></tbody>
        </table>
      </div>
    </div>
  </section>

  <footer class="note">
    Prototype dashboard — data is synthetically generated to model realistic AstroLive usage patterns (no real user data was used).
    Churn model: gradient boosting classifier trained on forward-looking 30-day inactivity labels, held-out accuracy and ROC-AUC shown above.
  </footer>

</div>
</div>
<div class="tooltip" id="tooltip"></div>

<script id="app-data" type="application/json">__DATA_JSON__</script>
<script>
const DATA = JSON.parse(document.getElementById('app-data').textContent);
const M = DATA.metrics;
const PRED = DATA.predictions;
const root = document.querySelector('.viz-root');
const css = getComputedStyle(root);
const v = (name) => css.getPropertyValue(name).trim();

document.getElementById('asof').textContent = `As of ${M.as_of_date} · ${M.kpis.total_users.toLocaleString()} users tracked`;

// ---------- theme toggle ----------
const toggleBtn = document.getElementById('theme-toggle');
toggleBtn.addEventListener('click', () => {
  const isDark = root.getAttribute('data-theme') === 'dark';
  root.setAttribute('data-theme', isDark ? 'light' : 'dark');
  toggleBtn.textContent = isDark ? '🌙 Dark mode' : '☀️ Light mode';
});

// ---------- KPI tiles ----------
function fmtCompact(n) {
  if (n >= 1e6) return (n/1e6).toFixed(1) + 'M';
  if (n >= 1e3) return (n/1e3).toFixed(1) + 'K';
  return Math.round(n).toLocaleString();
}
const kpis = [
  { label: 'Total users', value: M.kpis.total_users.toLocaleString(), delta: 'tracked in the platform' },
  { label: 'Conversion rate', value: M.kpis.conversion_rate_pct + '%', delta: 'free trial → paid consult' },
  { label: 'Repeat consultation rate', value: M.kpis.repeat_consultation_rate_pct + '%', delta: 'users with 2+ consultations' },
  { label: 'Revenue per user', value: '₹' + fmtCompact(M.kpis.revenue_per_user), delta: '₹' + fmtCompact(M.kpis.total_revenue) + ' total revenue' },
  { label: 'Churn-risk users', value: M.kpis.churn_risk_users.toLocaleString(), delta: M.kpis.churn_risk_pct + '% of user base', risk: true },
  { label: 'Revenue at risk (30d)', value: '₹' + fmtCompact(M.kpis.revenue_at_risk), delta: 'est. repeat spend if no action taken', risk: true },
  { label: 'Model accuracy (held-out)', value: (M.model_metrics.accuracy*100).toFixed(1) + '%', delta: 'ROC-AUC ' + M.model_metrics.roc_auc.toFixed(2) },
  { label: 'Best-performing astrologer rating', value: (M.top_astrologers[0] ? M.top_astrologers[0].avg_rating.toFixed(2) : '—') + ' ★', delta: M.top_astrologers[0] ? M.top_astrologers[0].name : '' },
];
document.getElementById('kpi-grid').innerHTML = kpis.map(k => `
  <div class="kpi">
    <div class="label">${k.label}</div>
    <div class="value">${k.value}</div>
    <div class="delta ${k.risk ? 'risk' : ''}">${k.delta}</div>
  </div>
`).join('');

// ---------- tooltip helper ----------
const tip = document.getElementById('tooltip');
function showTip(evt, html) {
  tip.innerHTML = html;
  tip.style.left = (evt.clientX + 14) + 'px';
  tip.style.top = (evt.clientY + 14) + 'px';
  tip.style.opacity = 1;
}
function hideTip() { tip.style.opacity = 0; }

// ---------- monthly trend line chart ----------
function trendChart() {
  const data = M.monthly_trend;
  const w = 520, h = 200, padL = 36, padR = 12, padT = 14, padB = 24;
  const xs = data.map((d,i) => padL + i * (w - padL - padR) / (data.length - 1));
  const maxY = Math.max(...data.map(d => d.consultations)) * 1.15;
  const y = (val) => padT + (h - padT - padB) * (1 - val / maxY);
  const ticks = [0, Math.round(maxY*0.5/50)*50, Math.round(maxY/50)*50];

  let gridSvg = ticks.map(t => `
    <line class="grid-line" x1="${padL}" x2="${w-padR}" y1="${y(t)}" y2="${y(t)}"></line>
    <text class="axis-label" x="4" y="${y(t)+4}">${t}</text>
  `).join('');

  const pathD = data.map((d,i) => `${i===0?'M':'L'} ${xs[i]} ${y(d.consultations)}`).join(' ');
  const dots = data.map((d,i) => `
    <circle cx="${xs[i]}" cy="${y(d.consultations)}" r="4" fill="${v('--series-1')}" stroke="${v('--surface-1')}" stroke-width="2"
      data-tip="${d.month}: ${d.consultations} consultations"></circle>
  `).join('');
  const xLabels = data.map((d,i) => i % Math.ceil(data.length/6) === 0 ? `<text class="axis-label" x="${xs[i]}" y="${h-6}" text-anchor="middle">${d.month.slice(5)}</text>` : '').join('');
  const lastIdx = data.length - 1;
  const lastLabel = `<text x="${xs[lastIdx]-10}" y="${y(data[lastIdx].consultations)-12}" text-anchor="end" font-size="12" font-weight="600" fill="${v('--text-primary')}">${data[lastIdx].consultations}${'*'}</text>`;

  const svg = `<svg width="100%" viewBox="0 0 ${w} ${h}" style="overflow:visible">
    <line class="baseline" x1="${padL}" x2="${w-padR}" y1="${y(0)}" y2="${y(0)}"></line>
    ${gridSvg}
    <path d="${pathD}" fill="none" stroke="${v('--series-1')}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"></path>
    ${dots}
    ${xLabels}
    ${lastLabel}
  </svg>`;
  const el = document.getElementById('trend-chart');
  el.innerHTML = svg;
  el.querySelectorAll('circle').forEach(c => {
    c.addEventListener('mousemove', (e) => showTip(e, c.dataset.tip));
    c.addEventListener('mouseleave', hideTip);
  });
}
trendChart();

// ---------- risk tier horizontal bar (status colors) ----------
function riskChart() {
  const dist = M.risk_distribution;
  const total = dist.low + dist.medium + dist.high;
  const tiers = [
    { key: 'low', label: 'Low risk', icon: '✅', color: v('--status-good') },
    { key: 'medium', label: 'Medium risk', icon: '⚠️', color: v('--status-warning') },
    { key: 'high', label: 'High risk', icon: '🚨', color: v('--status-critical') },
  ];
  const w = 480, barH = 22, gap = 14, padL = 100, padR = 60;
  const maxV = Math.max(...tiers.map(t => dist[t.key])) * 1.1;
  let y = 10;
  let bars = '';
  tiers.forEach(t => {
    const val = dist[t.key];
    const barW = (val / maxV) * (w - padL - padR);
    bars += `
      <text class="axis-label" x="${padL - 10}" y="${y + barH/2 + 4}" text-anchor="end" fill="${v('--text-secondary')}">${t.icon} ${t.label}</text>
      <rect x="${padL}" y="${y}" width="${Math.max(barW,2)}" height="${barH}" rx="4" fill="${t.color}"
        data-tip="${t.label}: ${val} users (${(val/total*100).toFixed(1)}%)"></rect>
      <text x="${padL + barW + 8}" y="${y + barH/2 + 4}" font-size="12" font-weight="600" fill="${v('--text-primary')}">${val}</text>
    `;
    y += barH + gap;
  });
  const h = y;
  const svg = `<svg width="100%" viewBox="0 0 ${w} ${h}" style="overflow:visible">${bars}</svg>`;
  const el = document.getElementById('risk-chart');
  el.innerHTML = svg;
  el.querySelectorAll('rect').forEach(r => {
    r.addEventListener('mousemove', (e) => showTip(e, r.dataset.tip));
    r.addEventListener('mouseleave', hideTip);
  });
  document.getElementById('risk-legend').innerHTML =
    `Out of ${total.toLocaleString()} users, <strong style="color:${v('--status-critical')}">${dist.high}</strong> are high risk and worth proactive outreach this week.`;
}
riskChart();

// ---------- feature importance ----------
function fiChart() {
  const fi = M.model_metrics.feature_importances;
  const entries = Object.entries(fi).slice(0, 8);
  const max = entries[0][1];
  const nice = {
    engagement_score: 'App engagement score',
    consultation_frequency: 'Consultation frequency',
    total_spent: 'Total amount spent',
    days_since_last_consultation: 'Days since last consultation',
    spend_trend: 'Spend trend',
    avg_session_duration: 'Avg. session duration',
    avg_rating_given: 'Avg. rating given',
    distinct_astrologers: 'Distinct astrologers used',
    days_since_signup: 'Days since signup',
    num_consultations: 'Number of consultations',
    distinct_topics: 'Distinct topics',
    num_failed_calls: 'Failed calls',
  };
  const el = document.getElementById('fi-chart');
  el.innerHTML = entries.map(([k, val]) => `
    <div class="fi-row">
      <div class="fi-label">${nice[k] || k}</div>
      <div class="fi-track"><div class="fi-fill" style="width:${(val/max*100).toFixed(1)}%"></div></div>
      <div class="fi-val">${(val*100).toFixed(1)}%</div>
    </div>
  `).join('');
  document.getElementById('model-quality').innerHTML =
    `Held out on ${M.model_metrics.test_size} users · accuracy ${(M.model_metrics.accuracy*100).toFixed(1)}% · ROC-AUC ${M.model_metrics.roc_auc.toFixed(2)}`;
}
fiChart();

// ---------- top astrologers table ----------
document.getElementById('astro-tbody').innerHTML = M.top_astrologers.map(a => `
  <tr>
    <td>${a.name}</td>
    <td>${a.specialization}</td>
    <td>${a.sessions}</td>
    <td>${a.avg_rating.toFixed(2)} ★</td>
    <td>${a.repeat_rate_pct}%</td>
  </tr>
`).join('');

// ---------- churn-risk user table ----------
const tierEl = document.getElementById('filter-tier');
const followupEl = document.getElementById('filter-followup');
const searchEl = document.getElementById('filter-search');
const tbody = document.getElementById('user-tbody');
const rowCount = document.getElementById('row-count');

function renderUsers() {
  const tier = tierEl.value;
  const followup = followupEl.value;
  const q = searchEl.value.trim().toLowerCase();
  let rows = PRED.filter(p => p.risk_tier !== 'low' || tier === 'low' || tier === 'all');
  rows = PRED.filter(p => (tier === 'all' || p.risk_tier === tier)
    && (followup === 'all' || (followup === 'due' && p.followup_due))
    && (q === '' || p.user_id.toLowerCase().includes(q)));
  rows = rows.sort((a,b) => b.churn_probability - a.churn_probability).slice(0, 200);
  rowCount.textContent = `${rows.length.toLocaleString()} of ${PRED.length.toLocaleString()} shown`;
  tbody.innerHTML = rows.map(p => `
    <tr>
      <td>${p.user_id}</td>
      <td><span class="badge ${p.risk_tier}">${(p.churn_probability*100).toFixed(0)}%</span></td>
      <td>${p.last_topic}</td>
      <td>${p.days_since_last_consultation}d ago</td>
      <td>${p.num_consultations}</td>
      <td>₹${Math.round(p.total_spent)}</td>
      <td class="reasons">${p.reasons.join(', ')}</td>
      <td>${p.recommended_action.icon} ${p.recommended_action.label}</td>
    </tr>
  `).join('');
}
[tierEl, followupEl].forEach(el => el.addEventListener('change', renderUsers));
searchEl.addEventListener('input', renderUsers);
renderUsers();
</script>
</body>
</html>
"""

HTML = HTML.replace("__DATA_JSON__", DATA_JSON)

with open("/root/astrolive/dashboard/growth_dashboard.html", "w") as f:
    f.write(HTML)

print(f"Wrote dashboard: /root/astrolive/dashboard/growth_dashboard.html ({len(HTML)/1024:.0f} KB)")

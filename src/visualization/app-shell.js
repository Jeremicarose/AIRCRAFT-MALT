function defaultApiUrl() {
  if (window.location.protocol === 'http:' || window.location.protocol === 'https:') {
    return window.location.origin;
  }
  return 'http://localhost:5051';
}

async function fetchJson(path) {
  const response = await fetch(`${defaultApiUrl()}${path}`);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status} for ${path}`);
  }
  return response.json();
}

function markActiveNav() {
  const current = document.body.dataset.appPage;
  document.querySelectorAll('[data-app-nav]').forEach((link) => {
    if (link.dataset.appNav === current) {
      link.classList.add('active');
      link.setAttribute('aria-current', 'page');
    } else {
      link.classList.remove('active');
      link.removeAttribute('aria-current');
    }
  });
}

function prepareCommandBar() {
  const labels = {
    overview: 'Overview',
    aircraft: 'Aircraft',
    receivers: 'Receivers',
    localization: 'Live map',
    pipeline: 'Pipeline',
    analytics: 'Metrics',
    settings: 'Settings',
  };
  document.querySelectorAll('[data-app-nav]').forEach((link) => {
    const label = labels[link.dataset.appNav];
    const text = link.querySelector('span');
    if (label && text) text.textContent = label;
  });

  const brand = document.querySelector('.app-brand');
  if (brand) {
    brand.innerHTML = `
      <div class="app-brand-mark" aria-hidden="true">⌁</div>
      <div><strong>MLAT / Airspace</strong><span>Receiver control plane</span></div>
    `;
  }
}

function setShellMetric(id, value, detail) {
  const valueNode = document.querySelector(`[data-shell-value="${id}"]`);
  const detailNode = document.querySelector(`[data-shell-detail="${id}"]`);
  if (valueNode) valueNode.textContent = value;
  if (detailNode && detail) detailNode.textContent = detail;
}

function shellEscape(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function shellNumber(value, digits = 0, fallback = 'n/a') {
  if (!Number.isFinite(Number(value))) return fallback;
  const number = Number(value);
  return digits > 0 ? number.toFixed(digits) : Math.round(number).toLocaleString();
}

function shellPercent(value, fallback = 'n/a') {
  if (!Number.isFinite(Number(value))) return fallback;
  return `${Math.round(Number(value) * 100)}%`;
}

function shellRelativeTime(timestamp) {
  if (!Number.isFinite(Number(timestamp))) return 'n/a';
  const seconds = Math.max(0, Math.round((Date.now() / 1000) - Number(timestamp)));
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m ago`;
  return `${Math.round(seconds / 3600)}h ago`;
}

function shellAgeSeconds(timestamp) {
  if (!Number.isFinite(Number(timestamp))) return null;
  return Math.max(0, (Date.now() / 1000) - Number(timestamp));
}

function shellToneFromScore(score) {
  if (!Number.isFinite(Number(score))) return 'tone-neutral';
  if (Number(score) >= 0.8) return 'tone-good';
  if (Number(score) >= 0.55) return 'tone-warn';
  return 'tone-risk';
}

function shellToneFromFreshness(ageSeconds, warnAt = 30, riskAt = 120) {
  if (!Number.isFinite(Number(ageSeconds))) return 'tone-neutral';
  if (Number(ageSeconds) <= warnAt) return 'tone-good';
  if (Number(ageSeconds) <= riskAt) return 'tone-warn';
  return 'tone-risk';
}

function shellHealthBadge(label, tone) {
  return `<span class="health-badge ${shellEscape(tone)}">${shellEscape(label)}</span>`;
}

function shellMiniBar(label, valueText, ratio, tone = 'tone-good') {
  const clamped = Math.max(0, Math.min(1, Number(ratio) || 0));
  return `
    <div class="mini-bar-row ${shellEscape(tone)}">
      <div class="mini-bar-copy"><strong>${shellEscape(label)}</strong><span>${shellEscape(valueText)}</span></div>
      <div class="mini-bar-track"><span style="width:${(clamped * 100).toFixed(1)}%"></span></div>
    </div>
  `;
}

function shellSparkline(points, options = {}) {
  const width = options.width || 240;
  const height = options.height || 72;
  const strokeClass = options.strokeClass || 'chart-line';
  const values = points
    .map((value) => Number(value))
    .filter((value) => Number.isFinite(value));
  if (!values.length) {
    return `<div class="chart-empty mini-sparkline-empty">No recent data</div>`;
  }
  if (values.length === 1) {
    const y = height / 2;
    return `
      <svg class="mini-sparkline" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" aria-hidden="true">
        <line class="chart-grid-line" x1="0" y1="${y}" x2="${width}" y2="${y}"></line>
        <circle class="${shellEscape(strokeClass)} mini-sparkline-dot" cx="${width / 2}" cy="${y}" r="3"></circle>
      </svg>
    `;
  }
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const path = values.map((value, index) => {
    const x = (index / (values.length - 1)) * width;
    const y = height - (((value - min) / span) * (height - 10) + 5);
    return `${index === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)}`;
  }).join(' ');
  return `
    <svg class="mini-sparkline" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" aria-hidden="true">
      <line class="chart-grid-line" x1="0" y1="${height - 1}" x2="${width}" y2="${height - 1}"></line>
      <path class="${shellEscape(strokeClass)}" d="${path}"></path>
    </svg>
  `;
}

function getSelectionParam(key) {
  return new URLSearchParams(window.location.search).get(key);
}

function setSelectionParam(key, value) {
  const url = new URL(window.location.href);
  if (value) {
    url.searchParams.set(key, value);
  } else {
    url.searchParams.delete(key);
  }
  window.history.replaceState({}, '', url);
}

function filterByQuery(items, query, projector) {
  if (!query) return items;
  const normalized = String(query).trim().toLowerCase();
  if (!normalized) return items;
  return items.filter((item) => String(projector(item) || '').toLowerCase().includes(normalized));
}

window.setShellMetric = setShellMetric;
window.shellEscape = shellEscape;
window.shellNumber = shellNumber;
window.shellPercent = shellPercent;
window.shellRelativeTime = shellRelativeTime;
window.shellAgeSeconds = shellAgeSeconds;
window.shellToneFromScore = shellToneFromScore;
window.shellToneFromFreshness = shellToneFromFreshness;
window.shellHealthBadge = shellHealthBadge;
window.shellMiniBar = shellMiniBar;
window.shellSparkline = shellSparkline;
window.getSelectionParam = getSelectionParam;
window.setSelectionParam = setSelectionParam;
window.filterByQuery = filterByQuery;

function setShellMode(modeData) {
  const pill = document.getElementById('shell-mode-pill');
  const freshness = document.getElementById('shell-freshness-pill');
  if (!pill || !freshness) return;

  const isDemo = Boolean(modeData && modeData.demo_mode);
  const isSimulation = Boolean(modeData && (modeData.simulation_mode || modeData.synthetic_feed_mode));
  const isStrict = Boolean(modeData && modeData.strict_production_mode);
  const isLive = Boolean(modeData && modeData.runtime_status === 'active' && !isDemo && !isSimulation);

  if (!modeData) {
    pill.textContent = 'Mode unavailable';
    pill.className = 'status-pill mode-sim';
    freshness.textContent = 'Pending';
    return;
  }

  pill.textContent = isDemo
    ? (modeData.demo_label || 'Hosted walkthrough')
    : isSimulation
      ? 'Simulation mode'
      : isLive
        ? (isStrict ? 'Strict live mode' : 'Live mode')
        : modeData.runtime_status === 'stale'
          ? (isStrict ? 'Strict runtime stale' : 'Runtime stale')
          : isStrict
            ? 'Strict live configured'
            : 'Live configured';
  pill.className = `status-pill ${isLive ? 'mode-live' : 'mode-sim'}`;
  freshness.textContent = modeData.runtime_status !== 'active'
    ? (isStrict ? 'Strict startup blocked until live runtime is available' : 'Processor unavailable')
    : modeData.benchmarkable_output
      ? 'Benchmarkable output'
      : modeData.synthetic_feed_mode
        ? 'Replay / synthetic feed'
        : 'Awaiting solved output';
}

function renderOverviewCards(target, cards) {
  target.innerHTML = cards.map((card) => `
    <article class="app-card">
      <span class="kicker">${card.kicker}</span>
      <h2>${card.title}</h2>
      <p>${card.copy}</p>
    </article>
  `).join('');
}

function renderSimpleList(target, rows, formatter) {
  target.innerHTML = rows.map(formatter).join('');
}

async function hydrateShell() {
  prepareCommandBar();
  markActiveNav();

  const [modeData, healthData, aircraftData, receiverData] = await Promise.all([
    fetchJson('/api/system/mode').catch(() => null),
    fetchJson('/api/health').catch(() => null),
    fetchJson('/api/aircraft?seconds=300').catch(() => null),
    fetchJson('/api/receivers').catch(() => null),
  ]);

  setShellMode(modeData);

  const aircraftCount = aircraftData ? aircraftData.count : 0;
  const receiverCount = receiverData ? receiverData.count : 0;
  const lastSignalAge = healthData && healthData.freshness ? healthData.freshness.last_signal_age_s : null;
  const healthStatus = healthData ? healthData.status : 'unknown';

  setShellMetric('aircraft', String(aircraftCount), aircraftCount ? 'Active in the last 5 minutes' : 'No aircraft currently active');
  setShellMetric('receivers', String(receiverCount), receiverCount ? 'Receivers visible to the runtime' : 'No receivers visible');
  setShellMetric(
    'freshness',
    lastSignalAge == null ? 'n/a' : `${Math.round(lastSignalAge)}s`,
    healthStatus === 'ok' ? 'Signal age from runtime health' : 'Health degraded or unavailable',
  );
  setShellMetric('status', healthStatus.toUpperCase(), 'Current API/runtime health state');

  const page = document.body.dataset.appPage;
  const hook = window.pageHydrators && window.pageHydrators[page];
  if (typeof hook === 'function') {
    await hook({ modeData, healthData, aircraftData, receiverData, fetchJson });
  }
}

window.pageHydrators = {};
window.addEventListener('DOMContentLoaded', () => {
  hydrateShell().catch((error) => {
    console.error('Failed to hydrate app shell', error);
  });
});
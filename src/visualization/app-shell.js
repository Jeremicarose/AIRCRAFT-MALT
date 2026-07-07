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

function setShellMetric(id, value, detail) {
  const valueNode = document.querySelector(`[data-shell-value="${id}"]`);
  const detailNode = document.querySelector(`[data-shell-detail="${id}"]`);
  if (valueNode) valueNode.textContent = value;
  if (detailNode && detail) detailNode.textContent = detail;
}

function setShellMode(modeData) {
  const pill = document.getElementById('shell-mode-pill');
  const freshness = document.getElementById('shell-freshness-pill');
  if (!pill || !freshness) return;

  const isDemo = Boolean(modeData && modeData.demo_mode);
  const isSimulation = Boolean(modeData && modeData.simulation_mode);
  const isLive = Boolean(modeData && !modeData.demo_mode && !modeData.simulation_mode);

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
      : 'Live mode';
  pill.className = `status-pill ${isLive ? 'mode-live' : 'mode-sim'}`;
  freshness.textContent = modeData.synthetic_feed_mode ? 'Replay / synthetic feed' : 'Benchmarkable feed';
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

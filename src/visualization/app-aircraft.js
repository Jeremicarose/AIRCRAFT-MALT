function aircraftText(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function aircraftAge(timestamp) {
  const seconds = Math.max(0, Math.round((Date.now() / 1000) - Number(timestamp || 0)));
  if (seconds < 60) return `${seconds}s`;
  return `${Math.round(seconds / 60)}m`;
}

window.pageHydrators.aircraft = async function ({ fetchJson }) {
  const target = document.getElementById('aircraft-table');
  const detailTarget = document.getElementById('aircraft-detail-panel');
  if (!target || !detailTarget) return;

  const data = await fetchJson('/api/positions/recent?seconds=600&limit=250').catch(() => null);
  const latestByAircraft = new Map();
  (data?.positions || []).forEach((position) => {
    if (!latestByAircraft.has(position.aircraft_id)) latestByAircraft.set(position.aircraft_id, position);
  });
  const positions = [...latestByAircraft.values()];

  if (!positions.length) {
    target.innerHTML = `
      <table class="app-table">
        <thead><tr><th>ICAO</th><th>Altitude</th><th>Receivers</th><th>Quality</th><th>Age</th></tr></thead>
        <tbody><tr><td colspan="5">No recent aircraft positions.</td></tr></tbody>
      </table>
    `;
    detailTarget.innerHTML = `
      <div class="panel-head"><div><h2>No aircraft selected</h2><p>Waiting for solved output</p></div></div>
      <div class="empty-state">Connect a receiver feed or inspect the live map.</div>
    `;
    return;
  }

  target.innerHTML = `
    <table class="app-table">
      <thead><tr><th>ICAO</th><th>Altitude</th><th>Receivers</th><th>Quality</th><th>Age</th></tr></thead>
      <tbody>
        ${positions.map((position) => `
          <tr>
            <td><button class="data-list-button" type="button" data-aircraft-id="${aircraftText(position.aircraft_id)}">${aircraftText(position.aircraft_id)}</button></td>
            <td>${Math.round(position.position.altitude).toLocaleString()}m</td>
            <td>${position.num_receivers}</td>
            <td>${Math.round(Number(position.quality?.score || 0) * 100)}%</td>
            <td>${aircraftAge(position.timestamp)}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;

  async function renderDetail(aircraftId) {
    const [latest, track] = await Promise.all([
      fetchJson(`/api/aircraft/${encodeURIComponent(aircraftId)}/latest`).catch(() => null),
      fetchJson(`/api/aircraft/${encodeURIComponent(aircraftId)}/track?limit=20`).catch(() => null),
    ]);
    if (!latest || !track) return;

    detailTarget.innerHTML = `
      <div class="panel-head"><div><h2>${aircraftText(aircraftId)}</h2><p>Latest derived state</p></div><span class="status-pill mode-live">Tracked</span></div>
      <div class="detail-kv">
        <div class="detail-kv-row"><strong>Position</strong><span>${latest.position.latitude.toFixed(4)}, ${latest.position.longitude.toFixed(4)}</span></div>
        <div class="detail-kv-row"><strong>Altitude</strong><span>${Math.round(latest.position.altitude).toLocaleString()}m</span></div>
        <div class="detail-kv-row"><strong>Uncertainty</strong><span>±${Math.round(latest.uncertainty)}m</span></div>
        <div class="detail-kv-row"><strong>Receivers</strong><span>${latest.num_receivers}</span></div>
        <div class="detail-kv-row"><strong>Quality</strong><span>${Math.round(Number(latest.quality?.score || 0) * 100)}% / ${aircraftText(latest.quality?.bucket || 'unknown')}</span></div>
        <div class="detail-kv-row"><strong>Solver</strong><span>${aircraftText(latest.solver?.method || 'unknown')}</span></div>
        <div class="detail-kv-row"><strong>Residual</strong><span>${Number(latest.solver?.residual_m || 0).toFixed(1)}m</span></div>
        <div class="detail-kv-row"><strong>Track points</strong><span>${track.num_positions}</span></div>
      </div>
      <div class="ops-rail-title">Recent track</div>
      <div class="list-rows">
        ${track.positions.slice(-6).reverse().map((point) => `
          <div class="list-row"><strong>${new Date(point.timestamp * 1000).toLocaleTimeString()}</strong><span>${point.latitude.toFixed(3)}, ${point.longitude.toFixed(3)} · ${Math.round(point.altitude)}m</span></div>
        `).join('')}
      </div>
    `;
  }

  target.querySelectorAll('[data-aircraft-id]').forEach((button) => {
    button.addEventListener('click', () => renderDetail(button.dataset.aircraftId));
  });
  renderDetail(positions[0].aircraft_id);
};

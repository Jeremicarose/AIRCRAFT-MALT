window.pageHydrators.aircraft = async function ({ fetchJson }) {
  const target = document.getElementById('aircraft-table');
  const detailTarget = document.getElementById('aircraft-detail-panel');
  if (!target) return;

  const data = await fetchJson('/api/positions/recent?seconds=600&limit=50').catch(() => null);
  if (!data || !data.positions.length) {
        target.innerHTML = '<div class="empty-state">No aircraft positions available in the last 10 minutes.</div>';
        if (detailTarget) {
          detailTarget.innerHTML = '<div class="empty-state">Select an aircraft once traffic is available to inspect path, quality, uncertainty, and solver context.</div>';
        }
        return;
  }

  target.innerHTML = `
    <div class="list-card">
      <div class="head">
        <div>
          <span class="kicker">Recent aircraft</span>
          <h3>Pick an aircraft, then inspect its solve context</h3>
          <p>Aircraft detail is now separated from the localization map so operators can compare quality, solver residuals, and track history without map clutter.</p>
        </div>
        <div class="inline-pills">
          <span class="inline-pill">Last 10 minutes</span>
          <span class="inline-pill">${data.count} rows</span>
        </div>
      </div>
      <div class="list-rows">
        ${data.positions.map((position) => `
          <div class="list-row">
            <strong>${position.aircraft_id}</strong>
            <span>${Math.round(position.position.altitude)}m · ${position.num_receivers} receivers · ${Math.round((position.quality.score || 0) * 100)}% quality</span>
            <span>Residual ${position.solver.residual_m} · ${new Date(position.timestamp * 1000).toLocaleTimeString()}</span>
            <button class="inline-action" type="button" data-track-id="${position.aircraft_id}">Inspect aircraft</button>
          </div>
        `).join('')}
      </div>
    </div>
  `;

  async function renderAircraftDetail(aircraftId) {
    if (!detailTarget) return;
    const [latest, track] = await Promise.all([
      fetchJson(`/api/aircraft/${encodeURIComponent(aircraftId)}/latest`).catch(() => null),
      fetchJson(`/api/aircraft/${encodeURIComponent(aircraftId)}/track?limit=40`).catch(() => null),
    ]);

    if (!latest || !track) {
      detailTarget.innerHTML = '<div class="empty-state">Unable to load aircraft detail right now.</div>';
      return;
    }

    detailTarget.innerHTML = `
      <div class="split-summary">
        <article class="app-panel">
          <span class="kicker">Aircraft detail</span>
          <h2>${aircraftId}</h2>
          <p>Latest derived state with solver and correlation context separated from the map-first localization surface.</p>
          <div class="detail-kv">
            <div class="detail-kv-row"><strong>Altitude</strong><span>${Math.round(latest.position.altitude)}m</span></div>
            <div class="detail-kv-row"><strong>Receivers</strong><span>${latest.num_receivers}</span></div>
            <div class="detail-kv-row"><strong>Quality</strong><span>${Math.round((latest.quality.score || 0) * 100)}% (${latest.quality.bucket})</span></div>
            <div class="detail-kv-row"><strong>Residual</strong><span>${latest.solver.residual_m}</span></div>
            <div class="detail-kv-row"><strong>Iterations</strong><span>${latest.solver.iterations}</span></div>
            <div class="detail-kv-row"><strong>Time span</strong><span>${latest.correlation.time_span_s}</span></div>
          </div>
        </article>
        <article class="app-panel">
          <span class="kicker">Track history</span>
          <h2>${track.num_positions} recent points</h2>
          <div class="list-rows">
            ${track.positions.slice(-10).reverse().map((point) => `
              <div class="list-row">
                <strong>${new Date(point.timestamp * 1000).toLocaleTimeString()}</strong>
                <span>${point.latitude.toFixed(3)}°, ${point.longitude.toFixed(3)}° · ${Math.round(point.altitude)}m</span>
                <span>${Math.round((point.quality.score || 0) * 100)}% quality · ±${Math.round(point.uncertainty)}m</span>
              </div>
            `).join('')}
          </div>
        </article>
      </div>
    `;
  }

  target.querySelectorAll('[data-track-id]').forEach((button) => {
    button.addEventListener('click', () => {
      renderAircraftDetail(button.dataset.trackId).catch(() => null);
    });
  });

  renderAircraftDetail(data.positions[0].aircraft_id).catch(() => null);
};

function aircraftText(value) {
  return window.shellEscape ? window.shellEscape(value) : String(value ?? '');
}

function aircraftAgeLabel(timestamp) {
  return window.shellRelativeTime ? window.shellRelativeTime(timestamp) : 'n/a';
}

function aircraftAgeSeconds(timestamp) {
  return window.shellAgeSeconds ? window.shellAgeSeconds(timestamp) : null;
}

function aircraftNumber(value, digits = 0, fallback = 'n/a') {
  return window.shellNumber ? window.shellNumber(value, digits, fallback) : fallback;
}

function aircraftPercent(value) {
  return window.shellPercent ? window.shellPercent(value) : 'n/a';
}

function aircraftScoreTone(score) {
  return window.shellToneFromScore ? window.shellToneFromScore(score) : 'tone-neutral';
}

function aircraftFreshnessTone(ageSeconds) {
  return window.shellToneFromFreshness ? window.shellToneFromFreshness(ageSeconds, 20, 90) : 'tone-neutral';
}

function aircraftBadge(label, tone) {
  return window.shellHealthBadge ? window.shellHealthBadge(label, tone) : `<span>${aircraftText(label)}</span>`;
}

function aircraftSparkline(values, strokeClass) {
  return window.shellSparkline ? window.shellSparkline(values, { strokeClass }) : '';
}

function aircraftMiniBar(label, valueText, ratio, tone) {
  return window.shellMiniBar ? window.shellMiniBar(label, valueText, ratio, tone) : '';
}

function getAircraftStatus(latest) {
  const ageSeconds = aircraftAgeSeconds(latest?.timestamp);
  const score = Number(latest?.quality?.score);
  const receivers = Number(latest?.num_receivers || 0);
  const residual = Number(latest?.solver?.residual_m);

  if (ageSeconds !== null && ageSeconds > 90) {
    return {
      label: 'Tracking lost',
      tone: 'tone-risk',
      reason: `Last solved position is ${aircraftAgeLabel(latest.timestamp)}, so the track should be treated as stale evidence.`,
    };
  }
  if (receivers > 0 && receivers < 4) {
    return {
      label: 'Insufficient receivers',
      tone: 'tone-warn',
      reason: `${receivers} receiver${receivers === 1 ? '' : 's'} contributed to the latest solve, which limits multilateration geometry.`,
    };
  }
  if ((Number.isFinite(score) && score < 0.55) || (Number.isFinite(residual) && residual > 300)) {
    return {
      label: 'Low confidence',
      tone: 'tone-warn',
      reason: `The latest solve reports ${aircraftPercent(score)} confidence${Number.isFinite(residual) ? ` with ${residual.toFixed(1)}m residual` : ''}, so treat the exact position as approximate.`,
    };
  }
  return {
    label: 'Healthy',
    tone: 'tone-good',
    reason: `Recent timing, receiver count, and solve quality all support the current position estimate.`,
  };
}

function normalizeTrackPoint(point, latest) {
  return {
    timestamp: Number(point?.timestamp || 0),
    latitude: Number(point?.latitude ?? point?.position?.latitude ?? latest?.position?.latitude ?? 0),
    longitude: Number(point?.longitude ?? point?.position?.longitude ?? latest?.position?.longitude ?? 0),
    altitude: Number(point?.altitude ?? point?.position?.altitude ?? latest?.position?.altitude ?? 0),
    uncertainty: Number(point?.uncertainty ?? point?.quality?.uncertainty_m ?? latest?.uncertainty ?? 0),
    numReceivers: Number(point?.num_receivers ?? point?.numReceivers ?? point?.correlation?.receiver_count ?? 0),
    qualityScore: Number(point?.quality?.score),
    qualityBucket: point?.quality?.bucket || 'unknown',
    residual: Number(point?.solver?.residual_m),
    solverMethod: point?.solver?.method || latest?.solver?.method || 'unknown',
    correlation: point?.correlation || {},
  };
}

function buildPathDistance(points) {
  if (points.length < 2) return 0;
  let total = 0;
  for (let index = 1; index < points.length; index += 1) {
    const prev = points[index - 1];
    const next = points[index];
    const dLat = (next.latitude - prev.latitude) * 111320;
    const avgLat = ((next.latitude + prev.latitude) / 2) * (Math.PI / 180);
    const dLon = (next.longitude - prev.longitude) * 111320 * Math.cos(avgLat);
    total += Math.sqrt((dLat ** 2) + (dLon ** 2));
  }
  return total;
}

function buildFlightPathSvg(points) {
  if (!points.length) return '<div class="chart-empty mini-sparkline-empty">No recent path</div>';
  if (points.length === 1) {
    return `
      <svg class="path-sparkline" viewBox="0 0 240 120" preserveAspectRatio="none" aria-hidden="true">
        <circle class="path-sparkline-dot" cx="120" cy="60" r="4"></circle>
      </svg>
    `;
  }
  const latitudes = points.map((point) => point.latitude);
  const longitudes = points.map((point) => point.longitude);
  const minLat = Math.min(...latitudes);
  const maxLat = Math.max(...latitudes);
  const minLon = Math.min(...longitudes);
  const maxLon = Math.max(...longitudes);
  const latSpan = (maxLat - minLat) || 0.01;
  const lonSpan = (maxLon - minLon) || 0.01;
  const width = 240;
  const height = 120;
  const padding = 10;
  const path = points.map((point, index) => {
    const x = padding + (((point.longitude - minLon) / lonSpan) * (width - padding * 2));
    const y = height - padding - (((point.latitude - minLat) / latSpan) * (height - padding * 2));
    return `${index === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)}`;
  }).join(' ');
  const first = points[0];
  const last = points[points.length - 1];
  const firstX = padding + (((first.longitude - minLon) / lonSpan) * (width - padding * 2));
  const firstY = height - padding - (((first.latitude - minLat) / latSpan) * (height - padding * 2));
  const lastX = padding + (((last.longitude - minLon) / lonSpan) * (width - padding * 2));
  const lastY = height - padding - (((last.latitude - minLat) / latSpan) * (height - padding * 2));
  return `
    <svg class="path-sparkline" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" aria-hidden="true">
      <path class="chart-line path-sparkline-line" d="${path}"></path>
      <circle class="path-sparkline-start" cx="${firstX.toFixed(2)}" cy="${firstY.toFixed(2)}" r="3.4"></circle>
      <circle class="path-sparkline-end" cx="${lastX.toFixed(2)}" cy="${lastY.toFixed(2)}" r="4"></circle>
    </svg>
  `;
}

function buildContributionRows(points) {
  const counts = new Map();
  let sightings = 0;
  points.forEach((point) => {
    const receiverIds = Array.isArray(point?.correlation?.receiver_ids) ? point.correlation.receiver_ids : [];
    receiverIds.forEach((receiverId) => {
      counts.set(receiverId, (counts.get(receiverId) || 0) + 1);
      sightings += 1;
    });
  });
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
    .map(([receiverId, count]) => ({
      receiverId,
      count,
      ratio: sightings ? count / Math.max(...counts.values()) : 0,
      share: sightings ? count / sightings : 0,
    }));
}

function buildEvidenceRows(latest, modeData, status) {
  const rows = [];
  rows.push({
    title: 'Trust verdict',
    body: status.reason,
    tone: status.tone,
  });
  rows.push({
    title: 'Solve method',
    body: `${aircraftText(latest?.solver?.method || 'unknown')} generated the most recent position fix${Number.isFinite(Number(latest?.solver?.residual_m)) ? ` with ${Number(latest.solver.residual_m).toFixed(1)}m residual.` : '.'}`,
    tone: Number(latest?.solver?.residual_m) <= 100 ? 'tone-good' : Number(latest?.solver?.residual_m) <= 300 ? 'tone-warn' : 'tone-risk',
  });
  rows.push({
    title: 'Receiver adequacy',
    body: `${latest?.num_receivers || 0} receivers were reported on the latest solve. This page treats contribution as “seen across recent solves,” not exact solver weighting.`,
    tone: Number(latest?.num_receivers) >= 4 ? 'tone-good' : 'tone-warn',
  });
  rows.push({
    title: 'Runtime provenance',
    body: modeData?.synthetic_feed_mode || modeData?.simulation_mode || modeData?.demo_mode
      ? 'Current output is replay, synthetic, or demo-sourced, so it validates the pipeline but not live-airspace proof.'
      : 'Current output is live-configured and not marked as replay/synthetic by shell mode data.',
    tone: modeData?.synthetic_feed_mode || modeData?.simulation_mode || modeData?.demo_mode ? 'tone-warn' : 'tone-good',
  });
  rows.push({
    title: 'Benchmark readiness',
    body: modeData?.benchmarkable_output
      ? 'Shell mode data marks current output as benchmarkable, so this aircraft can contribute to proof-ready evidence if the rest of the pipeline passes.'
      : 'Shell mode data does not currently mark output as benchmarkable, so aircraft evidence remains operational rather than publishable proof.',
    tone: modeData?.benchmarkable_output ? 'tone-good' : 'tone-warn',
  });
  return rows;
}

function buildReceiverLinks(receiverRows) {
  if (!receiverRows.length) return '<p class="panel-empty-note">No contributing receivers were exposed for the recent track.</p>';
  return `
    <div class="entity-link-list">
      ${receiverRows.map((row) => `
        <a class="entity-link-chip" href="/app/receivers.html?receiver=${encodeURIComponent(row.receiverId)}">${aircraftText(row.receiverId)}<span>${Math.round(row.share * 100)}% of recent solves</span></a>
      `).join('')}
    </div>
  `;
}

window.pageHydrators.aircraft = async function ({ fetchJson, modeData }) {
  const target = document.getElementById('aircraft-table');
  const detailTarget = document.getElementById('aircraft-detail-panel');
  if (!target || !detailTarget) return;

  const data = await fetchJson('/api/positions/recent?seconds=600&limit=250').catch(() => null);
  const latestByAircraft = new Map();
  [...(data?.positions || [])]
    .sort((a, b) => Number(b.timestamp || 0) - Number(a.timestamp || 0))
    .forEach((position) => {
      if (!latestByAircraft.has(position.aircraft_id)) latestByAircraft.set(position.aircraft_id, position);
    });
  const allPositions = [...latestByAircraft.values()];
  let filteredPositions = allPositions.slice();
  let selectedAircraftId = window.getSelectionParam ? window.getSelectionParam('aircraft') : null;

  function renderEmptyState() {
    target.innerHTML = `
      <div class="list-shell">
        <div class="list-toolbar">
          <label class="control-label" for="aircraft-search">Search aircraft</label>
          <input id="aircraft-search" class="control-input list-search-input" type="search" placeholder="Filter by ICAO">
        </div>
        <table class="app-table">
          <thead><tr><th>ICAO</th><th>Status</th><th>Receivers</th><th>Quality</th><th>Age</th></tr></thead>
          <tbody><tr><td colspan="5">No recent aircraft positions.</td></tr></tbody>
        </table>
      </div>
    `;
    detailTarget.innerHTML = `
      <div class="panel-head"><div><h2>No aircraft selected</h2><p>Waiting for solved output</p></div></div>
      <div class="empty-state">Connect a receiver feed or inspect the live map.</div>
    `;
  }

  if (!allPositions.length) {
    renderEmptyState();
    return;
  }

  async function renderDetail(aircraftId) {
    selectedAircraftId = aircraftId;
    if (window.setSelectionParam) window.setSelectionParam('aircraft', aircraftId);
    target.querySelectorAll('[data-aircraft-id]').forEach((button) => {
      button.classList.toggle('is-selected', button.dataset.aircraftId === aircraftId);
    });

    const [latest, track] = await Promise.all([
      fetchJson(`/api/aircraft/${encodeURIComponent(aircraftId)}/latest`).catch(() => null),
      fetchJson(`/api/aircraft/${encodeURIComponent(aircraftId)}/track?limit=20`).catch(() => null),
    ]);
    if (!latest || !track) {
      detailTarget.innerHTML = `
        <div class="panel-head"><div><h2>${aircraftText(aircraftId)}</h2><p>Unable to load trust evidence</p></div></div>
        <div class="empty-state">The latest aircraft detail request failed.</div>
      `;
      return;
    }

    const trackPoints = (track.positions || []).map((point) => normalizeTrackPoint(point, latest)).sort((a, b) => a.timestamp - b.timestamp);
    const status = getAircraftStatus(latest);
    const contributionRows = buildContributionRows(trackPoints);
    const confidenceValues = trackPoints.map((point) => point.qualityScore).filter((value) => Number.isFinite(value));
    const uncertaintyValues = trackPoints.map((point) => point.uncertainty).filter((value) => Number.isFinite(value));
    const flightDistance = buildPathDistance(trackPoints);
    const receiverMentions = contributionRows.reduce((sum, row) => sum + row.count, 0);
    const evidenceRows = buildEvidenceRows(latest, modeData, status);

    detailTarget.innerHTML = `
      <div class="panel-head inspector-head">
        <div>
          <h2>${aircraftText(aircraftId)}</h2>
          <p>Why this position is believable, and where the proof is weak.</p>
        </div>
        ${aircraftBadge(status.label, status.tone)}
      </div>
      <div class="inspector-scroll">
        <section class="inspector-section inspector-hero">
          <div class="summary-card-grid">
            <article class="summary-card accent-trust">
              <span>Latest position</span>
              <strong>${aircraftText(latest.position.latitude.toFixed(4))}, ${aircraftText(latest.position.longitude.toFixed(4))}</strong>
              <small>${aircraftAgeLabel(latest.timestamp)} · ${Math.round(Number(latest.position.altitude || 0)).toLocaleString()}m altitude</small>
            </article>
            <article class="summary-card ${aircraftScoreTone(latest.quality?.score)}">
              <span>Confidence</span>
              <strong>${aircraftPercent(latest.quality?.score)}</strong>
              <small>${aircraftText(latest.quality?.bucket || 'unknown')} bucket · residual ${Number(latest.solver?.residual_m || 0).toFixed(1)}m</small>
            </article>
            <article class="summary-card ${aircraftFreshnessTone(aircraftAgeSeconds(latest.timestamp))}">
              <span>Receiver geometry</span>
              <strong>${Math.round(Number(latest.num_receivers || 0))}</strong>
              <small>${receiverMentions} receiver mentions across ${trackPoints.length} recent solves</small>
            </article>
          </div>
        </section>

        <details class="inspector-disclosure inspector-section" open>
          <summary class="disclosure-summary"><span>Recent solve shape</span><small>Track motion and confidence over the last ${trackPoints.length} points.</small></summary>
          <div class="disclosure-body">
            <div class="mini-chart-grid">
              <article class="mini-chart-card">
                <div class="mini-chart-head"><strong>Flight path</strong><span>${Math.round(flightDistance).toLocaleString()}m sampled path</span></div>
                ${buildFlightPathSvg(trackPoints)}
              </article>
              <article class="mini-chart-card">
                <div class="mini-chart-head"><strong>Confidence timeline</strong><span>${confidenceValues.length ? `${aircraftPercent(confidenceValues[confidenceValues.length - 1])} latest` : 'No quality samples'}</span></div>
                ${aircraftSparkline(confidenceValues, 'chart-line')}
              </article>
            </div>
          </div>
        </details>

        <details class="inspector-disclosure inspector-section">
          <summary class="disclosure-summary"><span>Contribution and uncertainty</span><small>Frontend approximations from recent track evidence.</small></summary>
          <div class="disclosure-body">
            <div class="split-mini-grid">
              <article class="mini-evidence-card">
                <div class="mini-chart-head"><strong>Receiver contribution</strong><span>Seen across recent solves</span></div>
                <div class="contribution-stack">
                  ${contributionRows.length
                    ? contributionRows.map((row) => aircraftMiniBar(row.receiverId, `${row.count} sightings`, row.ratio, row.share >= 0.2 ? 'tone-good' : 'tone-warn')).join('')
                    : '<p class="panel-empty-note">No receiver IDs were exposed in recent track points.</p>'}
                </div>
              </article>
              <article class="mini-evidence-card">
                <div class="mini-chart-head"><strong>Uncertainty explanation</strong><span>${Number.isFinite(Number(latest.uncertainty)) ? `±${Math.round(Number(latest.uncertainty))}m latest` : 'Unavailable'}</span></div>
                <div class="explanation-stack">
                  <div class="explanation-row">
                    <strong>Estimated uncertainty</strong>
                    <span>${Number.isFinite(Number(latest.uncertainty))
                      ? `The latest solve advertises an uncertainty radius of ±${Math.round(Number(latest.uncertainty))}m. Use this as the visible error band rather than assuming a point-perfect location.`
                      : 'The API did not expose an uncertainty value for the latest solve.'}</span>
                  </div>
                  <div class="explanation-row">
                    <strong>Recent spread</strong>
                    <span>${uncertaintyValues.length
                      ? `Across the recent sample, uncertainty ranges from ±${Math.round(Math.min(...uncertaintyValues))}m to ±${Math.round(Math.max(...uncertaintyValues))}m.`
                      : 'There are not enough recent uncertainty samples to show spread.'}</span>
                  </div>
                </div>
              </article>
            </div>
          </div>
        </details>

        <details class="inspector-disclosure inspector-section">
          <summary class="disclosure-summary"><span>Evidence panel</span><small>Solver, provenance, and benchmark readiness statements.</small></summary>
          <div class="disclosure-body">
            <div class="checklist-card-grid">
              ${evidenceRows.map((row) => `
                <article class="checklist-card ${aircraftText(row.tone)}">
                  <strong>${aircraftText(row.title)}</strong>
                  <p>${aircraftText(row.body)}</p>
                </article>
              `).join('')}
            </div>
          </div>
        </details>

        <details class="inspector-disclosure inspector-section">
          <summary class="disclosure-summary"><span>Related receivers</span><small>Jump to the nodes most often seen in the recent track.</small></summary>
          <div class="disclosure-body">
            ${buildReceiverLinks(contributionRows)}
          </div>
        </details>

        <details class="inspector-disclosure inspector-section">
          <summary class="disclosure-summary"><span>Recent track drill-down</span><small>Per-point evidence for manual inspection.</small></summary>
          <div class="disclosure-body">
            <div class="list-rows detailed-list-rows">
              ${trackPoints.slice().reverse().map((point) => `
                <div class="list-row detail-list-row">
                  <strong>${new Date(point.timestamp * 1000).toLocaleTimeString()} · ${point.latitude.toFixed(3)}, ${point.longitude.toFixed(3)}</strong>
                  <span>${Math.round(point.altitude).toLocaleString()}m · ${aircraftPercent(point.qualityScore)} confidence · ${point.numReceivers || 0} receivers · residual ${Number.isFinite(point.residual) ? point.residual.toFixed(1) : 'n/a'}m</span>
                </div>
              `).join('')}
            </div>
          </div>
        </details>
      </div>
    `;
  }

  function renderTable() {
    target.innerHTML = `
      <div class="list-shell">
        <div class="list-toolbar">
          <div>
            <label class="control-label" for="aircraft-search">Search aircraft</label>
            <input id="aircraft-search" class="control-input list-search-input" type="search" placeholder="Filter by ICAO" value="${aircraftText(document.getElementById('aircraft-search')?.value || '')}">
          </div>
          <div class="list-toolbar-note">${filteredPositions.length} of ${allPositions.length} aircraft</div>
        </div>
        <table class="app-table aircraft-evidence-table">
          <thead><tr><th>ICAO</th><th>Status</th><th>Receivers</th><th>Quality</th><th>Age</th></tr></thead>
          <tbody>
            ${filteredPositions.map((position) => {
              const status = getAircraftStatus(position);
              return `
                <tr>
                  <td><button class="data-list-button ${selectedAircraftId === position.aircraft_id ? 'is-selected' : ''}" type="button" data-aircraft-id="${aircraftText(position.aircraft_id)}">${aircraftText(position.aircraft_id)}</button></td>
                  <td>${aircraftBadge(status.label, status.tone)}</td>
                  <td>${Math.round(Number(position.num_receivers || 0))}</td>
                  <td><span class="table-emphasis ${aircraftScoreTone(position.quality?.score)}">${aircraftPercent(position.quality?.score)}</span></td>
                  <td>${aircraftAgeLabel(position.timestamp)}</td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
    `;

    const searchInput = target.querySelector('#aircraft-search');
    if (searchInput) {
      searchInput.addEventListener('input', () => {
        filteredPositions = window.filterByQuery
          ? window.filterByQuery(allPositions, searchInput.value, (item) => item.aircraft_id)
          : allPositions;
        renderTable();
      });
    }

    target.querySelectorAll('[data-aircraft-id]').forEach((button) => {
      button.addEventListener('click', () => renderDetail(button.dataset.aircraftId));
    });
  }

  renderTable();
  const initialId = selectedAircraftId && allPositions.some((position) => position.aircraft_id === selectedAircraftId)
    ? selectedAircraftId
    : allPositions[0].aircraft_id;
  renderDetail(initialId);
};
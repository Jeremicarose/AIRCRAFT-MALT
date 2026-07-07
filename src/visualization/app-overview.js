window.pageHydrators.overview = async function ({ modeData, healthData, aircraftData, receiverData, fetchJson }) {
  const cards = [
    {
      kicker: 'System status',
      title: 'This page is the new operational home for the product.',
      copy: 'Use it for a fast summary of mode, freshness, benchmarkability, and runtime posture before drilling into aircraft, receivers, or localization.',
    },
    {
      kicker: 'Current mode',
      title: modeData ? (modeData.mode || 'unknown').toUpperCase() : 'UNKNOWN',
      copy: modeData
        ? `Simulation mode: ${Boolean(modeData.simulation_mode)} · Demo mode: ${Boolean(modeData.demo_mode)} · Synthetic feed: ${Boolean(modeData.synthetic_feed_mode)}`
        : 'Mode data unavailable.',
    },
    {
      kicker: 'Runtime health',
      title: healthData ? (healthData.status || 'unknown').toUpperCase() : 'UNKNOWN',
      copy: healthData && healthData.freshness
        ? `Last signal age: ${healthData.freshness.last_signal_age_s ?? 'n/a'}s · Last store age: ${healthData.freshness.last_store_age_s ?? 'n/a'}s`
        : 'Health data unavailable.',
    },
  ];

  renderOverviewCards(document.getElementById('overview-cards'), cards);

  const readiness = await fetchJson('/api/readiness').catch(() => null);
  const readinessTarget = document.getElementById('readiness-panel');
  const summaryTarget = document.getElementById('overview-summary');
  if (!readinessTarget) return;

  if (!readiness) {
    readinessTarget.innerHTML = '<div class="empty-state">Readiness data unavailable.</div>';
    return;
  }

  readinessTarget.innerHTML = `
    <div class="stat-grid">
      <article class="stat-tile">
        <strong>Quality</strong>
        <span class="value">${Math.round(readiness.dimensions.quality.avg_quality_score * 100)}%</span>
        <span class="detail">Ready: ${readiness.dimensions.quality.ready} · Benchmarkable: ${readiness.dimensions.quality.benchmarkable_output}</span>
      </article>
      <article class="stat-tile">
        <strong>Freshness</strong>
        <span class="value">${readiness.dimensions.freshness.last_store_age_s ?? 'n/a'}s</span>
        <span class="detail">Ready: ${readiness.dimensions.freshness.ready} · API latency: ${readiness.dimensions.freshness.avg_api_latency_ms.toFixed(1)}ms</span>
      </article>
      <article class="stat-tile">
        <strong>Reliability</strong>
        <span class="value">${readiness.dimensions.reliability.active_receivers}</span>
        <span class="detail">Receivers active · Failed solves: ${readiness.dimensions.reliability.failed_solves}</span>
      </article>
      <article class="stat-tile">
        <strong>Packaging</strong>
        <span class="value">${readiness.dimensions.packaging.ready ? 'Ready' : 'Not ready'}</span>
        <span class="detail">Health, positions, tracks, and premium stats are exposed</span>
      </article>
    </div>
  `;

  if (summaryTarget && healthData) {
    const freshness = healthData.freshness || {};
    const benchmarkability = healthData.benchmarkability || {};
    summaryTarget.innerHTML = `
      <div class="split-summary">
        <article class="app-panel hero-panel surface-premium">
          <span class="kicker">Decision summary</span>
          <h2>${readiness.ready ? 'Operationally ready by internal gates' : 'Not yet internally ready'}</h2>
          <p>The project already measures quality, freshness, reliability, and packaging internally. What still matters is whether the current output is benchmarkable and whether a real external comparator run is possible.</p>
          <div class="action-row">
            <a class="action-chip" href="/app/localization.html">Open localization</a>
            <a class="action-chip" href="/app/analytics.html">Inspect analytics</a>
            <a class="action-chip" href="/app/aircraft.html">Review aircraft</a>
          </div>
          <div class="decision-list">
            <div class="decision-item">
              <strong>What is already true</strong>
              <span>Quality, freshness, reliability, and packaging are measured internally through health, readiness, positions, and statistics surfaces.</span>
            </div>
            <div class="decision-item">
              <strong>What is still missing</strong>
              <span>Real external benchmark proof against trusted references, and real live observation input when replay/synthetic traffic is still active.</span>
            </div>
          </div>
        </article>
        <article class="app-panel">
          <span class="kicker">Current truth</span>
          <h2>${benchmarkability.benchmarkable_output ? 'Benchmarkable output present' : 'Replay / synthetic output still present'}</h2>
          <div class="detail-kv">
            <div class="detail-kv-row"><strong>Last signal age</strong><span>${freshness.last_signal_age_s ?? 'n/a'}s</span></div>
            <div class="detail-kv-row"><strong>Last store age</strong><span>${freshness.last_store_age_s ?? 'n/a'}s</span></div>
            <div class="detail-kv-row"><strong>Receiver stale count</strong><span>${freshness.receiver_stale_count ?? 'n/a'}</span></div>
            <div class="detail-kv-row"><strong>Synthetic feed mode</strong><span>${benchmarkability.synthetic_feed_mode}</span></div>
          </div>
          <div class="action-row">
            <a class="action-chip" href="/app/settings.html">View settings</a>
            <a class="action-chip" href="/api/readiness">Readiness API</a>
          </div>
        </article>
      </div>
    `;
  }
};

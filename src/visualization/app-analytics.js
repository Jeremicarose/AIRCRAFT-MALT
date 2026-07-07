window.pageHydrators.analytics = async function ({ fetchJson }) {
  const target = document.getElementById('analytics-panel');
  if (!target) return;

  const stats = await fetchJson('/api/statistics?hours=24').catch(() => null);
  const readiness = await fetchJson('/api/readiness').catch(() => null);

  if (!stats || !readiness) {
    target.innerHTML = '<div class="empty-state">Analytics data unavailable.</div>';
    return;
  }

  target.innerHTML = `
    <div class="app-grid three-col">
      <article class="app-card">
        <span class="kicker">Quality</span>
        <h2>${(readiness.dimensions.quality.avg_quality_score * 100).toFixed(0)}%</h2>
        <p>Average quality score across recent positions.</p>
      </article>
      <article class="app-card">
        <span class="kicker">Solve latency</span>
        <h2>${readiness.dimensions.freshness.avg_solve_latency_ms.toFixed(1)} ms</h2>
        <p>Average internal solve latency from the runtime.</p>
      </article>
      <article class="app-card">
        <span class="kicker">Rejected groups</span>
        <h2>${readiness.dimensions.reliability.rejected_groups}</h2>
        <p>Rejected correlation groups in current runtime state.</p>
      </article>
    </div>
    <article class="app-panel surface-premium">
      <span class="kicker">Readiness benchmark surface</span>
      <h2>Commercial proof still depends on external comparison</h2>
      <div class="comparison-grid">
        ${[
          ['More accurate', readiness.not_yet_proven.more_accurate_than_incumbents],
          ['More complete', readiness.not_yet_proven.more_complete_than_incumbents],
          ['Cheaper', readiness.not_yet_proven.cheaper_than_incumbents],
          ['Faster', readiness.not_yet_proven.faster_than_incumbents],
          ['Better coverage', readiness.not_yet_proven.better_coverage_than_incumbents],
          ['Better analytics', readiness.not_yet_proven.better_analytics_than_incumbents],
        ].map(([label, value]) => `
          <article class="comparison-card">
            <strong>${label}</strong>
            <span>This claim is still unproven against trusted external comparators.</span>
            <span class="comparison-flag ${value ? 'flag-true' : 'flag-false'}">${value ? 'Proven' : 'Not proven'}</span>
          </article>
        `).join('')}
      </div>
      <p style="margin-top:14px;color:var(--muted);line-height:1.6;">${readiness.not_yet_proven.reason}</p>
    </article>
  `;
};

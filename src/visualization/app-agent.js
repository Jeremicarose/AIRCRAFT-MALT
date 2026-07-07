window.pageHydrators.agent = async function ({ fetchJson }) {
  const target = document.getElementById('agent-panel');
  if (!target) return;
  const [readiness, health] = await Promise.all([
    fetchJson('/api/readiness').catch(() => null),
    fetchJson('/api/health').catch(() => null),
  ]);
  target.innerHTML = `
    <div class="split-summary">
      <article class="app-panel hero-panel surface-premium">
        <span class="kicker">Agent status</span>
        <h2>Automation is partial and infrastructure-oriented.</h2>
        <p>This project currently automates ingest, solving, persistence, and readiness reporting. It is not yet a strong end-user autonomous agent product.</p>
        <div class="decision-list">
          <div class="decision-item">
            <strong>What is automated today</strong>
            <span>Signal ingest, correlation, solving, persistence, readiness reporting, and benchmarkability checks.</span>
          </div>
          <div class="decision-item">
            <strong>What is not automated yet</strong>
            <span>High-trust autonomous decisions, user-facing reasoning traces, and rich action workflows.</span>
          </div>
        </div>
      </article>
      <article class="app-panel">
        <span class="kicker">Current signals</span>
        <h2>Runtime reasoning surface</h2>
        <p>${readiness ? `Reliability ready: ${readiness.dimensions.reliability.ready} · Freshness ready: ${readiness.dimensions.freshness.ready}` : 'Readiness data unavailable.'}</p>
      </article>
    </div>
    <article class="app-panel">
      <span class="kicker">Current autonomous boundary</span>
      <h2>What the system is doing on its own today</h2>
      <table class="app-table">
        <tbody>
          <tr><th>Signal freshness</th><td>${readiness ? readiness.dimensions.reliability.signal_fresh : 'unknown'}</td></tr>
          <tr><th>Rejected groups</th><td>${readiness ? readiness.dimensions.reliability.rejected_groups : 'unknown'}</td></tr>
          <tr><th>Failed solves</th><td>${readiness ? readiness.dimensions.reliability.failed_solves : 'unknown'}</td></tr>
          <tr><th>API health</th><td>${health ? health.status : 'unknown'}</td></tr>
        </tbody>
      </table>
      <p style="margin-top:14px;color:var(--muted);line-height:1.6;">This page is where future agent actions, reasoning logs, guardrails, and automated decision traces should live once the project has stronger autonomous workflows.</p>
    </article>
  `;
};

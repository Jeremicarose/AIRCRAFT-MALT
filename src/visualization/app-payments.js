window.pageHydrators.payments = async function ({ fetchJson }) {
  const target = document.getElementById('payments-panel');
  if (!target) return;
  const apiDoc = await fetchJson('/api').catch(() => null);
  target.innerHTML = `
    <div class="split-summary">
      <article class="app-panel hero-panel surface-premium">
        <span class="kicker">Current state</span>
        <h2>Payments are architecture-ready, not live-ready.</h2>
        <p>The repo already contains plans, API keys, entitlements, and usage metering. Fiber / CKB settlement history is not yet connected to a real payment source.</p>
        <div class="action-row">
          <a class="action-chip" href="/app/settings.html">Review settings</a>
          <a class="action-chip" href="/api">Inspect API packaging</a>
        </div>
      </article>
      <article class="app-panel">
        <span class="kicker">Next steps</span>
        <h2>What this page will eventually show</h2>
        <p>Payment history, pending transactions, settlement status, and premium access posture once a real payment layer is wired in.</p>
      </article>
    </div>
    <article class="app-panel">
      <span class="kicker">Current packaging signals</span>
      <h2>Commercial readiness already present in the API</h2>
      <div class="comparison-grid">
        <article class="comparison-card">
          <strong>Public plan</strong>
          <span>${apiDoc && apiDoc.commercial ? apiDoc.commercial.public_plan : 'unknown'}</span>
        </article>
        <article class="comparison-card">
          <strong>Premium plan</strong>
          <span>${apiDoc && apiDoc.commercial ? apiDoc.commercial.premium_plan : 'unknown'}</span>
        </article>
        <article class="comparison-card">
          <strong>Usage metering</strong>
          <span>${apiDoc && apiDoc.commercial ? apiDoc.commercial.usage_metering.join(', ') : 'unknown'}</span>
        </article>
        <article class="comparison-card">
          <strong>Premium features</strong>
          <span>${apiDoc && apiDoc.commercial ? apiDoc.commercial.premium_features.join(', ') : 'unknown'}</span>
        </article>
      </div>
    </article>
  `;
};

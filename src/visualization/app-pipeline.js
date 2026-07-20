function escapePipelineValue(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function pipelineMetricValue(value) {
  if (value == null) return 'n/a';
  if (typeof value === 'boolean') return value ? 'yes' : 'no';
  if (typeof value === 'number') {
    return Number.isInteger(value) ? String(value) : value.toFixed(value < 10 ? 2 : 1);
  }
  return String(value);
}

function pipelineStatusLabel(status) {
  return {
    pass: 'Verified',
    demo: 'Replay only',
    waiting: 'Waiting',
    blocked: 'Blocked',
  }[status] || status;
}

function renderPipelineStage(stage, index) {
  const metrics = Object.entries(stage.metrics || {}).filter(([, value]) => value != null);
  return `
    <article class="pipeline-stage status-${escapePipelineValue(stage.status)}">
      <div class="pipeline-stage-head">
        <span class="pipeline-stage-index">${String(index + 1).padStart(2, '0')}</span>
        <span class="pipeline-stage-state">${escapePipelineValue(pipelineStatusLabel(stage.status))}</span>
      </div>
      <h2>${escapePipelineValue(stage.label)}</h2>
      <p>${escapePipelineValue(stage.detail)}</p>
      <dl class="pipeline-stage-metrics">
        ${metrics.slice(0, 4).map(([label, value]) => `
          <div><dt>${escapePipelineValue(label.replaceAll('_', ' '))}</dt><dd>${escapePipelineValue(pipelineMetricValue(value))}</dd></div>
        `).join('')}
      </dl>
    </article>
  `;
}

function renderPipeline(payload) {
  const target = document.getElementById('pipeline-panel');
  if (!target) return;
  const liveReady = Boolean(payload.live_evidence_ready);
  const operational = Boolean(payload.pipeline_operational);
  const blockers = Array.isArray(payload.blockers) ? payload.blockers : [];
  const stages = Array.isArray(payload.stages) ? payload.stages : [];

  target.innerHTML = `
    <div class="evidence-stack">
      <section class="pipeline-verdict app-panel">
        <div>
          <span class="pipeline-verdict-label">Evidence verdict</span>
          <h2>${liveReady ? 'Live evidence is publishable' : operational ? 'Pipeline works, live proof is incomplete' : 'Pipeline is waiting for input'}</h2>
          <p>${liveReady
            ? 'All live-data and external benchmark gates are passing.'
            : payload.provenance?.mode === 'replay'
              ? 'The software path is operating with replay data. Replay stages remain visibly separate from live evidence.'
              : 'The runtime is live-configured, but one or more evidence gates still need a verified result.'}</p>
        </div>
        <span class="evidence-status ${liveReady ? 'status-pass' : 'status-hold'}">${liveReady ? 'Grant ready' : 'Evidence pending'}</span>
      </section>

      <section class="app-panel pipeline-flow-panel">
        <div class="evidence-heading">
          <div><h2>Receiver-to-dashboard trace</h2><p>Every stage is derived from the current runtime, database, or published artifact.</p></div>
          <span class="evidence-status ${payload.provenance?.mode === 'live' ? 'status-pass' : 'status-hold'}">${escapePipelineValue(payload.provenance?.mode || 'unknown')}</span>
        </div>
        <div class="pipeline-flow">
          ${stages.map(renderPipelineStage).join('')}
        </div>
      </section>

      <section class="pipeline-evidence-grid">
        <div class="app-panel pipeline-blockers">
          <div class="evidence-heading"><div><h2>Open evidence gates</h2><p>These conditions prevent a live-data claim.</p></div><span>${blockers.length}</span></div>
          ${blockers.length
            ? `<ul>${blockers.map((item) => `<li>${escapePipelineValue(item)}</li>`).join('')}</ul>`
            : '<p class="pipeline-clear">No evidence blockers are currently reported.</p>'}
        </div>
        <div class="app-panel pipeline-proof-links">
          <div class="evidence-heading"><div><h2>Inspect proof surfaces</h2><p>Open the machine-readable records used by this view.</p></div></div>
          <div class="pipeline-link-list">
            <a href="/api/pipeline">Pipeline JSON <span>current state</span></a>
            <a href="/api/evidence/metrics">Metrics JSON <span>bounded history</span></a>
            <a href="/api/benchmark/latest">Accuracy report <span>${escapePipelineValue(payload.benchmark?.status || 'not found')}</span></a>
            <a href="/app/analytics.html">System metrics <span>charts and artifacts</span></a>
          </div>
        </div>
      </section>
    </div>
  `;
}

window.pageHydrators.pipeline = async function ({ fetchJson }) {
  const load = async () => {
    const payload = await fetchJson('/api/pipeline');
    renderPipeline(payload);
  };
  await load();
  window.setInterval(() => load().catch(() => null), 10000);
};

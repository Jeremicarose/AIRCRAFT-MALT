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

function pipelineReasonChips(payload) {
  const chips = [];
  const blockers = Array.isArray(payload.blockers) ? payload.blockers : [];
  if (blockers.length) chips.push({ label: `${blockers.length} blocker${blockers.length === 1 ? '' : 's'}`, tone: 'tone-risk' });
  if (payload.provenance?.mode === 'replay') chips.push({ label: 'Replay provenance', tone: 'tone-warn' });
  if (!payload.benchmark?.publishable) chips.push({ label: `Benchmark ${payload.benchmark?.status || 'missing'}`, tone: 'tone-warn' });
  if (payload.live_evidence_ready) chips.push({ label: 'Proof publishable', tone: 'tone-good' });
  return chips;
}

function renderMetricEntries(metrics) {
  const entries = Object.entries(metrics || {}).filter(([, value]) => value != null);
  if (!entries.length) return '<p class="pipeline-stage-detail-empty">No additional metrics were exposed for this stage.</p>';
  return `
    <dl class="pipeline-stage-metrics pipeline-stage-metrics-expanded">
      ${entries.map(([label, value]) => `
        <div><dt>${escapePipelineValue(label.replaceAll('_', ' '))}</dt><dd>${escapePipelineValue(pipelineMetricValue(value))}</dd></div>
      `).join('')}
    </dl>
  `;
}

function renderPipelineStage(stage, index, expandedStageId) {
  const metrics = Object.entries(stage.metrics || {}).filter(([, value]) => value != null);
  const expanded = stage.id === expandedStageId;
  return `
    <article class="pipeline-stage status-${escapePipelineValue(stage.status)} ${expanded ? 'is-expanded' : ''}">
      <button class="pipeline-stage-button" type="button" data-stage-id="${escapePipelineValue(stage.id)}" aria-expanded="${expanded ? 'true' : 'false'}">
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
      </button>
      ${expanded ? `
        <div class="pipeline-stage-detail-panel">
          <div class="pipeline-stage-detail-copy">
            <strong>Full detail</strong>
            <p>${escapePipelineValue(stage.detail)}</p>
          </div>
          ${renderMetricEntries(stage.metrics)}
          <div class="pipeline-stage-link-row">
            <a class="action-chip" href="/api/pipeline">Pipeline JSON</a>
            <a class="action-chip" href="/api/evidence/metrics">Metrics JSON</a>
            <a class="action-chip" href="/api/benchmark/latest">Benchmark report</a>
          </div>
        </div>
      ` : ''}
    </article>
  `;
}

function buildHistorySummary(metricsPayload) {
  const history = Array.isArray(metricsPayload?.history) ? metricsPayload.history : [];
  if (!history.length) {
    return {
      receiverAvailability: null,
      signalFreshness: null,
      solveTrend: [],
      aircraftTrend: [],
    };
  }
  return {
    receiverAvailability: metricsPayload?.reliability?.receiver_availability_percent,
    signalFreshness: metricsPayload?.reliability?.signal_freshness_percent,
    solveTrend: history.map((row) => Number(row.solve_success_percent)).filter((value) => Number.isFinite(value)),
    aircraftTrend: history.map((row) => Number(row.active_aircraft)).filter((value) => Number.isFinite(value)),
  };
}

function renderTrendBlock(title, summary, values, strokeClass) {
  return `
    <article class="mini-chart-card trend-card">
      <div class="mini-chart-head"><strong>${escapePipelineValue(title)}</strong><span>${escapePipelineValue(summary)}</span></div>
      ${window.shellSparkline ? window.shellSparkline(values, { strokeClass }) : '<div class="chart-empty mini-sparkline-empty">No trend</div>'}
    </article>
  `;
}

function renderPipeline(payload, metricsPayload, expandedStageId) {
  const target = document.getElementById('pipeline-panel');
  if (!target) return;
  const liveReady = Boolean(payload.live_evidence_ready);
  const operational = Boolean(payload.pipeline_operational);
  const blockers = Array.isArray(payload.blockers) ? payload.blockers : [];
  const stages = Array.isArray(payload.stages) ? payload.stages : [];
  const passedStages = stages.filter((stage) => stage.status === 'pass').length;
  const progressDenominator = stages.length + blockers.length || 1;
  const progressRatio = Math.max(0, Math.min(1, passedStages / progressDenominator));
  const reasonChips = pipelineReasonChips(payload);
  const history = buildHistorySummary(metricsPayload);

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

      <section class="app-panel pipeline-progress-panel">
        <div class="section-title-row pipeline-progress-head">
          <div><h2>Proof progress</h2><p>Derived from passed stages versus unresolved blockers.</p></div>
          <strong>${Math.round(progressRatio * 100)}%</strong>
        </div>
        <div class="progress-bar-shell"><span style="width:${(progressRatio * 100).toFixed(1)}%"></span></div>
        <div class="reason-chip-row">
          ${reasonChips.map((chip) => `<span class="reason-chip ${escapePipelineValue(chip.tone)}">${escapePipelineValue(chip.label)}</span>`).join('') || '<span class="reason-chip tone-neutral">No explicit proof caveats</span>'}
        </div>
      </section>

      <details class="app-panel pipeline-flow-panel pipeline-disclosure" open>
        <summary class="disclosure-summary disclosure-summary-panel">
          <span>Receiver-to-dashboard trace</span>
          <small>Every stage is derived from the current runtime, database, or published artifact.</small>
        </summary>
        <div class="pipeline-flow-disclosure-head">
          <span class="evidence-status ${payload.provenance?.mode === 'live' ? 'status-pass' : 'status-hold'}">${escapePipelineValue(payload.provenance?.mode || 'unknown')}</span>
        </div>
        <div class="pipeline-flow">
          ${stages.map((stage, index) => renderPipelineStage(stage, index, expandedStageId)).join('')}
        </div>
      </details>

      <section class="pipeline-evidence-grid">
        <div class="app-panel pipeline-blockers">
          <div class="evidence-heading"><div><h2>Why incomplete</h2><p>These conditions prevent a live-data claim.</p></div><span>${blockers.length}</span></div>
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

      <details class="app-panel pipeline-history-panel pipeline-disclosure">
        <summary class="disclosure-summary disclosure-summary-panel">
          <span>Bounded history</span>
          <small>Small live trend summary sourced from <code>/api/evidence/metrics</code>.</small>
        </summary>
        <div class="mini-chart-grid trend-grid">
          ${renderTrendBlock('Solve success', history.solveTrend.length ? `${history.solveTrend[history.solveTrend.length - 1].toFixed(1)}% latest` : 'No samples', history.solveTrend, 'chart-line')}
          ${renderTrendBlock('Active aircraft', history.aircraftTrend.length ? `${Math.round(history.aircraftTrend[history.aircraftTrend.length - 1])} latest` : 'No samples', history.aircraftTrend, 'chart-line tone-cyan')}
        </div>
        <div class="pipeline-history-facts">
          <div><strong>${history.receiverAvailability != null ? `${Number(history.receiverAvailability).toFixed(1)}%` : 'n/a'}</strong><span>receiver availability in sampled window</span></div>
          <div><strong>${history.signalFreshness != null ? `${Number(history.signalFreshness).toFixed(1)}%` : 'n/a'}</strong><span>fresh signal samples in sampled window</span></div>
        </div>
      </details>
    </div>
  `;
}

window.pageHydrators.pipeline = async function ({ fetchJson }) {
  const target = document.getElementById('pipeline-panel');
  if (!target) return;
  let expandedStageId = null;

  const load = async () => {
    const [payload, metricsPayload] = await Promise.all([
      fetchJson('/api/pipeline'),
      fetchJson('/api/evidence/metrics?hours=24&limit=120').catch(() => null),
    ]);
    if (!expandedStageId && Array.isArray(payload?.stages) && payload.stages.length) {
      expandedStageId = payload.stages.find((stage) => stage.status !== 'pass')?.id || payload.stages[0].id;
    }
    renderPipeline(payload, metricsPayload, expandedStageId);
    target.querySelectorAll('[data-stage-id]').forEach((button) => {
      button.addEventListener('click', () => {
        expandedStageId = expandedStageId === button.dataset.stageId ? null : button.dataset.stageId;
        renderPipeline(payload, metricsPayload, expandedStageId);
      });
    });
  };

  await load();
  window.setInterval(() => load().catch(() => null), 10000);
};
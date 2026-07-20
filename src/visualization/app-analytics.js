function escapeAnalyticsValue(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function formatAnalyticsNumber(value, digits = 1) {
  return Number.isFinite(Number(value)) ? Number(value).toFixed(digits) : 'n/a';
}

function formatAnalyticsDate(value) {
  if (!value) return 'n/a';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? escapeAnalyticsValue(value) : date.toLocaleString();
}

function metricPath(report, key) {
  return report?.metrics?.[key] || null;
}

function renderLineChart({ title, detail, rows, key, unit = '', tone = 'orange', digits = 1, band = null }) {
  const points = rows
    .map((row) => ({ timestamp: Number(row.timestamp), value: Number(row[key]) }))
    .filter((point) => Number.isFinite(point.timestamp) && Number.isFinite(point.value));
  if (!points.length) {
    return `<section class="metric-chart-block"><div class="metric-chart-head"><div><h3>${escapeAnalyticsValue(title)}</h3><p>${escapeAnalyticsValue(detail)}</p></div><strong>n/a</strong></div><div class="chart-empty">Waiting for processor samples.</div></section>`;
  }

  const width = 640;
  const height = 180;
  const padX = 22;
  const padY = 20;
  const values = points.map((point) => point.value);
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const range = Math.max(0.0001, maxValue - minValue);
  const toX = (index) => padX + (points.length === 1 ? (width - padX * 2) / 2 : index * (width - padX * 2) / (points.length - 1));
  const toY = (value) => height - padY - ((value - minValue) / range) * (height - padY * 2);
  const coordinates = points.map((point, index) => {
    const x = toX(index);
    const y = toY(point.value);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');
  const firstTime = new Date(points[0].timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const lastTime = new Date(points.at(-1).timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const current = points.at(-1).value;

  let bandMarkup = '';
  if (band?.type === 'central' && points.length > 1) {
    const bandRatio = Number.isFinite(Number(band.ratio)) ? Math.min(Math.max(Number(band.ratio), 0.04), 0.45) : 0.18;
    const inset = range * bandRatio;
    const lowerValue = minValue + inset;
    const upperValue = maxValue - inset;
    if (upperValue > lowerValue) {
      const bandTop = toY(upperValue).toFixed(1);
      const bandHeight = Math.max(0, toY(lowerValue) - toY(upperValue)).toFixed(1);
      bandMarkup = `<rect x="${padX}" y="${bandTop}" width="${width - padX * 2}" height="${bandHeight}" class="chart-range-band"></rect>`;
    }
  }

  return `
    <section class="metric-chart-block">
      <div class="metric-chart-head">
        <div><h3>${escapeAnalyticsValue(title)}</h3><p>${escapeAnalyticsValue(detail)}</p></div>
        <strong>${escapeAnalyticsValue(formatAnalyticsNumber(current, digits))}${escapeAnalyticsValue(unit)}</strong>
      </div>
      <svg class="metric-chart tone-${tone}" viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeAnalyticsValue(title)} history">
        <line x1="${padX}" y1="${padY}" x2="${width - padX}" y2="${padY}" class="chart-grid-line"></line>
        <line x1="${padX}" y1="${height / 2}" x2="${width - padX}" y2="${height / 2}" class="chart-grid-line"></line>
        <line x1="${padX}" y1="${height - padY}" x2="${width - padX}" y2="${height - padY}" class="chart-grid-line"></line>
        ${bandMarkup}
        <polyline points="${coordinates}" class="chart-line"></polyline>
      </svg>
      <div class="metric-chart-axis"><span>${escapeAnalyticsValue(firstTime)}</span><span>${escapeAnalyticsValue(formatAnalyticsNumber(minValue, digits))}${escapeAnalyticsValue(unit)} to ${escapeAnalyticsValue(formatAnalyticsNumber(maxValue, digits))}${escapeAnalyticsValue(unit)}</span><span>${escapeAnalyticsValue(lastTime)}</span></div>
    </section>
  `;
}

function renderBenchmarkEvidence(report) {
  if (!report) {
    return `
      <section class="app-panel evidence-empty">
        <div class="evidence-heading"><div><h2>External accuracy benchmark</h2><p>A trusted reference dataset has not been published yet.</p></div><span class="evidence-status status-hold">Awaiting live data</span></div>
        <p>Accuracy and historical freshness remain unproven until live MLAT output is compared with a named reference source.</p>
        <div class="action-row"><a class="action-chip" href="/api/benchmark/latest">Inspect benchmark API</a></div>
      </section>
    `;
  }

  const publishable = report.evidence_status === 'publishable' && report.provenance?.benchmarkable === true;
  const sample = report.sample || {};
  const accuracy = report.accuracy || {};
  const freshness = report.freshness || {};
  const provenance = report.provenance || {};
  const inputs = report.inputs || {};
  const snapshotReliability = report.runtime_snapshot?.reliability || {};
  const limitations = Array.isArray(provenance.limitations) ? provenance.limitations : [];

  return `
    <section class="app-panel">
      <div class="evidence-heading"><div><h2>${publishable ? 'Published live accuracy evidence' : 'Pipeline validation report'}</h2><p>One-to-one reference matching with hashed source inputs.</p></div><span class="evidence-status ${publishable ? 'status-pass' : 'status-hold'}">${publishable ? 'Publishable' : 'Not claim-ready'}</span></div>
      <div class="evidence-metrics" aria-label="Latest benchmark metrics">
        <div><strong>${formatAnalyticsNumber(accuracy.horizontal_error_median_m, 0)} m</strong><span>Median horizontal error</span></div>
        <div><strong>${formatAnalyticsNumber(accuracy.horizontal_error_p95_m, 0)} m</strong><span>P95 horizontal error</span></div>
        <div><strong>${formatAnalyticsNumber((sample.coverage_ratio_vs_reference || 0) * 100, 1)}%</strong><span>Reference coverage</span></div>
        <div><strong>${escapeAnalyticsValue(sample.matched_records ?? 0)}</strong><span>One-to-one matches</span></div>
        <div><strong>${freshness.end_to_store_age_p95_ms == null ? 'n/a' : `${formatAnalyticsNumber(freshness.end_to_store_age_p95_ms, 0)} ms`}</strong><span>P95 end-to-store age</span></div>
        <div><strong>${escapeAnalyticsValue(snapshotReliability.active_receivers ?? 'n/a')}</strong><span>Receivers at capture</span></div>
      </div>
      <div class="evidence-table-wrap"><table class="app-table"><tbody>
        <tr><th scope="row">Reference</th><td>${escapeAnalyticsValue(provenance.reference_source)}</td></tr>
        <tr><th scope="row">Region</th><td>${escapeAnalyticsValue(provenance.region)}</td></tr>
        <tr><th scope="row">Data provenance</th><td>${escapeAnalyticsValue(provenance.data_provenance)}</td></tr>
        <tr><th scope="row">Generated</th><td>${formatAnalyticsDate(report.generated_at)}</td></tr>
        <tr><th scope="row">MLAT input hash</th><td class="evidence-hash">${escapeAnalyticsValue(inputs.mlat?.sha256?.slice(0, 16) || 'n/a')}</td></tr>
        <tr><th scope="row">Reference input hash</th><td class="evidence-hash">${escapeAnalyticsValue(inputs.reference?.sha256?.slice(0, 16) || 'n/a')}</td></tr>
      </tbody></table></div>
      ${limitations.length ? `<p class="evidence-note"><strong>Limitations:</strong> ${escapeAnalyticsValue(limitations.join(' '))}</p>` : ''}
      <div class="action-row"><a class="action-chip" href="/api/benchmark/latest">Open benchmark JSON</a></div>
    </section>
  `;
}

function renderOperationalEvidence(performance, reliability) {
  const apiLatency = metricPath(performance, 'api_latency_ms');
  const dbInsert = metricPath(performance, 'database_position_insert_ms');
  const registryLookup = metricPath(performance, 'receiver_cache_lookup_ms');
  const throughput = metricPath(performance, 'api_throughput');
  const memory = metricPath(performance, 'process_peak_rss_mb');
  const reliabilityMetrics = reliability?.metrics || {};
  const hasEvidence = performance || reliability;

  if (!hasEvidence) {
    return `<section class="app-panel evidence-empty"><div class="evidence-heading"><div><h2>Operational benchmark artifacts</h2><p>Generate reproducible local performance and reliability reports.</p></div><span class="evidence-status status-hold">Not captured</span></div><p>Run the evidence capture command to publish latency, throughput, memory, and sampled availability.</p></section>`;
  }

  return `
    <section class="app-panel">
      <div class="evidence-heading"><div><h2>Operational benchmark artifacts</h2><p>Reproducible baselines are labeled by environment and data provenance.</p></div><span class="evidence-status ${performance ? 'status-pass' : 'status-hold'}">${performance ? 'Baseline published' : 'Partial evidence'}</span></div>
      <div class="evidence-metrics">
        <div><strong>${apiLatency ? `${formatAnalyticsNumber(apiLatency.median, 2)} ms` : 'n/a'}</strong><span>Median API latency</span></div>
        <div><strong>${apiLatency ? `${formatAnalyticsNumber(apiLatency.p95, 2)} ms` : 'n/a'}</strong><span>P95 API latency</span></div>
        <div><strong>${dbInsert ? `${formatAnalyticsNumber(dbInsert.median, 3)} ms` : 'n/a'}</strong><span>Median DB insert</span></div>
        <div><strong>${registryLookup ? `${formatAnalyticsNumber(registryLookup.median, 3)} ms` : 'n/a'}</strong><span>Receiver cache lookup</span></div>
        <div><strong>${throughput ? `${formatAnalyticsNumber(throughput.requests_per_second, 1)}/s` : 'n/a'}</strong><span>API throughput</span></div>
        <div><strong>${memory ? `${formatAnalyticsNumber(memory.value, 1)} MB` : 'n/a'}</strong><span>Peak process memory</span></div>
        <div><strong>${reliability ? `${formatAnalyticsNumber(reliabilityMetrics.api_availability_percent, 2)}%` : 'n/a'}</strong><span>Sampled API availability</span></div>
        <div><strong>${reliability ? `${formatAnalyticsNumber(reliabilityMetrics.receiver_availability_percent, 2)}%` : 'n/a'}</strong><span>Receiver availability</span></div>
      </div>
      <div class="evidence-table-wrap"><table class="app-table"><tbody>
        <tr><th scope="row">Performance provenance</th><td>${escapeAnalyticsValue(performance?.provenance?.data_provenance || 'not captured')}</td></tr>
        <tr><th scope="row">Performance generated</th><td>${formatAnalyticsDate(performance?.generated_at)}</td></tr>
        <tr><th scope="row">Reliability window</th><td>${reliability ? `${formatAnalyticsNumber(reliabilityMetrics.window_seconds, 0)} seconds, ${escapeAnalyticsValue(reliabilityMetrics.samples)} samples` : 'not captured'}</td></tr>
        <tr><th scope="row">Live-data claim</th><td>${performance?.provenance?.live_data === true ? 'live' : 'no, local operational baseline only'}</td></tr>
      </tbody></table></div>
      <div class="action-row"><a class="action-chip" href="/api/evidence/performance/latest">Open performance JSON</a><a class="action-chip" href="/api/evidence/reliability/latest">Open reliability JSON</a></div>
    </section>
  `;
}

window.pageHydrators.analytics = async function ({ fetchJson, healthData }) {
  const target = document.getElementById('analytics-panel');
  if (!target) return;

  const [readiness, metrics, performance, reliability] = await Promise.all([
    fetchJson('/api/readiness').catch(() => null),
    fetchJson('/api/evidence/metrics?hours=24&limit=500').catch(() => null),
    fetchJson('/api/evidence/performance/latest').catch(() => null),
    fetchJson('/api/evidence/reliability/latest').catch(() => null),
  ]);
  const benchmark = readiness?.external_benchmark?.available
    ? await fetchJson('/api/benchmark/latest').catch(() => null)
    : null;

  if (!readiness || !metrics) {
    target.innerHTML = '<div class="empty-state">Operational metrics are unavailable. Start the processor and API with the same database.</div>';
    return;
  }

  const current = metrics.current || {};
  const history = metrics.history || [];
  const reliabilitySummary = metrics.reliability || {};
  const provenanceLive = metrics.provenance?.live_data === true;

  target.innerHTML = `
    <div class="evidence-stack">
      <section class="app-panel">
        <div class="evidence-heading"><div><h2>Current operating window</h2><p>Processor counters and delivery health from the shared evidence store.</p></div><span class="evidence-status ${provenanceLive ? 'status-pass' : 'status-hold'}">${provenanceLive ? 'Live data' : 'Replay data'}</span></div>
        <div class="evidence-metrics">
          <div><strong>${formatAnalyticsNumber(current.signals_per_minute, 0)}/min</strong><span>Observations</span></div>
          <div><strong>${formatAnalyticsNumber(current.positions_per_minute, 1)}/min</strong><span>Position attempts</span></div>
          <div><strong>${formatAnalyticsNumber(current.solve_success_percent, 1)}%</strong><span>Solve success</span></div>
          <div><strong>${escapeAnalyticsValue(current.active_receivers ?? 0)}</strong><span>Active receivers</span></div>
          <div><strong>${current.last_store_age_s == null ? 'n/a' : `${formatAnalyticsNumber(current.last_store_age_s, 1)} s`}</strong><span>Position age</span></div>
          <div><strong>${formatAnalyticsNumber(current.avg_api_latency_ms, 2)} ms</strong><span>API latency</span></div>
          <div><strong>${formatAnalyticsNumber(current.process_rss_mb, 1)} MB</strong><span>Peak memory</span></div>
          <div><strong>${reliabilitySummary.receiver_availability_percent == null ? 'n/a' : `${formatAnalyticsNumber(reliabilitySummary.receiver_availability_percent, 1)}%`}</strong><span>Receiver availability</span></div>
        </div>
      </section>

      <section class="app-panel metrics-history-panel">
        <div class="evidence-heading"><div><h2>24-hour operational history</h2><p>${escapeAnalyticsValue(metrics.sample_count)} persisted samples. Charts remain provenance-aware.</p></div><span class="evidence-status ${history.length ? 'status-pass' : 'status-hold'}">${history.length ? 'History active' : 'Waiting'}</span></div>
        <div class="metric-chart-grid">
          ${renderLineChart({ title: 'Observation throughput', detail: 'Receiver observations accepted per minute', rows: history, key: 'signals_per_minute', unit: '/min', tone: 'cyan', digits: 0 })}
          ${renderLineChart({ title: 'Position throughput', detail: 'Correlated position attempts per minute', rows: history, key: 'positions_per_minute', unit: '/min', tone: 'orange', digits: 1 })}
          ${renderLineChart({ title: 'Position freshness', detail: 'Age of the latest stored aircraft position', rows: history, key: 'last_store_age_s', unit: ' s', tone: 'green', digits: 1, band: { type: 'central', ratio: 0.22 } })}
          ${renderLineChart({ title: 'Solve latency', detail: 'Average processor solve duration', rows: history, key: 'avg_solve_latency_ms', unit: ' ms', tone: 'orange', digits: 2 })}
          ${renderLineChart({ title: 'Receiver availability', detail: 'Receivers available to the correlation runtime', rows: history, key: 'active_receivers', unit: '', tone: 'cyan', digits: 0, band: { type: 'central', ratio: 0.2 } })}
          ${renderLineChart({ title: 'Process memory', detail: 'Peak resident memory reported by the processor', rows: history, key: 'process_rss_mb', unit: ' MB', tone: 'green', digits: 1, band: { type: 'central', ratio: 0.18 } })}
        </div>
      </section>

      ${renderOperationalEvidence(performance, reliability)}
      ${renderBenchmarkEvidence(benchmark)}

      <section class="app-panel">
        <div class="evidence-heading"><div><h2>Claim ledger</h2><p>Comparative statements stay closed until the required evidence exists.</p></div></div>
        <div class="evidence-table-wrap"><table class="app-table claim-ledger"><thead><tr><th scope="col">Claim</th><th scope="col">Status</th></tr></thead><tbody>
          ${Object.entries(readiness.not_yet_proven || {}).filter(([, value]) => typeof value === 'boolean').map(([key, proven]) => `<tr><th scope="row">${escapeAnalyticsValue(key.replaceAll('_', ' '))}</th><td><span class="evidence-status ${proven ? 'status-pass' : 'status-hold'}">${proven ? 'Proven' : 'Not proven'}</span></td></tr>`).join('')}
        </tbody></table></div>
      </section>
    </div>
  `;
};

function escapeSettingsValue(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function formatSettingsNumber(value, digits = 1) {
  return Number.isFinite(Number(value)) ? Number(value).toFixed(digits) : 'n/a';
}

function formatSettingsBoolean(value, { trueLabel = 'Enabled', falseLabel = 'Disabled', unknownLabel = 'Unknown' } = {}) {
  if (value === true) return trueLabel;
  if (value === false) return falseLabel;
  return unknownLabel;
}

function settingsToneFromStatus(status) {
  if (status === 'ok' || status === 'active' || status === 'ready' || status === 'live') return 'good';
  if (status === 'degraded' || status === 'stale' || status === 'simulation' || status === 'configured_live') return 'warn';
  if (status === 'unavailable') return 'risk';
  return 'warn';
}

function settingsToneFromBoolean(value, { negativeWhenTrue = false } = {}) {
  if (value == null) return 'warn';
  if (negativeWhenTrue) return value ? 'risk' : 'good';
  return value ? 'good' : 'warn';
}

function settingsBadge(label, tone) {
  return `<span class="overview-badge tone-${tone}">${escapeSettingsValue(label)}</span>`;
}

function renderSummaryCard({ label, value, detail, tone = 'warn' }) {
  return `
    <article class="summary-card tone-${tone}">
      <span>${escapeSettingsValue(label)}</span>
      <strong>${escapeSettingsValue(value)}</strong>
      <small>${escapeSettingsValue(detail)}</small>
    </article>
  `;
}

function renderSettingsRow({ label, value, detail, tone = 'warn' }) {
  return `
    <div class="overview-ops-row settings-detail-row">
      <div>
        <strong>${escapeSettingsValue(label)}</strong>
        <span>${escapeSettingsValue(detail)}</span>
      </div>
      <span class="overview-inline-status tone-${tone}">${escapeSettingsValue(value)}</span>
    </div>
  `;
}

function renderSettingsSection({ title, detail, rows, evidence = false }) {
  return `
    <section class="overview-rail-section ${evidence ? 'overview-rail-section-evidence' : ''}">
      <div class="overview-rail-head">
        <div>
          <h2>${escapeSettingsValue(title)}</h2>
          <p>${escapeSettingsValue(detail)}</p>
        </div>
      </div>
      <div class="overview-ops-list">${rows.join('')}</div>
    </section>
  `;
}

window.pageHydrators.settings = async function ({ modeData, fetchJson }) {
  const target = document.getElementById('settings-panel');
  if (!target) return;

  const [health, readiness] = await Promise.all([
    fetchJson('/api/health').catch(() => null),
    fetchJson('/api/readiness').catch(() => null),
  ]);

  const quality = readiness?.dimensions?.quality || {};
  const reliability = readiness?.dimensions?.reliability || {};
  const freshness = health?.freshness || {};
  const broadcaster = health?.broadcaster || {};
  const database = health?.database || {};

  const runtimeStatus = modeData?.runtime_status || 'unknown';
  const modeLabel = modeData?.mode || 'unknown';
  const healthStatus = health?.status || 'unknown';
  const benchmarkableOutput = quality.benchmarkable_output;
  const simulatedPositions = quality.simulated_positions;
  const registryConfigured = Boolean(modeData?.receiver_registry_type_hash);
  const registryLive = modeData?.registry_discovery_live === true;
  const syntheticFeedMode = modeData?.synthetic_feed_mode === true;
  const demoMode = modeData?.demo_mode === true;
  const strictProduction = modeData?.strict_production_mode === true;
  const activeReceivers = reliability.active_receivers;
  const dbSize = database.size_mb;

  const runtimeTone = settingsToneFromStatus(runtimeStatus);
  const healthTone = healthStatus === 'degraded' ? 'warn' : settingsToneFromStatus(healthStatus);
  const evidenceTone = settingsToneFromBoolean(benchmarkableOutput);

  const environmentVerdict = runtimeStatus === 'active'
    ? syntheticFeedMode
      ? 'Processor healthy, but this environment is still running synthetic or replay input.'
      : benchmarkableOutput
        ? 'Runtime is active and current output is usable for evidence workflows.'
        : 'Runtime is active, but evidence quality is still constrained by current output.'
    : runtimeStatus === 'stale'
      ? 'The processor is reachable, but telemetry freshness needs attention before this page can be trusted.'
      : 'The page is configured, but runtime activity is not currently available.';

  const operatorGuidance = syntheticFeedMode
    ? 'Treat this page as operational posture only. Do not use it as proof of live system quality until synthetic input is cleared.'
    : benchmarkableOutput
      ? 'Use this page to confirm the stack is producing live, benchmarkable output before publishing claims or artifacts.'
      : 'Use this page to identify which readiness gate still blocks trustworthy benchmark or claim publication.';

  const blockerCopy = [
    !registryConfigured ? 'Receiver registry is not configured.' : null,
    simulatedPositions > 0 ? `${simulatedPositions} recent positions are still simulated.` : null,
    !benchmarkableOutput ? 'Recent output is not benchmarkable.' : null,
    healthStatus !== 'ok' ? `Health endpoint reports ${healthStatus}.` : null,
  ].filter(Boolean);

  const summaryCards = [
    {
      label: 'Runtime state',
      value: runtimeStatus === 'active' ? 'Active' : runtimeStatus === 'stale' ? 'Stale' : 'Unavailable',
      detail: 'Processor heartbeat and telemetry freshness.',
      tone: runtimeTone,
    },
    {
      label: 'Source posture',
      value: demoMode ? 'Hosted demo' : syntheticFeedMode ? 'Replay / synthetic' : modeLabel.replaceAll('_', ' '),
      detail: syntheticFeedMode ? 'Visible output is not live-source evidence.' : 'Current environment mode exposed by the shell.',
      tone: syntheticFeedMode || demoMode ? 'warn' : settingsToneFromStatus(modeLabel),
    },
    {
      label: 'Evidence readiness',
      value: benchmarkableOutput ? 'Benchmarkable' : 'Constrained',
      detail: benchmarkableOutput ? 'Recent positions can support evidence workflows.' : 'Output is still blocked from trustworthy benchmark use.',
      tone: evidenceTone,
    },
    {
      label: 'System health',
      value: healthStatus === 'ok' ? 'Healthy' : healthStatus,
      detail: Number.isFinite(Number(dbSize)) ? `${formatSettingsNumber(dbSize, 1)} MB evidence store` : 'Health endpoint did not expose database size.',
      tone: healthTone,
    },
  ].map(renderSummaryCard).join('');

  const runtimeRows = [
    renderSettingsRow({
      label: 'Operating mode',
      value: modeLabel.replaceAll('_', ' '),
      detail: demoMode ? 'Hosted demo context is active for this environment.' : 'Top-level shell posture for the current runtime.',
      tone: syntheticFeedMode || demoMode ? 'warn' : settingsToneFromStatus(modeLabel),
    }),
    renderSettingsRow({
      label: 'Configured transport',
      value: modeData?.configured_transport || 'unknown',
      detail: syntheticFeedMode ? 'Transport is currently feeding replay or simulated source material.' : 'Ingress transport selected for source acquisition.',
      tone: syntheticFeedMode ? 'warn' : 'good',
    }),
    renderSettingsRow({
      label: 'Fallback policy',
      value: formatSettingsBoolean(modeData?.simulate_if_unavailable, { trueLabel: 'Simulation allowed', falseLabel: 'Live only', unknownLabel: 'Unknown' }),
      detail: 'Controls whether the stack may fall back to synthetic input when live sources disappear.',
      tone: settingsToneFromBoolean(modeData?.simulate_if_unavailable),
    }),
    renderSettingsRow({
      label: 'Strict production',
      value: formatSettingsBoolean(modeData?.strict_production_mode, { trueLabel: 'Strict live', falseLabel: 'Standard', unknownLabel: 'Unknown' }),
      detail: strictProduction ? 'The stack is configured to prefer strict live posture before claim-ready behavior.' : 'The environment allows a more flexible operational posture.',
      tone: settingsToneFromBoolean(modeData?.strict_production_mode),
    }),
    renderSettingsRow({
      label: 'WebSocket capability',
      value: formatSettingsBoolean(modeData?.websocket_available, { trueLabel: 'Available', falseLabel: 'Unavailable', unknownLabel: 'Unknown' }),
      detail: 'Determines whether the frontend can receive live updates over Socket.IO.',
      tone: settingsToneFromBoolean(modeData?.websocket_available),
    }),
  ];

  const evidenceRows = [
    renderSettingsRow({
      label: 'Registry configuration',
      value: registryConfigured ? 'Configured' : 'Unconfigured',
      detail: registryConfigured ? 'Receiver registry hash is present for participant discovery.' : 'No receiver registry hash is available, so provenance cannot be tied to a configured registry.',
      tone: settingsToneFromBoolean(registryConfigured),
    }),
    renderSettingsRow({
      label: 'Registry discovery',
      value: registryConfigured ? (registryLive ? 'Live' : 'Waiting') : 'Disabled',
      detail: registryConfigured ? 'Shows whether runtime telemetry confirms live discovery against the configured registry.' : 'Discovery cannot become live until registry configuration exists.',
      tone: !registryConfigured ? 'warn' : settingsToneFromBoolean(registryLive),
    }),
    renderSettingsRow({
      label: 'Benchmarkable output',
      value: formatSettingsBoolean(benchmarkableOutput, { trueLabel: 'Yes', falseLabel: 'No', unknownLabel: 'Unknown' }),
      detail: 'Recent positions must be present and non-synthetic before the output can support benchmark publication.',
      tone: evidenceTone,
    }),
    renderSettingsRow({
      label: 'Simulated positions',
      value: simulatedPositions == null ? 'Unknown' : String(simulatedPositions),
      detail: simulatedPositions > 0 ? 'Synthetic positions are currently contaminating the evidence window.' : 'No recent simulated positions are reported in the readiness window.',
      tone: simulatedPositions == null ? 'warn' : simulatedPositions > 0 ? 'risk' : 'good',
    }),
    renderSettingsRow({
      label: 'External benchmark',
      value: readiness?.external_benchmark?.publishable ? 'Publishable' : readiness?.external_benchmark?.available ? 'Captured' : 'Missing',
      detail: readiness?.external_benchmark?.publishable ? 'A publishable external comparison artifact is available.' : 'No publishable external benchmark artifact is currently present.',
      tone: readiness?.external_benchmark?.publishable ? 'good' : 'warn',
    }),
  ];

  const systemRows = [
    renderSettingsRow({
      label: 'Health status',
      value: healthStatus,
      detail: 'Primary API health signal derived from signal freshness and database reachability.',
      tone: healthTone,
    }),
    renderSettingsRow({
      label: 'Latest stored position',
      value: freshness.last_store_age_s == null ? 'n/a' : `${formatSettingsNumber(freshness.last_store_age_s, 1)} s`,
      detail: 'Age of the newest persisted aircraft position in shared storage.',
      tone: freshness.last_store_age_s == null ? 'warn' : freshness.last_store_age_s <= 30 ? 'good' : 'risk',
    }),
    renderSettingsRow({
      label: 'Latest signal',
      value: freshness.last_signal_age_s == null ? 'n/a' : `${formatSettingsNumber(freshness.last_signal_age_s, 1)} s`,
      detail: 'Age of the newest receiver signal seen by runtime telemetry.',
      tone: freshness.last_signal_age_s == null ? 'warn' : freshness.last_signal_age_s <= 30 ? 'good' : 'risk',
    }),
    renderSettingsRow({
      label: 'Receiver freshness',
      value: freshness.receiver_last_seen_age_s == null ? 'n/a' : `${formatSettingsNumber(freshness.receiver_last_seen_age_s, 1)} s`,
      detail: freshness.receiver_stale_count == null ? 'Receiver freshness data is unavailable.' : `${freshness.receiver_stale_count} receivers are currently marked stale.`,
      tone: freshness.receiver_last_seen_age_s == null ? 'warn' : (freshness.receiver_stale_count || 0) > 0 ? 'warn' : 'good',
    }),
    renderSettingsRow({
      label: 'Broadcaster runtime',
      value: broadcaster.enabled ? (broadcaster.started ? 'Broadcasting' : 'Enabled, not started') : 'Disabled',
      detail: broadcaster.websocket_available ? 'Socket transport exists for dashboard hydration.' : 'No socket transport is available for broadcast fan-out.',
      tone: !broadcaster.enabled ? 'warn' : broadcaster.started ? 'good' : 'risk',
    }),
    renderSettingsRow({
      label: 'Active receivers',
      value: activeReceivers == null ? 'n/a' : String(activeReceivers),
      detail: 'Receivers contributing to the current operational readiness window.',
      tone: activeReceivers == null ? 'warn' : activeReceivers >= 4 ? 'good' : 'warn',
    }),
  ];

  target.innerHTML = `
    <div class="evidence-stack settings-shell">
      <section class="app-panel overview-briefing-panel settings-hero-panel">
        <div class="overview-briefing-shell tone-${runtimeTone}">
          <div class="overview-briefing-copy">
            <span class="pipeline-verdict-label">Environment briefing</span>
            <h2>${escapeSettingsValue(environmentVerdict)}</h2>
            <p>${escapeSettingsValue(operatorGuidance)}</p>
          </div>
          <div class="overview-briefing-side">
            ${settingsBadge(runtimeStatus === 'active' ? 'Processor active' : runtimeStatus === 'stale' ? 'Telemetry stale' : 'Runtime unavailable', runtimeTone)}
            ${settingsBadge(benchmarkableOutput ? 'Benchmarkable output' : 'Evidence constrained', evidenceTone)}
            ${settingsBadge(healthStatus === 'ok' ? 'System healthy' : `Health ${healthStatus}`, healthTone)}
          </div>
        </div>
        <div class="overview-briefing-grid settings-briefing-grid">
          <div class="briefing-note">
            <strong>What this page should answer</strong>
            <span>This surface should tell an operator whether the environment is live enough, fresh enough, and trustworthy enough to support evidence or claim workflows.</span>
          </div>
          <div class="briefing-note">
            <strong>Current blockers</strong>
            <span>${escapeSettingsValue(blockerCopy.length ? blockerCopy.join(' ') : 'No major blockers are currently exposed by mode, health, or readiness data.')}</span>
          </div>
        </div>
      </section>

      <section class="settings-summary-panel">
        <div class="summary-card-grid settings-summary-grid">${summaryCards}</div>
      </section>

      <div class="app-grid two-col settings-detail-layout">
        <section class="app-panel ops-rail settings-rail-panel">
          ${renderSettingsSection({
            title: 'Runtime posture',
            detail: 'How the environment is configured to run and what kind of source material it is using.',
            rows: runtimeRows,
          })}
        </section>

        <section class="app-panel ops-rail settings-rail-panel">
          ${renderSettingsSection({
            title: 'Evidence posture',
            detail: 'Whether the current output can support benchmark artifacts, trust claims, and provenance-sensitive reporting.',
            rows: evidenceRows,
            evidence: true,
          })}

          ${renderSettingsSection({
            title: 'System health',
            detail: 'Freshness, storage, and broadcaster state needed for operators to trust the surrounding dashboard.',
            rows: systemRows,
          })}
        </section>
      </div>
    </div>
  `;
};

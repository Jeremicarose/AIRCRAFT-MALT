function overviewValue(value, fallback = 'n/a') {
  return value === null || value === undefined || value === '' ? fallback : value;
}

function overviewAge(value) {
  return value !== null && value !== undefined && Number.isFinite(Number(value))
    ? `${Math.round(Number(value))}s`
    : 'n/a';
}

function overviewEscape(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function overviewPercent(value) {
  if (!Number.isFinite(Number(value))) return 'n/a';
  return `${Math.round(Number(value) * 100)}%`;
}

function overviewRelativeAge(timestamp) {
  if (!Number.isFinite(Number(timestamp))) return 'n/a';
  const seconds = Math.max(0, Math.round((Date.now() / 1000) - Number(timestamp)));
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m ago`;
  return `${Math.round(seconds / 3600)}h ago`;
}

function overviewStatusTone(status) {
  if (['good', 'pass', 'live', 'healthy', 'ready', 'publishable', 'fresh'].includes(status)) return 'good';
  if (['info', 'selected', 'active'].includes(status)) return 'info';
  if (['bad', 'fail', 'down', 'degraded', 'blocked', 'missing', 'stale', 'unavailable'].includes(status)) return 'risk';
  return 'warn';
}

function overviewBadge(label, status) {
  return `<span class="overview-badge tone-${overviewStatusTone(status)}">${overviewEscape(label)}</span>`;
}

function overviewMetricStateClass(status) {
  return `is-${overviewStatusTone(status)}`;
}

function summarizeMode(modeData) {
  const runtimeStatus = modeData?.runtime_status || 'unavailable';
  const isDemo = Boolean(modeData?.demo_mode);
  const isSynthetic = Boolean(modeData?.synthetic_feed_mode);
  const isSimulation = Boolean(modeData?.simulation_mode || isSynthetic);
  const isLive = runtimeStatus === 'active' && !isDemo && !isSimulation;
  const isStale = runtimeStatus === 'stale';
  const isUnavailable = !isLive && !isDemo && !isSimulation && runtimeStatus !== 'active';

  let sourceKind = 'unavailable';
  let sourceLabel = 'Unavailable';
  let sourceSummary = 'The overview cannot confirm a current output source.';
  let feedMeaning = 'No fresh runtime output is available to display.';

  if (isLive) {
    sourceKind = 'live';
    sourceLabel = 'Live feed';
    sourceSummary = 'Receiver input is actively producing live MLAT output.';
    feedMeaning = 'Current positions are expected to reflect live traffic.';
  } else if (isDemo) {
    sourceKind = 'replay';
    sourceLabel = 'Replay feed';
    sourceSummary = overviewValue(modeData?.scenario?.summary, 'Recorded traffic is being replayed through the current runtime.');
    feedMeaning = 'Replay output is visible, but it should not be interpreted as live traffic.';
  } else if (isSimulation) {
    sourceKind = 'synthetic';
    sourceLabel = 'Synthetic feed';
    sourceSummary = 'Synthetic or simulated traffic is driving the current runtime.';
    feedMeaning = 'Synthetic output is useful for demonstration and validation, not live operations.';
  } else if (isStale) {
    sourceKind = 'stale';
    sourceLabel = 'Stale runtime';
    sourceSummary = 'The runtime was configured, but fresh solved output is no longer arriving.';
    feedMeaning = 'The operator should verify receiver input, solver freshness, and downstream storage.';
  }

  return {
    runtimeStatus,
    isDemo,
    isSynthetic,
    isSimulation,
    isLive,
    isStale,
    isUnavailable,
    sourceKind,
    sourceLabel,
    sourceSummary,
    feedMeaning,
    benchmarkableOutput: Boolean(modeData?.benchmarkable_output),
    strictProductionMode: Boolean(modeData?.strict_production_mode),
    registryConfigured: Boolean(modeData?.receiver_registry_type_hash),
  };
}

function buildOverviewState({ modeData, healthData, aircraftData, receiverData, readiness, benchmark, positionsData }) {
  const mode = summarizeMode(modeData);
  const receivers = Array.isArray(receiverData?.receivers) ? receiverData.receivers : [];
  const positions = Array.isArray(positionsData?.positions) ? positionsData.positions : [];
  const readinessFreshness = readiness?.dimensions?.freshness || {};
  const readinessReliability = readiness?.dimensions?.reliability || {};
  const readinessQuality = readiness?.dimensions?.quality || {};
  const healthFreshness = healthData?.freshness || {};
  const latestByAircraft = new Map();
  [...positions]
    .sort((a, b) => Number(b.timestamp || 0) - Number(a.timestamp || 0))
    .forEach((position) => {
      if (!latestByAircraft.has(position.aircraft_id)) latestByAircraft.set(position.aircraft_id, position);
    });
  const recentAircraft = [...latestByAircraft.values()];
  const aircraftCount = Number.isFinite(Number(aircraftData?.count)) ? Number(aircraftData.count) : recentAircraft.length;
  const activeReceiverCount = Number.isFinite(Number(readinessReliability.active_receivers))
    ? Number(readinessReliability.active_receivers)
    : receivers.filter((receiver) => ['active', 'online'].includes(String(receiver.status || '').toLowerCase())).length;
  const receiverCount = Number.isFinite(Number(receiverData?.count)) ? Number(receiverData.count) : receivers.length;
  const lastSignalAge = Number.isFinite(Number(healthFreshness.last_signal_age_s)) ? Number(healthFreshness.last_signal_age_s) : null;
  const lastStoreAge = Number.isFinite(Number(readinessFreshness.last_store_age_s)) ? Number(readinessFreshness.last_store_age_s) : null;
  const avgQuality = Number.isFinite(Number(readinessQuality.avg_quality_score)) ? Number(readinessQuality.avg_quality_score) : null;
  const avgResidual = Number.isFinite(Number(readinessQuality.avg_solver_residual_m)) ? Number(readinessQuality.avg_solver_residual_m) : null;
  const avgUncertainty = Number.isFinite(Number(readinessQuality.avg_uncertainty_m)) ? Number(readinessQuality.avg_uncertainty_m) : null;
  const recentPositionCount = Number.isFinite(Number(readinessQuality.recent_position_count)) ? Number(readinessQuality.recent_position_count) : recentAircraft.length;
  const failedSolves = Number.isFinite(Number(readinessReliability.failed_solves)) ? Number(readinessReliability.failed_solves) : null;
  const benchmarkStatus = benchmark?.evidence_status || readiness?.external_benchmark?.status || 'missing';
  const notYetProven = Array.isArray(readiness?.not_yet_proven) ? readiness.not_yet_proven : [];
  const benchmarkableOutput = Boolean(readinessQuality.benchmarkable_output ?? mode.benchmarkableOutput);
  const mapCenter = modeData?.scenario?.map?.center || { latitude: 40.82, longitude: -74.35 };
  const mapZoom = modeData?.scenario?.map?.zoom || 7;

  const aircraftStatus = aircraftCount > 0
    ? (lastStoreAge !== null && lastStoreAge <= 20 ? 'healthy' : lastStoreAge !== null && lastStoreAge <= 90 ? 'waiting' : 'stale')
    : (mode.isLive ? 'waiting' : mode.isDemo || mode.isSimulation ? 'waiting' : 'unavailable');

  const feedStatus = lastSignalAge !== null
    ? (lastSignalAge <= 15 ? (mode.isLive ? 'fresh' : 'expected') : lastSignalAge <= 60 ? 'waiting' : 'stale')
    : (mode.isUnavailable ? 'unavailable' : 'waiting');

  const runtimeComponents = {
    processor: modeData?.runtime_status === 'active' ? 'Active' : modeData?.runtime_status === 'stale' ? 'Stale' : 'Unavailable',
    api: healthData?.status === 'ok' ? 'Healthy' : overviewValue(healthData?.status, 'Unknown').replace(/_/g, ' '),
    database: lastStoreAge !== null ? (lastStoreAge <= 30 ? 'Current' : lastStoreAge <= 120 ? 'Lagging' : 'Stale') : 'Unknown',
  };

  const runtimeHealthyCount = [
    runtimeComponents.processor === 'Active',
    runtimeComponents.api === 'Healthy',
    runtimeComponents.database === 'Current',
  ].filter(Boolean).length;

  let operatorVerdict = 'No trustworthy output is visible yet.';
  let operatorTone = 'risk';
  let nextQuestion = 'Trace pipeline blockers';
  let nextHref = '/app/pipeline.html';
  let nextCopy = 'Inspect the receiver-to-dashboard chain and evidence gates.';

  if (mode.isLive && aircraftCount > 0 && activeReceiverCount > 0 && benchmarkableOutput) {
    operatorVerdict = 'Live output is flowing and currently looks benchmarkable.';
    operatorTone = 'good';
    nextQuestion = 'Investigate live positions';
    nextHref = '/app/localization.html';
    nextCopy = 'Inspect current aircraft tracks and contributing receivers on the live map.';
  } else if ((mode.isDemo || mode.isSimulation) && aircraftCount > 0) {
    operatorVerdict = 'Replay feed is visible, but the output should be treated as non-live proof.';
    operatorTone = 'warn';
    nextQuestion = 'Review evidence gates';
    nextHref = '/app/analytics.html';
    nextCopy = 'Confirm whether replay or synthetic output is clearly separated from live evidence.';
  } else if (aircraftCount > 0 && !benchmarkableOutput) {
    operatorVerdict = 'Aircraft are being tracked, but the output is not yet ready to claim as benchmarkable.';
    operatorTone = 'warn';
    nextQuestion = 'Review evidence gates';
    nextHref = '/app/analytics.html';
    nextCopy = 'Check which benchmark or readiness conditions are still missing.';
  } else if (activeReceiverCount > 0 && aircraftCount === 0) {
    operatorVerdict = 'Receivers are visible, but the system is not currently producing recent aircraft solves.';
    operatorTone = 'warn';
    nextQuestion = 'Investigate live positions';
    nextHref = '/app/localization.html';
    nextCopy = 'Check whether timing input is fresh and whether the solver is producing positions.';
  }

  return {
    mode,
    receivers,
    recentAircraft,
    aircraftCount,
    activeReceiverCount,
    receiverCount,
    lastSignalAge,
    lastStoreAge,
    avgQuality,
    avgResidual,
    avgUncertainty,
    recentPositionCount,
    failedSolves,
    benchmarkStatus,
    notYetProven,
    benchmarkableOutput,
    mapCenter,
    mapZoom,
    aircraftStatus,
    feedStatus,
    runtimeComponents,
    runtimeHealthyCount,
    operatorVerdict,
    operatorTone,
    nextQuestion,
    nextHref,
    nextCopy,
  };
}

function buildMetricCards(state) {
  return [
    {
      id: 'aircraft',
      label: 'Aircraft tracked',
      statusText: state.aircraftStatus === 'healthy' ? 'Current' : state.aircraftStatus === 'waiting' ? 'Watching' : state.aircraftCount > 0 ? 'Stale' : 'No solves',
      status: state.aircraftStatus === 'healthy' ? 'good' : state.aircraftStatus === 'waiting' ? 'warn' : 'risk',
      value: String(state.aircraftCount),
      supporting: state.recentPositionCount > 0 ? `${state.recentPositionCount} recent positions` : 'No recent solved positions',
      detail: state.aircraftCount > 0 ? `Store age ${overviewAge(state.lastStoreAge)}` : 'Solver output window',
      href: '/app/aircraft.html',
      action: 'Inspect aircraft',
    },
    {
      id: 'receivers',
      label: 'Receivers active',
      statusText: state.receiverCount === 0 ? 'Missing' : state.activeReceiverCount === state.receiverCount ? 'Healthy' : state.activeReceiverCount > 0 ? 'Partial' : 'Offline',
      status: state.receiverCount === 0 ? 'risk' : state.activeReceiverCount === state.receiverCount ? 'good' : state.activeReceiverCount > 0 ? 'warn' : 'risk',
      value: state.receiverCount ? `${state.activeReceiverCount}/${state.receiverCount}` : '0/0',
      supporting: state.receiverCount ? `${Math.round((state.activeReceiverCount / state.receiverCount) * 100)}% active` : 'No receiver records',
      detail: 'Receiver participation in current readiness window',
      href: '/app/receivers.html',
      action: 'Inspect receivers',
    },
    {
      id: 'feed',
      label: 'Signal freshness',
      statusText: state.feedStatus === 'fresh' ? 'Fresh' : state.feedStatus === 'expected' || state.feedStatus === 'waiting' ? 'Watching' : 'Stale',
      status: state.feedStatus === 'fresh' ? 'good' : state.feedStatus === 'expected' || state.feedStatus === 'waiting' ? 'warn' : 'risk',
      value: state.lastSignalAge !== null ? overviewAge(state.lastSignalAge) : 'n/a',
      supporting: state.lastSignalAge !== null ? 'Latest signal age' : state.mode.feedMeaning,
      detail: state.lastSignalAge !== null ? 'Incoming signal clock' : 'No live freshness sample',
      href: '/app/pipeline.html',
      action: 'Review pipeline',
    },
    {
      id: 'trust',
      label: 'Trust state',
      statusText: state.benchmarkableOutput ? 'Benchmarkable' : 'Evidence pending',
      status: state.benchmarkableOutput ? 'good' : state.mode.isLive ? 'warn' : 'warn',
      value: state.benchmarkableOutput ? 'Ready' : 'Check',
      supporting: state.benchmarkableOutput ? 'Output can support benchmark interpretation' : 'Evidence still needs review',
      detail: `${state.runtimeHealthyCount}/3 runtime checks nominal`,
      href: '/app/analytics.html',
      action: 'Review evidence',
    },
  ];
}

function renderMetricCards(state) {
  const cards = buildMetricCards(state);
  const target = document.getElementById('overview-metrics');
  if (!target) return;
  target.innerHTML = cards.map((card) => `
    <article class="metric-card ${overviewMetricStateClass(card.status)}" data-card-id="${overviewEscape(card.id)}">
      <div class="metric-card-head">
        <strong>${overviewEscape(card.label)}</strong>
        <span class="metric-status tone-${overviewStatusTone(card.status)}">${overviewEscape(card.statusText)}</span>
      </div>
      <span class="metric-value">${overviewEscape(card.value)}</span>
      <small class="metric-supporting">${overviewEscape(card.supporting)}</small>
      <div class="metric-card-foot">
        <small>${overviewEscape(card.detail)}</small>
        <a class="metric-card-link" href="${overviewEscape(card.href)}">${overviewEscape(card.action)}</a>
      </div>
    </article>
  `).join('');
}

function briefingFreshnessLine(state) {
  if (state.lastSignalAge !== null) return `${state.mode.sourceLabel} · last signal ${overviewAge(state.lastSignalAge)} · store ${overviewAge(state.lastStoreAge)}`;
  return `${state.mode.sourceLabel} · ${state.mode.feedMeaning}`;
}

function briefingWarnings(state) {
  const warnings = [];
  if (state.mode.isDemo) warnings.push('Replay mode is visible; do not treat the map as live traffic.');
  if (state.mode.isSimulation) warnings.push('Synthetic traffic is visible; keep it separate from operational evidence.');
  if (state.lastSignalAge !== null && state.lastSignalAge > 60) warnings.push('Signal freshness has drifted beyond the normal watch window.');
  if (state.aircraftCount === 0 && state.activeReceiverCount > 0) warnings.push('Receivers are reporting, but recent aircraft solves are missing.');
  if (!state.benchmarkableOutput && state.mode.isLive) warnings.push('Live output is visible, but benchmark readiness is still incomplete.');
  return warnings.slice(0, 2);
}

function renderBriefing(state) {
  const verdict = document.getElementById('overview-briefing');
  if (!verdict) return;

  const blockers = state.notYetProven.length
    ? state.notYetProven.slice(0, 5).map((item) => `<li>${overviewEscape(String(item).replaceAll('_', ' '))}</li>`).join('')
    : '<li>No open readiness caveats reported.</li>';
  const warnings = briefingWarnings(state);
  const warningMarkup = warnings.length
    ? `<div class="overview-briefing-alerts">${warnings.map((warning) => `<p>${overviewEscape(warning)}</p>`).join('')}</div>`
    : '';

  verdict.innerHTML = `
    <div class="overview-briefing-shell tone-${overviewStatusTone(state.operatorTone)}">
      <div class="overview-briefing-copy">
        <span class="pipeline-verdict-label">Operational summary</span>
        <h2>${overviewEscape(state.operatorVerdict)}</h2>
        <p>${overviewEscape(briefingFreshnessLine(state))}</p>
        ${warningMarkup}
      </div>
    </div>
    <details class="inspector-disclosure overview-briefing-disclosure">
      <summary class="disclosure-summary">
        <span>Why this verdict</span>
        <small>Definitions, trust blockers, and operator guidance.</small>
      </summary>
      <div class="disclosure-body overview-briefing-disclosure-body">
        <div class="overview-briefing-grid overview-briefing-grid-compact">
          <div class="briefing-note briefing-note-callout">
            <strong>Source context</strong>
            <span>${overviewEscape(state.mode.sourceSummary)}</span>
          </div>
          <div class="briefing-note briefing-note-callout">
            <strong>Next check</strong>
            <span>${overviewEscape(state.nextCopy)}</span>
          </div>
          <div class="briefing-note briefing-note-list">
            <strong>Trust blockers</strong>
            <ul>${blockers}</ul>
          </div>
        </div>
      </div>
    </details>
  `;
}

function classifyQuality(position) {
  const score = Number(position?.quality?.score);
  if (!Number.isFinite(score)) return 'unknown';
  if (score >= 0.8) return 'good';
  if (score >= 0.55) return 'warn';
  return 'risk';
}

function qualityLabel(position) {
  const bucket = overviewValue(position?.quality?.bucket, 'unknown');
  const score = overviewPercent(position?.quality?.score);
  return `${score} · ${bucket}`;
}

function uncertaintyLabel(position) {
  return Number.isFinite(Number(position?.uncertainty)) ? `±${Math.round(Number(position.uncertainty))}m` : 'n/a';
}

function residualLabel(position) {
  return Number.isFinite(Number(position?.solver?.residual_m)) ? `${Number(position.solver.residual_m).toFixed(1)}m` : 'n/a';
}

function receiverIdsForPosition(position) {
  return Array.isArray(position?.correlation?.receiver_ids) ? position.correlation.receiver_ids : [];
}

function buildOverviewMap(target, state) {
  if (!target || !window.L) return null;
  const map = L.map(target, { zoomControl: false, attributionControl: true })
    .setView([state.mapCenter.latitude, state.mapCenter.longitude], state.mapZoom);
  L.control.zoom({ position: 'bottomleft' }).addTo(map);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '© OpenStreetMap © CARTO',
    subdomains: 'abcd',
    maxZoom: 20,
  }).addTo(map);

  return {
    map,
    receiverMarkers: new Map(),
    aircraftMarkers: new Map(),
    relationshipLines: [],
    confidenceCircle: null,
    selectedAircraftId: null,
  };
}

function clearOverviewRelationships(mapState) {
  mapState.relationshipLines.forEach((line) => mapState.map.removeLayer(line));
  mapState.relationshipLines = [];
  if (mapState.confidenceCircle) {
    mapState.map.removeLayer(mapState.confidenceCircle);
    mapState.confidenceCircle = null;
  }
}

function relationshipStyle(selected = false) {
  return {
    color: selected ? 'rgba(110, 176, 255, 0.88)' : 'rgba(110, 176, 255, 0.4)',
    weight: selected ? 2.4 : 1.4,
    opacity: 1,
    dashArray: selected ? '9 6' : '6 8',
    lineCap: 'round',
    interactive: false,
    className: selected ? 'overview-relationship-line is-selected' : 'overview-relationship-line',
  };
}

function renderOverviewMapHud(state) {
  const status = document.getElementById('overview-map-status');
  const story = document.getElementById('overview-map-story');
  const legend = document.getElementById('overview-map-legend');
  if (status) {
    const label = state.aircraftCount > 0
      ? `${state.mode.sourceLabel} · ${state.aircraftCount} tracked`
      : state.receiverCount > 0
        ? `${state.mode.sourceLabel} · solves pending`
        : `${state.mode.sourceLabel} · awaiting telemetry`;
    status.textContent = label;
    status.className = `map-hud-status tone-${overviewStatusTone(state.mode.isLive ? 'good' : state.mode.isDemo || state.mode.isSimulation ? 'warn' : 'risk')}`;
  }
  if (story) {
    const receiverLinkCount = state.recentAircraft.reduce((sum, position) => sum + receiverIdsForPosition(position).length, 0);
    story.textContent = receiverLinkCount > 0
      ? `${receiverLinkCount} receiver links support the visible solves.`
      : 'Map shows current solves and selected evidence detail.';
  }
  if (legend) {
    legend.innerHTML = `
      <span><i class="legend-dot aircraft"></i>Aircraft</span>
      <span><i class="legend-dot receiver"></i>Receiver</span>
      <span><i class="legend-dot link"></i>Selection</span>
      <span><i class="legend-dot confidence"></i>Error band</span>
    `;
  }
}

function selectedAircraftSummary(position) {
  if (!position) {
    return `
      <div class="overview-selection-empty">
        <strong>Select an aircraft</strong>
        <span>Choose a solve on the map to inspect quality, receiver participation, and estimated error.</span>
      </div>
    `;
  }
  const receiverIds = receiverIdsForPosition(position);
  return `
    <div class="overview-selection-card tone-${classifyQuality(position)}">
      <div class="overview-selection-head">
        <div>
          <strong>${overviewEscape(position.aircraft_id)}</strong>
          <span>${overviewEscape(overviewRelativeAge(position.timestamp))}</span>
        </div>
        <span class="overview-selection-state tone-info">Selected</span>
      </div>
      <div class="overview-selection-grid">
        <div><span>Quality</span><strong>${overviewEscape(qualityLabel(position))}</strong></div>
        <div><span>Error</span><strong>${overviewEscape(uncertaintyLabel(position))}</strong></div>
        <div><span>Residual</span><strong>${overviewEscape(residualLabel(position))}</strong></div>
        <div><span>Receivers</span><strong>${overviewEscape(String(position.num_receivers || receiverIds.length || 0))}</strong></div>
      </div>
      <p>${overviewEscape(receiverIds.length
        ? 'Highlighted links show the named receivers behind this solve.'
        : 'No explicit receiver IDs were attached to this solve, so no links are drawn.')}</p>
      <a class="metric-card-link" href="/app/aircraft.html">Inspect aircraft detail</a>
    </div>
  `;
}

function renderSelectedAircraftCard(position) {
  const target = document.getElementById('overview-selected-aircraft');
  if (!target) return;
  target.innerHTML = selectedAircraftSummary(position);
}

function receiverPopup(receiver) {
  return `<strong>${overviewEscape(receiver.receiver_id)}</strong><br>${overviewEscape(receiver.status)} receiver`;
}

function aircraftPopup(position) {
  return `<strong>${overviewEscape(position.aircraft_id)}</strong><br>${overviewEscape(qualityLabel(position))} · ${overviewEscape(uncertaintyLabel(position))}<br>${overviewEscape(String(position.num_receivers || receiverIdsForPosition(position).length || 0))} receivers`;
}

function updateMapSelection(mapState, state) {
  const selectedId = mapState.selectedAircraftId;
  const selectedPosition = selectedId ? state.recentAircraft.find((item) => item.aircraft_id === selectedId) : null;
  const relatedReceiverIds = new Set(receiverIdsForPosition(selectedPosition));
  clearOverviewRelationships(mapState);

  mapState.aircraftMarkers.forEach((marker, aircraftId) => {
    const node = marker.getElement()?.querySelector('.overview-aircraft-marker');
    if (!node) return;
    node.classList.toggle('is-selected', aircraftId === selectedId);
    node.classList.toggle('is-dimmed', Boolean(selectedId) && aircraftId !== selectedId);
  });

  mapState.receiverMarkers.forEach((marker, receiverId) => {
    const node = marker.getElement()?.querySelector('.overview-receiver-marker');
    if (!node) return;
    node.classList.toggle('is-related', relatedReceiverIds.has(receiverId));
    node.classList.toggle('is-dimmed', Boolean(selectedId) && !relatedReceiverIds.has(receiverId));
  });

  if (selectedPosition) {
    receiverIdsForPosition(selectedPosition).forEach((receiverId) => {
      const receiver = state.receivers.find((item) => item.receiver_id === receiverId);
      if (!receiver) return;
      const line = L.polyline([
        [receiver.latitude, receiver.longitude],
        [selectedPosition.position.latitude, selectedPosition.position.longitude],
      ], relationshipStyle(true)).addTo(mapState.map);
      mapState.relationshipLines.push(line);
    });

    if (Number.isFinite(Number(selectedPosition.uncertainty)) && Number(selectedPosition.uncertainty) > 0) {
      mapState.confidenceCircle = L.circle([
        selectedPosition.position.latitude,
        selectedPosition.position.longitude,
      ], {
        radius: Number(selectedPosition.uncertainty),
        color: 'rgba(110, 176, 255, 0.92)',
        weight: 1,
        fillColor: 'rgba(110, 176, 255, 0.14)',
        fillOpacity: 1,
        className: 'overview-confidence-circle',
        interactive: false,
      }).addTo(mapState.map);
    }
  }

  renderSelectedAircraftCard(selectedPosition);
}

function selectAircraft(mapState, state, aircraftId, center = true) {
  mapState.selectedAircraftId = aircraftId;
  updateMapSelection(mapState, state);
  const marker = mapState.aircraftMarkers.get(aircraftId);
  if (center && marker) {
    mapState.map.setView(marker.getLatLng(), Math.max(mapState.map.getZoom(), 8));
    marker.openPopup();
  }
}

function renderOverviewMap(mapState, state) {
  renderOverviewMapHud(state);
  mapState.receiverMarkers.forEach((marker) => mapState.map.removeLayer(marker));
  mapState.aircraftMarkers.forEach((marker) => mapState.map.removeLayer(marker));
  mapState.receiverMarkers.clear();
  mapState.aircraftMarkers.clear();
  clearOverviewRelationships(mapState);

  const receiverIcon = L.divIcon({
    className: 'overview-receiver-icon-shell',
    html: '<div class="overview-receiver-marker"></div>',
    iconSize: [14, 14],
  });
  const aircraftIcon = L.divIcon({
    className: 'overview-aircraft-icon-shell',
    html: '<div class="overview-aircraft-marker"></div>',
    iconSize: [16, 16],
  });

  const points = [];
  state.receivers.forEach((receiver) => {
    if (!Number.isFinite(Number(receiver.latitude)) || !Number.isFinite(Number(receiver.longitude))) return;
    const marker = L.marker([receiver.latitude, receiver.longitude], { icon: receiverIcon })
      .bindPopup(receiverPopup(receiver))
      .addTo(mapState.map);
    mapState.receiverMarkers.set(receiver.receiver_id, marker);
    points.push([receiver.latitude, receiver.longitude]);
  });

  state.recentAircraft.forEach((position) => {
    const latitude = position?.position?.latitude;
    const longitude = position?.position?.longitude;
    if (!Number.isFinite(Number(latitude)) || !Number.isFinite(Number(longitude))) return;
    const marker = L.marker([latitude, longitude], { icon: aircraftIcon })
      .bindPopup(aircraftPopup(position))
      .addTo(mapState.map)
      .on('click', () => selectAircraft(mapState, state, position.aircraft_id));
    mapState.aircraftMarkers.set(position.aircraft_id, marker);
    points.push([latitude, longitude]);
  });

  if (points.length) {
    mapState.map.fitBounds(points, { padding: [50, 50], maxZoom: 9 });
  }

  const selectionStillVisible = mapState.selectedAircraftId && mapState.aircraftMarkers.has(mapState.selectedAircraftId);
  if (!selectionStillVisible) {
    mapState.selectedAircraftId = state.recentAircraft[0]?.aircraft_id || null;
  }
  updateMapSelection(mapState, state);
  window.setTimeout(() => mapState.map.invalidateSize(), 50);
}

function railRow(label, value, tone = 'warn', detail = '') {
  return `
    <div class="overview-ops-row">
      <div>
        <strong>${overviewEscape(label)}</strong>
        ${detail ? `<span>${overviewEscape(detail)}</span>` : ''}
      </div>
      <span class="overview-inline-status tone-${overviewStatusTone(tone)}">${overviewEscape(value)}</span>
    </div>
  `;
}

function railLinks(links = []) {
  if (!links.length) return '';
  return `
    <details class="overview-links-disclosure">
      <summary class="overview-links-summary">More routes</summary>
      <div class="overview-section-links">
        ${links.map((link) => `<a class="overview-text-link" href="${overviewEscape(link.href)}">${overviewEscape(link.label)}</a>`).join('')}
      </div>
    </details>
  `;
}

function railAction(action) {
  if (!action) return '';
  return `
    <div class="overview-section-action">
      <a class="action-chip action-chip-primary" href="${overviewEscape(action.href)}">${overviewEscape(action.label)}</a>
      <p>${overviewEscape(action.copy)}</p>
    </div>
  `;
}

function evidenceMeaning(state) {
  if (state.mode.isLive && state.benchmarkableOutput) return 'Live output is visible and currently marked benchmarkable.';
  if (state.mode.isDemo) return 'Replay output is visible but should remain separate from live proof.';
  if (state.mode.isSimulation) return 'Synthetic output is visible but not publishable as live evidence.';
  return 'The current output cannot yet be treated as trustworthy benchmark evidence.';
}

function runtimeAction(state) {
  if (state.runtimeHealthyCount === 3) {
    return {
      label: 'Open settings',
      href: '/app/settings.html',
      copy: 'Confirm the active runtime configuration and mode assumptions.',
    };
  }
  return {
    label: 'Review pipeline',
    href: '/app/pipeline.html',
    copy: 'Inspect processor, storage, and freshness checkpoints that are keeping the runtime from serving current output.',
  };
}

function trackingAction(state) {
  if (state.aircraftCount > 0) {
    return {
      label: 'Inspect aircraft',
      href: '/app/aircraft.html',
      copy: 'Move from this summary into the aircraft list to inspect individual tracks and freshness.',
    };
  }
  if (state.activeReceiverCount > 0) {
    return {
      label: 'Open live map',
      href: '/app/localization.html',
      copy: 'Verify whether receivers are feeding the solver but positions are failing to materialize.',
    };
  }
  return {
    label: 'Inspect receivers',
    href: '/app/receivers.html',
    copy: 'Check receiver availability and whether any participants are online at all.',
  };
}

function solverAction(state) {
  if (state.avgQuality !== null && state.avgQuality >= 0.8 && (state.failedSolves === 0 || state.failedSolves === null)) {
    return {
      label: 'Open live map',
      href: '/app/localization.html',
      copy: 'Use the map to inspect current solves while quality and residuals remain in bounds.',
    };
  }
  return {
    label: 'Check metrics',
    href: '/app/analytics.html',
    copy: 'Review solve quality, residuals, and failed solve counts before trusting current tracks.',
  };
}

function trustAction(state) {
  if (state.benchmarkableOutput) {
    return {
      label: 'Review evidence gates',
      href: '/app/analytics.html',
      copy: 'Confirm the evidence trail behind the current benchmarkable state.',
    };
  }
  return {
    label: state.nextQuestion,
    href: state.nextHref,
    copy: state.nextCopy,
  };
}

function renderRail(state) {
  const target = document.getElementById('overview-ops-rail');
  if (!target) return;

  const runtimeRows = [
    railRow('Processor', state.runtimeComponents.processor, state.runtimeComponents.processor === 'Active' ? 'good' : state.runtimeComponents.processor === 'Stale' ? 'warn' : 'risk', 'Solver runtime state'),
    railRow('API', state.runtimeComponents.api, state.runtimeComponents.api === 'Healthy' ? 'good' : 'risk', 'Overview data surface'),
    railRow('Database', state.runtimeComponents.database, state.runtimeComponents.database === 'Current' ? 'good' : state.runtimeComponents.database === 'Lagging' ? 'warn' : 'risk', 'Stored output freshness'),
    railRow('Source', overviewValue(state.mode.runtimeStatus, 'unknown'), state.mode.isLive ? 'good' : state.mode.isDemo || state.mode.isSimulation ? 'warn' : 'risk', state.mode.sourceLabel),
  ].join('');

  const trackingRows = [
    railRow('Aircraft', String(state.aircraftCount), state.aircraftCount > 0 ? 'good' : 'warn', state.aircraftCount > 0 ? 'Visible in recent output window' : 'No recent aircraft solves visible'),
    railRow('Receivers', `${state.activeReceiverCount}/${state.receiverCount}`, state.activeReceiverCount > 0 ? (state.activeReceiverCount === state.receiverCount ? 'good' : 'warn') : 'risk', 'Active or online receiver count'),
    railRow('Store age', overviewAge(state.lastStoreAge), state.lastStoreAge !== null && state.lastStoreAge <= 20 ? 'good' : state.lastStoreAge !== null && state.lastStoreAge <= 90 ? 'warn' : 'risk', 'Latest stored solve'),
    railRow('Signal age', overviewAge(state.lastSignalAge), state.lastSignalAge !== null && state.lastSignalAge <= 15 ? 'good' : state.lastSignalAge !== null && state.lastSignalAge <= 60 ? 'warn' : 'risk', 'Latest runtime signal'),
  ].join('');

  const solverRows = [
    railRow('Avg quality', overviewPercent(state.avgQuality), state.avgQuality !== null && state.avgQuality >= 0.8 ? 'good' : state.avgQuality !== null && state.avgQuality >= 0.55 ? 'warn' : 'risk', 'Recent solve score'),
    railRow('Residual', state.avgResidual !== null ? `${state.avgResidual.toFixed(1)}m` : 'n/a', state.avgResidual !== null && state.avgResidual <= 100 ? 'good' : state.avgResidual !== null && state.avgResidual <= 300 ? 'warn' : 'risk', 'Solver fit error'),
    railRow('Uncertainty', state.avgUncertainty !== null ? `±${Math.round(state.avgUncertainty)}m` : 'n/a', state.avgUncertainty !== null && state.avgUncertainty <= 75 ? 'good' : state.avgUncertainty !== null && state.avgUncertainty <= 200 ? 'warn' : 'risk', 'Average estimated error'),
    railRow('Failed solves', state.failedSolves !== null ? String(state.failedSolves) : 'n/a', state.failedSolves === 0 ? 'good' : state.failedSolves !== null && state.failedSolves <= 5 ? 'warn' : 'risk', 'Recent readiness failures'),
  ].join('');

  const benchmarkTone = /publish|ready|verified|pass/i.test(String(state.benchmarkStatus))
    ? 'good'
    : /missing|pending|not/i.test(String(state.benchmarkStatus))
      ? 'warn'
      : 'risk';

  const evidenceRows = [
    `
      <div class="overview-evidence-row">
        <div>
          <strong>Registry</strong>
          <span>${overviewEscape(state.mode.registryConfigured ? 'Named participants are available from the current registry state.' : 'No receiver registry hash is visible in the current mode state.')}</span>
        </div>
        <span class="overview-inline-status tone-${overviewStatusTone(state.mode.registryConfigured ? 'good' : 'warn')}">${state.mode.registryConfigured ? 'Ready' : 'Missing'}</span>
      </div>
    `,
    `
      <div class="overview-evidence-row">
        <div>
          <strong>Output</strong>
          <span>${overviewEscape(evidenceMeaning(state))}</span>
        </div>
        <span class="overview-inline-status tone-${overviewStatusTone(state.mode.isLive && state.benchmarkableOutput ? 'good' : state.mode.isLive ? 'warn' : 'warn')}">${overviewEscape(state.mode.isLive ? 'Live' : state.mode.isDemo ? 'Replay' : state.mode.isSimulation ? 'Synthetic' : 'Not ready')}</span>
      </div>
    `,
    `
      <div class="overview-evidence-row">
        <div>
          <strong>Benchmark</strong>
          <span>${overviewEscape(state.benchmarkableOutput ? 'Readiness data currently allows benchmark-oriented interpretation.' : 'Readiness data does not yet confirm benchmarkable output.')}</span>
        </div>
        <span class="overview-inline-status tone-${overviewStatusTone(benchmarkTone)}">${overviewEscape(String(state.benchmarkStatus).replaceAll('_', ' '))}</span>
      </div>
    `,
  ].join('');

  target.innerHTML = `
    <section class="overview-rail-section">
      <div class="overview-rail-head">
        <div>
          <h2>Runtime</h2>
          <p>Can the control plane serve current MLAT output?</p>
        </div>
      </div>
      <div class="overview-ops-list">${runtimeRows}</div>
      ${railAction(runtimeAction(state))}
      ${railLinks([
        { href: '/app/pipeline.html', label: 'Pipeline' },
        { href: '/app/settings.html', label: 'Settings' },
      ])}
    </section>

    <section class="overview-rail-section">
      <div class="overview-rail-head">
        <div>
          <h2>Tracking</h2>
          <p>Are solves and receivers active enough to trust this surface?</p>
        </div>
      </div>
      <div class="overview-ops-list">${trackingRows}</div>
      ${railAction(trackingAction(state))}
      ${railLinks([
        { href: '/app/localization.html', label: 'Live map' },
        { href: '/app/receivers.html', label: 'Receivers' },
        { href: '/app/aircraft.html', label: 'Aircraft' },
      ])}
    </section>

    <section class="overview-rail-section">
      <div class="overview-rail-head">
        <div>
          <h2>Solver / readiness</h2>
          <p>How clean do recent solves look?</p>
        </div>
      </div>
      <div class="overview-ops-list">${solverRows}</div>
      ${railAction(solverAction(state))}
      ${railLinks([
        { href: '/app/analytics.html', label: 'Metrics' },
        { href: '/app/localization.html', label: 'Map detail' },
      ])}
    </section>

    <section class="overview-rail-section overview-rail-section-evidence">
      <div class="overview-rail-head">
        <div>
          <h2>Trust summary</h2>
          <p>Is the current output ready to defend as evidence-backed?</p>
        </div>
      </div>
      <div class="overview-evidence-list">${evidenceRows}</div>
      ${railAction(trustAction(state))}
      ${railLinks([
        { href: '/app/analytics.html', label: 'Evidence gates' },
        { href: '/app/settings.html', label: 'Mode setup' },
      ])}
    </section>
  `;
}

function renderDrilldowns() {
  const target = document.getElementById('overview-drilldowns');
  if (!target) return;
  target.innerHTML = `
    <a class="action-chip" href="/app/localization.html">Open live map</a>
    <a class="action-chip" href="/app/aircraft.html">Inspect aircraft</a>
    <a class="action-chip" href="/app/receivers.html">Inspect receivers</a>
    <a class="action-chip" href="/app/pipeline.html">Review pipeline</a>
    <a class="action-chip" href="/app/analytics.html">Check metrics</a>
    <a class="action-chip" href="/app/settings.html">Open settings</a>
  `;
}

function updateShellMetrics(state) {
  const metricTarget = document.getElementById('shell-freshness-pill');
  if (metricTarget && state.mode.isLive && state.benchmarkableOutput) {
    metricTarget.textContent = 'Live output benchmarkable';
  } else if (metricTarget && state.mode.isDemo) {
    metricTarget.textContent = 'Replay output visible';
  } else if (metricTarget && state.mode.isSimulation) {
    metricTarget.textContent = 'Synthetic output visible';
  } else if (metricTarget && state.lastSignalAge !== null) {
    metricTarget.textContent = `Last signal ${overviewAge(state.lastSignalAge)}`;
  }

  if (typeof window.setShellMetric === 'function') {
    window.setShellMetric('aircraft', String(state.aircraftCount), state.aircraftCount > 0 ? `${state.recentPositionCount} recent positions in readiness data` : 'No current aircraft solves');
    window.setShellMetric('receivers', String(state.activeReceiverCount), state.receiverCount > 0 ? `${state.activeReceiverCount}/${state.receiverCount} receivers active or online` : 'No receivers visible');
    window.setShellMetric('freshness', overviewAge(state.lastSignalAge), `${state.mode.sourceLabel}`);
    window.setShellMetric('status', state.operatorTone === 'good' ? 'LIVE' : state.operatorTone === 'warn' ? 'WATCH' : 'CHECK', state.operatorVerdict);
  }
}

window.pageHydrators.overview = async function ({ modeData, healthData, aircraftData, receiverData, fetchJson }) {
  const [readiness, benchmark, positionsData] = await Promise.all([
    fetchJson('/api/readiness').catch(() => null),
    fetchJson('/api/benchmark/latest').catch(() => null),
    fetchJson('/api/positions/recent?seconds=600&limit=500').catch(() => null),
  ]);

  const state = buildOverviewState({ modeData, healthData, aircraftData, receiverData, readiness, benchmark, positionsData });
  renderMetricCards(state);
  renderBriefing(state);
  renderRail(state);
  renderDrilldowns(state);
  updateShellMetrics(state);

  const mapTarget = document.getElementById('overview-map');
  if (!mapTarget) return;
  const existingState = window.__overviewMapState;
  if (!existingState) {
    window.__overviewMapState = buildOverviewMap(mapTarget, state);
  }
  if (window.__overviewMapState) {
    renderOverviewMap(window.__overviewMapState, state);
  }
};

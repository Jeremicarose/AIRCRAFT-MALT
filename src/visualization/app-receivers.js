function receiverText(value) {
  return window.shellEscape ? window.shellEscape(value) : String(value ?? '');
}

function receiverAgeLabel(timestamp) {
  return window.shellRelativeTime ? window.shellRelativeTime(timestamp) : 'n/a';
}

function receiverAgeSeconds(timestamp) {
  return window.shellAgeSeconds ? window.shellAgeSeconds(timestamp) : null;
}

function receiverBadge(label, tone) {
  return window.shellHealthBadge ? window.shellHealthBadge(label, tone) : `<span>${receiverText(label)}</span>`;
}

function receiverMiniBar(label, valueText, ratio, tone) {
  return window.shellMiniBar ? window.shellMiniBar(label, valueText, ratio, tone) : '';
}

function classifyReceiver(receiver) {
  const status = String(receiver?.status || '').toLowerCase();
  const ageSeconds = receiverAgeSeconds(receiver?.last_seen);
  if (status !== 'online' && status !== 'active') {
    return {
      label: 'Offline',
      tone: 'tone-risk',
      score: 20,
      reason: 'Runtime status is not reporting the receiver as online.',
    };
  }
  if (ageSeconds !== null && ageSeconds > 300) {
    return {
      label: 'Stale',
      tone: 'tone-warn',
      score: 48,
      reason: `The receiver last reported ${receiverAgeLabel(receiver.last_seen)}, so uptime is uncertain.`,
    };
  }
  if (ageSeconds !== null && ageSeconds > 90) {
    return {
      label: 'Aging',
      tone: 'tone-warn',
      score: 68,
      reason: `The receiver is online, but its freshest update is already ${receiverAgeLabel(receiver.last_seen)}.`,
    };
  }
  return {
    label: 'Healthy',
    tone: 'tone-good',
    score: 92,
    reason: 'The receiver is online and fresh enough to support current solves.',
  };
}

function capabilitySummary(receiver) {
  const caps = Array.isArray(receiver?.capabilities) ? receiver.capabilities : [];
  if (!caps.length) return 'No capabilities advertised';
  if (caps.length <= 2) return caps.join(' · ');
  return `${caps.slice(0, 2).join(' · ')} +${caps.length - 2}`;
}

function buildReceiverContribution(receiverId, aircraftRows) {
  const related = aircraftRows.filter((aircraft) => Array.isArray(aircraft?.correlation?.receiver_ids) && aircraft.correlation.receiver_ids.includes(receiverId));
  const latestRelated = related
    .slice()
    .sort((a, b) => Number(b.timestamp || 0) - Number(a.timestamp || 0));
  const contributionCount = latestRelated.length;
  const avgQuality = contributionCount
    ? latestRelated.reduce((sum, aircraft) => sum + (Number(aircraft?.quality?.score) || 0), 0) / contributionCount
    : null;
  const avgReceivers = contributionCount
    ? latestRelated.reduce((sum, aircraft) => sum + (Number(aircraft?.num_receivers) || 0), 0) / contributionCount
    : null;
  return {
    relatedAircraft: latestRelated,
    contributionCount,
    avgQuality,
    avgReceivers,
  };
}

function buildTrustSection(modeData) {
  const configured = Boolean(modeData?.receiver_registry_type_hash);
  return {
    label: configured ? 'Configured' : 'Unconfigured',
    tone: configured ? 'tone-good' : 'tone-warn',
    detail: configured
      ? `This runtime has a receiver registry type hash configured (${receiverText(`${modeData.receiver_registry_type_hash.slice(0, 18)}…`)}).`
      : 'This runtime does not expose a configured receiver registry type hash, so identity proof is currently local/runtime-scoped.',
  };
}

function buildFreshnessTimeline(ageSeconds, online) {
  const slots = [
    { label: '0–1m', pass: online && ageSeconds !== null && ageSeconds <= 60 },
    { label: '1–5m', pass: online && ageSeconds !== null && ageSeconds > 60 && ageSeconds <= 300 },
    { label: '5m+', pass: ageSeconds !== null && ageSeconds > 300 },
  ];
  return slots.map((slot, index) => `
    <div class="timeline-bucket ${slot.pass ? 'is-active' : ''}">
      <strong>${String(index + 1).padStart(2, '0')}</strong>
      <span>${receiverText(slot.label)}</span>
    </div>
  `).join('');
}

function buildRelatedAircraftLinks(relatedAircraft) {
  if (!relatedAircraft.length) return '<p class="panel-empty-note">No current aircraft reference this receiver in recent correlation data.</p>';
  return `
    <div class="entity-link-list">
      ${relatedAircraft.slice(0, 8).map((aircraft) => `
        <a class="entity-link-chip" href="/app/aircraft.html?aircraft=${encodeURIComponent(aircraft.aircraft_id)}">${receiverText(aircraft.aircraft_id)}<span>${Math.round(Number(aircraft?.quality?.score || 0) * 100)}% confidence</span></a>
      `).join('')}
    </div>
  `;
}

window.pageHydrators.receivers = async function ({ receiverData, modeData, aircraftData, fetchJson }) {
  const target = document.getElementById('receivers-list');
  const detailTarget = document.getElementById('receiver-detail-panel');
  if (!target || !detailTarget) return;
  const receivers = receiverData?.receivers || [];
  const aircraftRows = Array.isArray(aircraftData?.aircraft)
    ? aircraftData.aircraft
    : Array.isArray(aircraftData?.positions)
      ? aircraftData.positions
      : (await fetchJson('/api/positions/recent?seconds=300&limit=250').catch(() => null))?.positions || [];
  let filteredReceivers = receivers.slice();
  let selectedReceiverId = window.getSelectionParam ? window.getSelectionParam('receiver') : null;

  if (!receivers.length) {
    target.innerHTML = `
      <div class="list-shell">
        <div class="list-toolbar"><div class="list-toolbar-note">No registry nodes are currently visible.</div></div>
        <table class="app-table">
          <thead><tr><th>Receiver</th><th>Status</th><th>Capabilities</th><th>Last seen</th></tr></thead>
          <tbody><tr><td colspan="4">No registry nodes are currently visible.</td></tr></tbody>
        </table>
      </div>
    `;
    detailTarget.innerHTML = `
      <div class="panel-head"><div><h2>No receiver selected</h2><p>Registry discovery has no active records</p></div></div>
      <div class="detail-kv">
        <div class="detail-kv-row"><strong>Network</strong><span>${receiverText(modeData?.mode || 'unknown')}</span></div>
        <div class="detail-kv-row"><strong>Registry</strong><span>${modeData?.receiver_registry_type_hash ? 'configured' : 'unconfigured'}</span></div>
      </div>
    `;
    return;
  }

  function renderList() {
    target.innerHTML = `
      <div class="list-shell">
        <div class="list-toolbar">
          <div>
            <label class="control-label" for="receiver-search">Search receivers</label>
            <input id="receiver-search" class="control-input list-search-input" type="search" placeholder="Filter by receiver id" value="${receiverText(document.getElementById('receiver-search')?.value || '')}">
          </div>
          <div class="list-toolbar-note">${filteredReceivers.length} of ${receivers.length} receivers</div>
        </div>
        <table class="app-table receiver-profile-table">
          <thead><tr><th>Receiver</th><th>Health</th><th>Capabilities</th><th>Freshness</th></tr></thead>
          <tbody>
            ${filteredReceivers.map((receiver) => {
              const state = classifyReceiver(receiver);
              return `
                <tr>
                  <td><button class="data-list-button ${selectedReceiverId === receiver.receiver_id ? 'is-selected' : ''}" type="button" data-receiver-id="${receiverText(receiver.receiver_id)}">${receiverText(receiver.receiver_id)}</button></td>
                  <td>${receiverBadge(state.label, state.tone)}</td>
                  <td>${receiverText(capabilitySummary(receiver))}</td>
                  <td>${receiverText(receiverAgeLabel(receiver.last_seen))}</td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
    `;

    const searchInput = target.querySelector('#receiver-search');
    if (searchInput) {
      searchInput.addEventListener('input', () => {
        filteredReceivers = window.filterByQuery
          ? window.filterByQuery(receivers, searchInput.value, (item) => `${item.receiver_id} ${(item.capabilities || []).join(' ')}`)
          : receivers;
        renderList();
      });
    }

    target.querySelectorAll('[data-receiver-id]').forEach((button) => {
      button.addEventListener('click', () => renderDetail(button.dataset.receiverId));
    });
  }

  function renderDetail(receiverId) {
    const receiver = receivers.find((item) => item.receiver_id === receiverId);
    if (!receiver) return;
    selectedReceiverId = receiverId;
    if (window.setSelectionParam) window.setSelectionParam('receiver', receiverId);
    target.querySelectorAll('[data-receiver-id]').forEach((button) => {
      button.classList.toggle('is-selected', button.dataset.receiverId === receiverId);
    });

    const state = classifyReceiver(receiver);
    const contribution = buildReceiverContribution(receiver.receiver_id, aircraftRows);
    const trust = buildTrustSection(modeData);
    const online = ['online', 'active'].includes(String(receiver.status || '').toLowerCase());
    const freshnessTimeline = buildFreshnessTimeline(receiverAgeSeconds(receiver.last_seen), online);

    detailTarget.innerHTML = `
      <div class="panel-head inspector-head">
        <div>
          <h2>${receiverText(receiver.receiver_id)}</h2>
          <p>Receiver profile anchored in freshness, contribution, and configured trust context.</p>
        </div>
        ${receiverBadge(state.label, state.tone)}
      </div>
      <div class="inspector-scroll">
        <section class="inspector-section inspector-hero">
          <div class="summary-card-grid receiver-summary-grid">
            <article class="summary-card ${state.tone}">
              <span>Health score</span>
              <strong>${Math.round(state.score)}</strong>
              <small>${receiverText(state.reason)}</small>
            </article>
            <article class="summary-card ${Number.isFinite(contribution.avgQuality) ? (window.shellToneFromScore ? window.shellToneFromScore(contribution.avgQuality) : 'tone-neutral') : 'tone-neutral'}">
              <span>Visible aircraft</span>
              <strong>${contribution.relatedAircraft.length}</strong>
              <small>${Number.isFinite(contribution.avgQuality) ? `${Math.round(contribution.avgQuality * 100)}% avg confidence on related solves` : 'No related aircraft in the current snapshot'}</small>
            </article>
            <article class="summary-card ${trust.tone}">
              <span>Trust state</span>
              <strong>${receiverText(trust.label)}</strong>
              <small>${receiverText(modeData?.benchmarkable_output ? 'Benchmarkable runtime context available' : 'Operational-only runtime context')}</small>
            </article>
          </div>
        </section>

        <section class="inspector-section">
          <div class="section-title-row"><h3>Contribution summary</h3><p>Inferred from the shell aircraft snapshot and recent correlation data.</p></div>
          <div class="split-mini-grid">
            <article class="mini-evidence-card">
              <div class="mini-chart-head"><strong>Current contribution</strong><span>${contribution.contributionCount} related aircraft</span></div>
              <div class="contribution-stack">
                ${receiverMiniBar('Aircraft visibility', `${contribution.relatedAircraft.length} aircraft`, Math.min(1, contribution.relatedAircraft.length / Math.max(1, aircraftRows.length || 1)), contribution.relatedAircraft.length ? 'tone-good' : 'tone-warn')}
                ${receiverMiniBar('Average solve quality', Number.isFinite(contribution.avgQuality) ? `${Math.round(contribution.avgQuality * 100)}%` : 'n/a', Number.isFinite(contribution.avgQuality) ? contribution.avgQuality : 0, Number.isFinite(contribution.avgQuality) ? (window.shellToneFromScore ? window.shellToneFromScore(contribution.avgQuality) : 'tone-neutral') : 'tone-neutral')}
                ${receiverMiniBar('Solve geometry', Number.isFinite(contribution.avgReceivers) ? `${contribution.avgReceivers.toFixed(1)} avg receivers` : 'n/a', Number.isFinite(contribution.avgReceivers) ? Math.min(1, contribution.avgReceivers / 6) : 0, Number.isFinite(contribution.avgReceivers) && contribution.avgReceivers >= 4 ? 'tone-good' : 'tone-warn')}
              </div>
            </article>
            <article class="mini-evidence-card">
              <div class="mini-chart-head"><strong>Location</strong><span>Map-linked placement</span></div>
              <div class="explanation-stack">
                <div class="explanation-row">
                  <strong>Coordinates</strong>
                  <span>${receiver.latitude.toFixed(5)}, ${receiver.longitude.toFixed(5)} · ${Math.round(receiver.altitude).toLocaleString()}m altitude</span>
                </div>
                <div class="explanation-row">
                  <strong>Capabilities</strong>
                  <span>${receiverText((receiver.capabilities || []).join(', ') || 'No capabilities advertised')}</span>
                </div>
              </div>
            </article>
          </div>
        </section>

        <section class="inspector-section">
          <div class="section-title-row"><h3>Trust and uptime</h3><p>Honest first-pass identity and freshness framing without synthetic history.</p></div>
          <div class="split-mini-grid">
            <article class="mini-evidence-card">
              <div class="mini-chart-head"><strong>CKB trust / identity</strong><span>${receiverText(trust.label)}</span></div>
              <div class="explanation-stack">
                <div class="explanation-row">
                  <strong>Registry state</strong>
                  <span>${receiverText(trust.detail)}</span>
                </div>
                <div class="explanation-row">
                  <strong>Scope</strong>
                  <span>${modeData?.receiver_registry_type_hash ? 'This page shows configured registry state only. Owner, tx hash, and historical identity metadata are not currently exposed by the receiver API.' : 'The runtime does not currently expose registry-backed identity metadata for this receiver.'}</span>
                </div>
              </div>
            </article>
            <article class="mini-evidence-card">
              <div class="mini-chart-head"><strong>Freshness timeline</strong><span>${receiverText(receiverAgeLabel(receiver.last_seen))}</span></div>
              <div class="timeline-buckets">${freshnessTimeline}</div>
            </article>
          </div>
        </section>

        <section class="inspector-section">
          <div class="section-title-row"><h3>Cross-links</h3><p>Move between the live map and aircraft supported by this receiver.</p></div>
          <div class="action-row profile-action-row">
            <a class="action-chip" href="/app/localization.html?receiver=${encodeURIComponent(receiver.receiver_id)}">Open on live map</a>
            <a class="action-chip" href="/app/aircraft.html">Inspect aircraft list</a>
          </div>
          ${buildRelatedAircraftLinks(contribution.relatedAircraft)}
        </section>
      </div>
    `;
  }

  renderList();
  const initialReceiverId = selectedReceiverId && receivers.some((receiver) => receiver.receiver_id === selectedReceiverId)
    ? selectedReceiverId
    : receivers[0].receiver_id;
  renderDetail(initialReceiverId);
};
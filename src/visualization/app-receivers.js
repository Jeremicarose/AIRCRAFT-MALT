function receiverText(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

window.pageHydrators.receivers = async function ({ receiverData, modeData }) {
  const target = document.getElementById('receivers-list');
  const detailTarget = document.getElementById('receiver-detail-panel');
  if (!target || !detailTarget) return;
  const receivers = receiverData?.receivers || [];

  if (!receivers.length) {
    target.innerHTML = `
      <table class="app-table">
        <thead><tr><th>Receiver</th><th>Status</th><th>Capabilities</th><th>Last seen</th></tr></thead>
        <tbody><tr><td colspan="4">No registry nodes are currently visible.</td></tr></tbody>
      </table>
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

  target.innerHTML = `
    <table class="app-table">
      <thead><tr><th>Receiver</th><th>Status</th><th>Capabilities</th><th>Last seen</th></tr></thead>
      <tbody>
        ${receivers.map((receiver) => `
          <tr>
            <td><button class="data-list-button" type="button" data-receiver-id="${receiverText(receiver.receiver_id)}">${receiverText(receiver.receiver_id)}</button></td>
            <td>${receiverText(receiver.status)}</td>
            <td>${receiverText(receiver.capabilities.join(', '))}</td>
            <td>${new Date(receiver.last_seen * 1000).toLocaleString()}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;

  function renderDetail(receiver) {
    detailTarget.innerHTML = `
      <div class="panel-head"><div><h2>${receiverText(receiver.receiver_id)}</h2><p>Registry-backed receiver</p></div><span class="status-pill ${String(receiver.status).toLowerCase() === 'online' ? 'mode-live' : 'mode-sim'}">${receiverText(receiver.status)}</span></div>
      <div class="detail-kv">
        <div class="detail-kv-row"><strong>Latitude</strong><span>${receiver.latitude.toFixed(5)}</span></div>
        <div class="detail-kv-row"><strong>Longitude</strong><span>${receiver.longitude.toFixed(5)}</span></div>
        <div class="detail-kv-row"><strong>Altitude</strong><span>${Math.round(receiver.altitude)}m</span></div>
        <div class="detail-kv-row"><strong>Capabilities</strong><span>${receiverText(receiver.capabilities.join(', '))}</span></div>
        <div class="detail-kv-row"><strong>Last seen</strong><span>${new Date(receiver.last_seen * 1000).toLocaleString()}</span></div>
        <div class="detail-kv-row"><strong>CKB registry</strong><span>${modeData?.receiver_registry_type_hash ? 'testnet / typed cell' : 'unconfigured'}</span></div>
      </div>
      <div class="ops-rail-actions"><a class="action-chip" href="/app/localization.html">Locate on map</a></div>
    `;
  }

  target.querySelectorAll('[data-receiver-id]').forEach((button) => {
    button.addEventListener('click', () => {
      const receiver = receivers.find((item) => item.receiver_id === button.dataset.receiverId);
      if (receiver) renderDetail(receiver);
    });
  });
  renderDetail(receivers[0]);
};

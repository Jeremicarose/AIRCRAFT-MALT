window.pageHydrators.receivers = async function ({ receiverData }) {
  const target = document.getElementById('receivers-list');
  const detailTarget = document.getElementById('receiver-detail-panel');
  if (!target) return;

  if (!receiverData || !receiverData.receivers.length) {
    target.innerHTML = '<div class="empty-state">No receivers visible.</div>';
    if (detailTarget) {
      detailTarget.innerHTML = '<div class="empty-state">Receiver detail will appear here when nodes are available.</div>';
    }
    return;
  }

  renderSimpleList(target, receiverData.receivers, (receiver) => `
    <article class="list-row" data-receiver-card="${receiver.receiver_id}">
      <strong>${receiver.receiver_id}</strong>
      <span>${receiver.status} · ${receiver.capabilities.join(' · ')}</span>
      <span>${receiver.latitude.toFixed(3)}°, ${receiver.longitude.toFixed(3)}° · alt ${Math.round(receiver.altitude)}m</span>
    </article>
  `);

  function renderReceiverDetail(receiver) {
    if (!detailTarget) return;
    detailTarget.innerHTML = `
      <div class="split-summary">
        <article class="app-panel">
          <span class="kicker">Receiver detail</span>
          <h2>${receiver.receiver_id}</h2>
          <p>Receiver status, capabilities, and placement without the aircraft and localization surfaces competing for the same space.</p>
          <div class="detail-kv">
            <div class="detail-kv-row"><strong>Status</strong><span>${receiver.status}</span></div>
            <div class="detail-kv-row"><strong>Capabilities</strong><span>${receiver.capabilities.join(' · ')}</span></div>
            <div class="detail-kv-row"><strong>Latitude</strong><span>${receiver.latitude.toFixed(4)}</span></div>
            <div class="detail-kv-row"><strong>Longitude</strong><span>${receiver.longitude.toFixed(4)}</span></div>
            <div class="detail-kv-row"><strong>Altitude</strong><span>${Math.round(receiver.altitude)}m</span></div>
            <div class="detail-kv-row"><strong>Last seen</strong><span>${new Date(receiver.last_seen * 1000).toLocaleString()}</span></div>
          </div>
        </article>
        <article class="app-panel">
          <span class="kicker">Role in system</span>
          <h2>Registry-backed node</h2>
          <p>This surface is where future operator actions such as status review, contribution scoring, maintenance, and registry editing should live.</p>
        </article>
      </div>
    `;
  }

  target.querySelectorAll('[data-receiver-card]').forEach((card) => {
    card.addEventListener('click', () => {
      const receiver = receiverData.receivers.find((item) => item.receiver_id === card.dataset.receiverCard);
      if (receiver) {
        renderReceiverDetail(receiver);
      }
    });
  });

  renderReceiverDetail(receiverData.receivers[0]);
};

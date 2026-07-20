window.pageHydrators.settings = async function ({ modeData, fetchJson }) {
  const target = document.getElementById('settings-panel');
  if (!target) return;

  const [health, readiness] = await Promise.all([
    fetchJson('/api/health').catch(() => null),
    fetchJson('/api/readiness').catch(() => null),
  ]);
  target.innerHTML = `
    <div class="app-grid two-col">
      <article class="app-panel">
        <div class="panel-head"><div><h2>Runtime</h2><p>Current execution posture</p></div></div>
        <table class="app-table">
          <tbody>
            <tr><th>Mode</th><td>${modeData ? modeData.mode : 'unknown'}</td></tr>
            <tr><th>Processor</th><td>${modeData ? modeData.runtime_status : 'unknown'}</td></tr>
            <tr><th>Simulation mode</th><td>${modeData ? modeData.simulation_mode : 'unknown'}</td></tr>
            <tr><th>Strict production</th><td>${modeData ? modeData.strict_production_mode : 'unknown'}</td></tr>
            <tr><th>Configured transport</th><td>${modeData ? modeData.configured_transport : 'unknown'}</td></tr>
            <tr><th>Fallback allowed</th><td>${modeData ? modeData.simulate_if_unavailable : 'unknown'}</td></tr>
            <tr><th>Demo mode</th><td>${modeData ? modeData.demo_mode : 'unknown'}</td></tr>
            <tr><th>WebSocket available</th><td>${modeData ? modeData.websocket_available : 'unknown'}</td></tr>
            <tr><th>Synthetic feed mode</th><td>${modeData ? modeData.synthetic_feed_mode : 'unknown'}</td></tr>
            <tr><th>Registry type hash</th><td class="evidence-hash">${modeData?.receiver_registry_type_hash ? `${modeData.receiver_registry_type_hash.slice(0, 18)}…` : 'unconfigured'}</td></tr>
          </tbody>
        </table>
      </article>
      <article class="app-panel">
        <div class="panel-head"><div><h2>Evidence</h2><p>Storage and benchmark gates</p></div></div>
        <table class="app-table">
          <tbody>
            <tr><th>Database size</th><td>${health && health.database ? health.database.size_mb : 'n/a'} MB</td></tr>
            <tr><th>Benchmarkable output</th><td>${readiness ? readiness.dimensions.quality.benchmarkable_output : 'unknown'}</td></tr>
            <tr><th>Simulated positions</th><td>${readiness ? readiness.dimensions.quality.simulated_positions : 'unknown'}</td></tr>
            <tr><th>Health status</th><td>${health ? health.status : 'unknown'}</td></tr>
          </tbody>
        </table>
      </article>
    </div>
  `;
};

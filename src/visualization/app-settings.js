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
        <span class="kicker">Runtime posture</span>
        <h2>Current mode visibility</h2>
        <table class="app-table">
          <tbody>
            <tr><th>Mode</th><td>${modeData ? modeData.mode : 'unknown'}</td></tr>
            <tr><th>Simulation mode</th><td>${modeData ? modeData.simulation_mode : 'unknown'}</td></tr>
            <tr><th>Demo mode</th><td>${modeData ? modeData.demo_mode : 'unknown'}</td></tr>
            <tr><th>WebSocket available</th><td>${modeData ? modeData.websocket_available : 'unknown'}</td></tr>
            <tr><th>Synthetic feed mode</th><td>${modeData ? modeData.synthetic_feed_mode : 'unknown'}</td></tr>
          </tbody>
        </table>
      </article>
      <article class="app-panel">
        <span class="kicker">Storage / benchmarkability</span>
        <h2>Current environment constraints</h2>
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

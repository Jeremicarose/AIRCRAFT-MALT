const map = L.map('map', { zoomControl: false }).setView([40.7128, -74.006], 7);
L.control.zoom({ position: 'topleft' }).addTo(map);
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '© OpenStreetMap © CARTO',
    subdomains: 'abcd',
    maxZoom: 20,
}).addTo(map);

const aircraft = {};
const receivers = {};
const receiverMarkers = {};
const aircraftMarkers = {};
const aircraftPaths = {};
const aircraftGlowPaths = {};
let socket = null;
let refreshTimer = null;
let websocketAvailable = false;
let lastSnapshotPositionCount = 0;
let lastBoundsFitAt = 0;
let selectedAircraftId = null;
let systemMode = null;

const aircraftIcon = L.divIcon({
    className: 'custom-aircraft-icon',
    html: '<div class="map-aircraft-marker"></div>',
    iconSize: [18, 18],
});

const receiverIcon = L.divIcon({
    className: 'custom-receiver-icon',
    html: '<div class="map-receiver-marker"></div>',
    iconSize: [18, 18],
});

function defaultApiUrl() {
    if (window.location.protocol === 'http:' || window.location.protocol === 'https:') {
        return window.location.origin;
    }
    return 'http://localhost:5051';
}

function getApiBase() {
    return document.getElementById('api-url').value.trim().replace(/\/$/, '');
}

function setDockStatus(message, tone = 'neutral') {
    const dockStatus = document.getElementById('map-dock-status');
    if (!dockStatus) {
        return;
    }
    dockStatus.textContent = message;
    dockStatus.className = `map-dock-status tone-${tone}`;
}

function setStatus(message, tone = 'neutral') {
    document.getElementById('connection-status').textContent = message;
    setDockStatus(
        tone === 'live' ? 'Connected' : tone === 'pending' ? 'Loading' : tone === 'error' ? 'Issue' : 'Offline',
        tone,
    );
}

function setFeedPill(message) {
    document.getElementById('feed-pill').textContent = message;
}

function formatRelativeTime(epochSeconds) {
    if (!epochSeconds) {
        return 'recently';
    }
    const delta = Math.max(0, Math.round((Date.now() / 1000) - epochSeconds));
    if (delta < 60) {
        return `${delta}s ago`;
    }
    if (delta < 3600) {
        return `${Math.round(delta / 60)}m ago`;
    }
    return `${Math.round(delta / 3600)}h ago`;
}

function formatClock(epochSeconds) {
    if (!epochSeconds) {
        return 'Awaiting timestamp';
    }
    return new Date(epochSeconds * 1000).toLocaleTimeString();
}

function formatCoordinate(lat, lon) {
    if (typeof lat !== 'number' || typeof lon !== 'number') {
        return 'No coordinates';
    }
    return `${lat.toFixed(3)}°, ${lon.toFixed(3)}°`;
}

function parseCapabilities(raw) {
    if (Array.isArray(raw)) {
        return raw;
    }
    if (typeof raw === 'string') {
        try {
            const parsed = JSON.parse(raw);
            return Array.isArray(parsed) ? parsed : [raw];
        } catch (_error) {
            return [raw];
        }
    }
    return [];
}

function getAircraftPopup(ac) {
    return `
        <b>Aircraft ${ac.id}</b><br>
        Position: ${ac.lat.toFixed(4)}°, ${ac.lon.toFixed(4)}°<br>
        Altitude: ${Math.round(ac.alt)}m (${Math.round(ac.alt * 3.28084)}ft)<br>
        Receivers: ${ac.numReceivers || 0}<br>
        Uncertainty: ±${Math.round(ac.uncertainty || 0)}m<br>
        Last update: ${formatClock(ac.timestamp)}
    `;
}

function getExperienceCopy(modeData) {
    if (!modeData) {
        return {
            pill: 'Mode unavailable',
            heroMode: 'Unknown source',
            heroFeed: websocketAvailable ? 'Streaming' : 'Refresh based',
            description: 'MLAT on this map means each position estimate is derived from multiple receivers. The mode service is unavailable, so treat this as a general walkthrough: start with an aircraft first, then use receivers to understand the support behind that estimate.',
            bannerTitle: '',
            bannerCopy: '',
            bannerBadge: '',
            aircraftRailCopy: 'Choose an aircraft first to inspect its path, uncertainty, and receiver support from the current map view.',
            feedLabel: websocketAvailable ? 'Streaming updates' : 'Manual refresh',
        };
    }

    const isDemo = Boolean(modeData.demo_mode);
    const isSimulation = Boolean(modeData.simulation_mode);
    const scenario = modeData.scenario || {};
    const scenarioLabel = modeData.demo_label || scenario.label || 'Hosted walkthrough';
    const scenarioSummary = scenario.summary || 'A stable replay is active for public exploration.';

    if (isDemo) {
        return {
            pill: scenarioLabel,
            heroMode: 'Hosted replay',
            heroFeed: websocketAvailable ? 'Streaming replay' : 'Replay refresh',
            description: `${scenarioSummary} MLAT here means the aircraft marker is an estimate supported by multiple receivers. This walkthrough is read-only and usually replay based, so the clearest first action is to click an aircraft, then use receivers afterward to understand coverage and support.`,
            bannerTitle: scenarioLabel,
            bannerCopy: `${scenarioSummary} Expect a hosted replay unless the product explicitly says live. Start with one aircraft, then move to receivers for context.`,
            bannerBadge: modeData.demo_read_only ? 'Read only' : 'Hosted replay',
            aircraftRailCopy: 'Replay aircraft ordered by latest update. Click one first to inspect path, uncertainty, and receiver support before moving into receiver context.',
            feedLabel: websocketAvailable ? 'Replay stream' : 'Replay refresh',
        };
    }

    if (isSimulation) {
        return {
            pill: 'Sample traffic',
            heroMode: 'Staged sample',
            heroFeed: websocketAvailable ? 'Streaming sample' : 'Sample refresh',
            description: 'This deployment is using staged traffic to explain the product flow. MLAT on this map still means each position is supported by multiple receivers. Start with an aircraft to inspect the estimate, then click a receiver to understand the supporting network around it.',
            bannerTitle: '',
            bannerCopy: '',
            bannerBadge: '',
            aircraftRailCopy: 'Sample aircraft ordered by latest update. Start with one aircraft, then use receivers to understand the network behind it.',
            feedLabel: websocketAvailable ? 'Sample stream' : 'Sample refresh',
        };
    }

    return {
        pill: 'Live traffic',
        heroMode: 'Live traffic',
        heroFeed: websocketAvailable ? 'Streaming live' : 'Live refresh',
        description: 'This deployment is showing live traffic. MLAT on this map means each aircraft position is estimated from multiple receivers. Start by clicking an aircraft to inspect path, uncertainty, and receiver count, then compare that estimate with nearby receivers.',
        bannerTitle: '',
        bannerCopy: '',
        bannerBadge: '',
        aircraftRailCopy: 'Live aircraft ordered by latest update. Start with one aircraft to inspect movement, uncertainty, and receiver support.',
        feedLabel: websocketAvailable ? 'Live stream' : 'Live refresh',
    };
}

function updateModeBanner(modeData) {
    const pill = document.getElementById('mode-pill');
    const description = document.getElementById('mode-description');
    const heroMode = document.getElementById('hero-mode');
    const heroFeed = document.getElementById('hero-feed');
    const demoChip = document.getElementById('demo-chip');
    const demoBanner = document.getElementById('demo-banner');
    const demoBannerTitle = document.getElementById('demo-banner-title');
    const demoBannerCopy = document.getElementById('demo-banner-copy');
    const demoBannerBadge = document.getElementById('demo-banner-badge');
    const aircraftRailCopy = document.getElementById('aircraft-rail-copy');

    const copy = getExperienceCopy(modeData);
    const isDemo = Boolean(modeData && modeData.demo_mode);
    const isLive = Boolean(modeData && !modeData.demo_mode && !modeData.simulation_mode);

    pill.textContent = copy.pill;
    pill.className = `status-pill ${isLive ? 'mode-live' : 'mode-sim'}`;
    heroMode.textContent = copy.heroMode;
    heroFeed.textContent = copy.heroFeed;
    description.textContent = copy.description;
    aircraftRailCopy.textContent = copy.aircraftRailCopy;

    demoChip.hidden = !isDemo;
    demoBanner.hidden = !isDemo;

    if (isDemo) {
        demoChip.textContent = 'Hosted walkthrough';
        demoBannerTitle.textContent = copy.bannerTitle;
        demoBannerCopy.textContent = copy.bannerCopy;
        demoBannerBadge.textContent = copy.bannerBadge;
    }
}

async function fetchJson(path) {
    const response = await fetch(`${getApiBase()}${path}`);
    if (!response.ok) {
        throw new Error(`HTTP ${response.status} for ${path}`);
    }
    return response.json();
}

function clearAircraftState() {
    Object.values(aircraftMarkers).forEach((marker) => map.removeLayer(marker));
    Object.values(aircraftPaths).forEach((path) => map.removeLayer(path));
    Object.values(aircraftGlowPaths).forEach((path) => map.removeLayer(path));
    Object.keys(aircraft).forEach((key) => delete aircraft[key]);
    Object.keys(aircraftMarkers).forEach((key) => delete aircraftMarkers[key]);
    Object.keys(aircraftPaths).forEach((key) => delete aircraftPaths[key]);
    Object.keys(aircraftGlowPaths).forEach((key) => delete aircraftGlowPaths[key]);
}

function upsertReceiver(receiver) {
    receivers[receiver.receiver_id] = {
        id: receiver.receiver_id,
        name: receiver.receiver_id,
        lat: receiver.latitude,
        lon: receiver.longitude,
        alt: receiver.altitude,
        status: receiver.status,
        capabilities: parseCapabilities(receiver.capabilities),
        lastSeen: receiver.last_seen,
    };

    const popup = `
        <b>${receiver.receiver_id}</b><br>
        Position: ${receiver.latitude.toFixed(4)}°, ${receiver.longitude.toFixed(4)}°<br>
        Altitude: ${Math.round(receiver.altitude)}m<br>
        Status: ${receiver.status}<br>
        Capabilities: ${parseCapabilities(receiver.capabilities).join(', ') || 'n/a'}
    `;

    if (receiverMarkers[receiver.receiver_id]) {
        receiverMarkers[receiver.receiver_id].setLatLng([receiver.latitude, receiver.longitude]);
        receiverMarkers[receiver.receiver_id].setPopupContent(popup);
    } else {
        receiverMarkers[receiver.receiver_id] = L.marker([receiver.latitude, receiver.longitude], { icon: receiverIcon })
            .addTo(map)
            .bindPopup(popup)
            .on('click', () => focusReceiver(receiver.receiver_id));
    }
}

function upsertAircraftFromApi(record, countForRate = true) {
    const aircraftId = record.aircraft_id;
    const lat = record.position ? record.position.latitude : record.latitude;
    const lon = record.position ? record.position.longitude : record.longitude;
    const alt = record.position ? record.position.altitude : record.altitude;

    if (typeof lat !== 'number' || typeof lon !== 'number') {
        return;
    }

    if (!aircraft[aircraftId]) {
        aircraft[aircraftId] = {
            id: aircraftId,
            lat,
            lon,
            alt: alt || 0,
            uncertainty: record.uncertainty || 0,
            numReceivers: record.num_receivers || 0,
            timestamp: record.timestamp || Date.now() / 1000,
            positions: [],
        };
    }

    const ac = aircraft[aircraftId];
    ac.lat = lat;
    ac.lon = lon;
    ac.alt = alt || 0;
    ac.uncertainty = record.uncertainty || 0;
    ac.numReceivers = record.num_receivers || 0;
    ac.timestamp = record.timestamp || Date.now() / 1000;
    ac.positions.push({ lat, lon, time: ac.timestamp });

    if (ac.positions.length > 80) {
        ac.positions = ac.positions.slice(-80);
    }

    if (!aircraftMarkers[aircraftId]) {
        aircraftMarkers[aircraftId] = L.marker([lat, lon], { icon: aircraftIcon })
            .addTo(map)
            .bindPopup(getAircraftPopup(ac))
            .on('click', () => focusAircraft(aircraftId));
    } else {
        aircraftMarkers[aircraftId].setLatLng([lat, lon]);
        aircraftMarkers[aircraftId].setPopupContent(getAircraftPopup(ac));
    }

    if (!aircraftGlowPaths[aircraftId]) {
        aircraftGlowPaths[aircraftId] = L.polyline([], {
            color: 'rgba(255, 210, 120, 0.12)',
            weight: 10,
            opacity: 1,
        }).addTo(map);
        aircraftPaths[aircraftId] = L.polyline([], {
            color: '#ffd278',
            weight: 2.4,
            opacity: 0.9,
        }).addTo(map);
    }

    const track = ac.positions.map((point) => [point.lat, point.lon]);
    aircraftGlowPaths[aircraftId].setLatLngs(track);
    aircraftPaths[aircraftId].setLatLngs(track);

    if (countForRate) {
        lastSnapshotPositionCount += 1;
    }
}

function maybeFitMap() {
    const now = Date.now();
    if (now - lastBoundsFitAt < 10000) {
        return;
    }
    const points = [
        ...Object.values(aircraft).map((ac) => [ac.lat, ac.lon]),
        ...Object.values(receivers).map((recv) => [recv.lat, recv.lon]),
    ];
    if (points.length === 0) {
        return;
    }
    lastBoundsFitAt = now;
    map.fitBounds(points, { padding: [56, 56], maxZoom: 9 });
}

async function fitBoundsFromApi() {
    try {
        const data = await fetchJson('/api/map/bounds');
        const bounds = data.bounds;
        if (!bounds) {
            maybeFitMap();
            return;
        }
        lastBoundsFitAt = Date.now();
        map.fitBounds([
            [bounds.south, bounds.west],
            [bounds.north, bounds.east],
        ], { padding: [56, 56], maxZoom: 9 });
    } catch (_error) {
        maybeFitMap();
    }
}

function updateReceiverList() {
    const receiverList = Object.values(receivers);
    const list = document.getElementById('receiver-list');

    if (receiverList.length === 0) {
        list.innerHTML = '<div class="empty-state">No receivers are visible yet. Refresh the walkthrough to load the latest network snapshot.</div>';
        document.getElementById('receiver-count').textContent = '0';
        return;
    }

    list.innerHTML = receiverList.map((recv) => {
        const capabilityText = recv.capabilities.length ? recv.capabilities.join(' · ') : 'Receiver details unavailable';
        const statusClass = String(recv.status || '').toLowerCase() === 'active' ? 'receiver-status live' : 'receiver-status';
        return `
            <button class="receiver-item" type="button" data-receiver-id="${recv.id}">
                <div>
                    <strong>${recv.name}</strong>
                    <span>${capabilityText}</span>
                    <span>Use after aircraft selection · last seen ${formatRelativeTime(recv.lastSeen)}</span>
                </div>
                <div class="${statusClass}">${recv.status}</div>
            </button>
        `;
    }).join('');

    list.querySelectorAll('[data-receiver-id]').forEach((button) => {
        button.addEventListener('click', () => focusReceiver(button.dataset.receiverId));
    });

    document.getElementById('receiver-count').textContent = String(receiverList.length);
    document.getElementById('receiver-detail').textContent = `${receiverList.filter((recv) => String(recv.status).toLowerCase() === 'active').length} currently reporting`;
}

function renderSelectedAircraft(ac, mode = 'snapshot') {
    if (!ac) {
        document.getElementById('selected-aircraft-title').textContent = 'No aircraft selected';
        document.getElementById('selected-aircraft-copy').textContent = 'Choose a target from the aircraft list or click a map marker to bring its latest state into focus.';
        document.getElementById('selected-altitude').textContent = '—';
        document.getElementById('selected-receivers').textContent = '—';
        document.getElementById('selected-uncertainty').textContent = '—';
        document.getElementById('selected-track-count').textContent = '—';
        document.getElementById('selected-timestamp').textContent = 'Awaiting target';
        document.getElementById('selected-position').textContent = 'No coordinates';
        return;
    }

    document.getElementById('selected-aircraft-title').textContent = `Aircraft ${ac.id}`;
    document.getElementById('selected-aircraft-copy').textContent = mode === 'focus'
        ? 'This focused aircraft view is the main explanation surface: compare the current estimate, recent path, uncertainty, and receiver support before moving on to receiver context.'
        : 'This is the latest state from the current map snapshot. Select it again to refresh the detailed path and bring that estimate back into focus.';
    document.getElementById('selected-altitude').textContent = `${Math.round(ac.alt)}m`;
    document.getElementById('selected-receivers').textContent = String(ac.numReceivers || 0);
    document.getElementById('selected-uncertainty').textContent = `±${Math.round(ac.uncertainty || 0)}m`;
    document.getElementById('selected-track-count').textContent = String(ac.positions.length || 0);
    document.getElementById('selected-timestamp').textContent = formatClock(ac.timestamp);
    document.getElementById('selected-position').textContent = formatCoordinate(ac.lat, ac.lon);
}

function updateUI() {
    const aircraftList = Object.values(aircraft).sort((a, b) => b.timestamp - a.timestamp);
    const isDemo = Boolean(systemMode && systemMode.demo_mode);
    const isSimulation = Boolean(systemMode && systemMode.simulation_mode);
    document.getElementById('aircraft-count').textContent = String(aircraftList.length);
    document.getElementById('hero-status').textContent = aircraftList.length > 0 ? 'Ready' : 'Standby';
    document.getElementById('aircraft-detail').textContent = aircraftList.length > 0
        ? `${formatRelativeTime(aircraftList[0].timestamp)} latest map update`
        : isDemo ? 'Replay loading' : 'Awaiting traffic';

    const perMinute = Math.round(lastSnapshotPositionCount / 10);
    document.getElementById('rate').textContent = String(perMinute);
    document.getElementById('rate-detail').textContent = isDemo
        ? 'Replay update pace in this hosted walkthrough'
        : websocketAvailable ? 'Update pace from the current stream' : 'Update pace from manual refreshes';

    const avgUncertainty = aircraftList.length > 0
        ? Math.round(aircraftList.reduce((sum, ac) => sum + (ac.uncertainty || 0), 0) / aircraftList.length)
        : 0;
    document.getElementById('avg-uncertainty').textContent = `${avgUncertainty}m`;
    document.getElementById('uncertainty-detail').textContent = aircraftList.length > 0
        ? (isDemo || isSimulation ? 'Across the aircraft shown in this walkthrough' : 'Across the aircraft shown right now')
        : 'No aircraft in the current view';

    const list = document.getElementById('aircraft-list');
    if (aircraftList.length === 0) {
        list.innerHTML = `<div class="empty-state">${isDemo
            ? 'Replay traffic is still loading. Refresh the walkthrough and the hosted sample feed will populate the map again.'
            : isSimulation
                ? 'Sample traffic is not visible yet. Refresh the map to load the latest staged positions.'
                : 'No aircraft are visible yet. Refresh the map to load the latest live positions.'}</div>`;
        renderSelectedAircraft(null);
        return;
    }

    list.innerHTML = aircraftList.map((ac, index) => `
        <button class="aircraft-item" type="button" data-aircraft-id="${ac.id}">
            <strong>${index === 0 ? `${ac.id} · start here` : ac.id}</strong>
            <span>${formatClock(ac.timestamp)} · ${Math.round(ac.alt)}m · ${ac.numReceivers} receivers</span>
            <span>Uncertainty ±${Math.round(ac.uncertainty || 0)}m · ${formatCoordinate(ac.lat, ac.lon)}</span>
        </button>
    `).join('');

    list.querySelectorAll('[data-aircraft-id]').forEach((button) => {
        button.addEventListener('click', () => focusAircraft(button.dataset.aircraftId));
    });

    if (!selectedAircraftId || !aircraft[selectedAircraftId]) {
        selectedAircraftId = aircraftList[0].id;
    }
    renderSelectedAircraft(aircraft[selectedAircraftId], 'snapshot');
}

async function loadReceivers() {
    const data = await fetchJson('/api/receivers');
    Object.values(receiverMarkers).forEach((marker) => map.removeLayer(marker));
    Object.keys(receiverMarkers).forEach((key) => delete receiverMarkers[key]);
    Object.keys(receivers).forEach((key) => delete receivers[key]);
    data.receivers.forEach(upsertReceiver);
    updateReceiverList();
}

async function loadPositions() {
    clearAircraftState();
    const data = await fetchJson('/api/positions/recent?seconds=600&limit=500');
    const orderedPositions = [...data.positions].sort((a, b) => a.timestamp - b.timestamp);
    lastSnapshotPositionCount = data.count || orderedPositions.length;
    orderedPositions.forEach((record) => upsertAircraftFromApi(record, false));
    updateUI();
}

async function loadStatistics() {
    try {
        const data = await fetchJson('/api/statistics?hours=1');
        const current = data.current || {};
        if (typeof current.active_aircraft === 'number') {
            document.getElementById('aircraft-count').textContent = String(current.active_aircraft);
        }
    } catch (_error) {
        return;
    }
}

async function loadSystemMode() {
    try {
        const data = await fetchJson('/api/system/mode');
        systemMode = data;
        websocketAvailable = Boolean(data.websocket_available);
        updateModeBanner(data);
        return data;
    } catch (_error) {
        websocketAvailable = false;
        updateModeBanner(null);
        return null;
    }
}

async function refreshSnapshot() {
    setStatus('Refreshing the map walkthrough…', 'pending');
    try {
        const [, , , modeData] = await Promise.all([
            loadReceivers(),
            loadPositions(),
            loadStatistics(),
            loadSystemMode(),
        ]);
        if (modeData && modeData.demo_mode) {
            applyScenarioMap(modeData);
        } else {
            await fitBoundsFromApi();
        }
        updateUI();
        setStatus(`Loaded the latest map state from ${getApiBase()}`, websocketAvailable ? 'live' : 'neutral');
    } catch (error) {
        setStatus(`Refresh failed: ${error.message}`, 'error');
    }
}

function disconnectLive() {
    if (socket) {
        socket.disconnect();
        socket = null;
    }
    if (refreshTimer) {
        clearInterval(refreshTimer);
        refreshTimer = null;
    }
    setFeedPill('Feed offline');
    setStatus('Disconnected', 'neutral');
    document.getElementById('hero-status').textContent = 'Offline';
    document.getElementById('hero-feed').textContent = 'Offline';
}

function applyScenarioMap(modeData) {
    const mapConfig = modeData && modeData.scenario && modeData.scenario.map;
    if (!mapConfig || !mapConfig.bounds) {
        return;
    }
    lastBoundsFitAt = Date.now();
    map.fitBounds([
        [mapConfig.bounds.south, mapConfig.bounds.west],
        [mapConfig.bounds.north, mapConfig.bounds.east],
    ], { padding: [56, 56], maxZoom: mapConfig.zoom || 9 });
}

function applyTrackToAircraft(aircraftId, track) {
    if (!track || !Array.isArray(track.positions) || track.positions.length === 0 || !aircraft[aircraftId]) {
        return;
    }

    aircraft[aircraftId].positions = track.positions.map((position) => ({
        lat: position.latitude,
        lon: position.longitude,
        time: position.timestamp,
    })).slice(-80);

    const latLngs = aircraft[aircraftId].positions.map((point) => [point.lat, point.lon]);
    if (aircraftGlowPaths[aircraftId]) {
        aircraftGlowPaths[aircraftId].setLatLngs(latLngs);
    }
    if (aircraftPaths[aircraftId]) {
        aircraftPaths[aircraftId].setLatLngs(latLngs);
    }
}

async function hydrateSelectedAircraft(aircraftId, centerMap = true) {
    const fallback = aircraft[aircraftId];
    if (!fallback) {
        return;
    }

    selectedAircraftId = aircraftId;

    try {
        const [latest, track] = await Promise.all([
            fetchJson(`/api/aircraft/${encodeURIComponent(aircraftId)}/latest`),
            fetchJson(`/api/aircraft/${encodeURIComponent(aircraftId)}/track?limit=100`),
        ]);

        const latestRecord = {
            aircraft_id: latest.aircraft_id,
            position: latest.position,
            uncertainty: latest.uncertainty,
            num_receivers: latest.num_receivers,
            timestamp: latest.timestamp,
        };
        upsertAircraftFromApi(latestRecord, false);
        applyTrackToAircraft(aircraftId, track);
    } catch (_error) {
        // Keep fallback local state when detail endpoints fail.
    }

    const ac = aircraft[aircraftId];
    if (!ac) {
        return;
    }

    renderSelectedAircraft(ac, 'focus');
    if (centerMap) {
        map.setView([ac.lat, ac.lon], 10);
    }
    if (aircraftMarkers[aircraftId]) {
        aircraftMarkers[aircraftId].openPopup();
    }
}

function focusAircraft(aircraftId) {
    hydrateSelectedAircraft(aircraftId, true).catch(() => null);
}

function focusReceiver(receiverId) {
    const receiver = receivers[receiverId];
    if (!receiver) {
        return;
    }
    map.setView([receiver.lat, receiver.lon], 9);
    if (receiverMarkers[receiverId]) {
        receiverMarkers[receiverId].openPopup();
    }
}

async function connectLive() {
    disconnectLive();
    setStatus('Connecting to the map feed…', 'pending');
    setFeedPill('Feed pending');

    try {
        await refreshSnapshot();
    } catch (_error) {
        return;
    }

    if (websocketAvailable && typeof io === 'function') {
        socket = io(getApiBase(), {
            transports: ['websocket', 'polling'],
        });

        socket.on('connect', () => {
            const isDemo = Boolean(systemMode && systemMode.demo_mode);
            const isLive = Boolean(systemMode && !systemMode.demo_mode && !systemMode.simulation_mode);
            setStatus(
                isDemo
                    ? `Connected to ${getApiBase()} with replay updates`
                    : isLive
                        ? `Connected to ${getApiBase()} with live updates`
                        : `Connected to ${getApiBase()} with sample updates`,
                'live',
            );
            setFeedPill(isDemo ? 'Replay stream' : isLive ? 'Live stream' : 'Sample stream');
            document.getElementById('hero-feed').textContent = 'Stream';
            document.getElementById('hero-status').textContent = isDemo ? 'Replay ready' : 'Live ready';
        });

        socket.on('disconnect', () => {
            setStatus('Disconnected', 'neutral');
            setFeedPill('Feed offline');
            document.getElementById('hero-status').textContent = 'Standby';
        });

        socket.on('connect_error', (error) => {
            setStatus(`Stream unavailable, refresh mode only: ${error.message}`, 'error');
            setFeedPill('Refresh mode');
            document.getElementById('hero-feed').textContent = 'Refresh';
        });

        socket.on('position_update', (payload) => {
            if (!payload || !payload.aircraft_id || !payload.position) {
                return;
            }
            upsertAircraftFromApi({
                aircraft_id: payload.aircraft_id,
                ...payload.position,
            }, true);
            updateUI();
            if (selectedAircraftId === payload.aircraft_id) {
                renderSelectedAircraft(aircraft[selectedAircraftId]);
            }
        });
    } else {
        const isDemo = Boolean(systemMode && systemMode.demo_mode);
        const isLive = Boolean(systemMode && !systemMode.demo_mode && !systemMode.simulation_mode);
        setStatus(
            isDemo
                ? `Connected to ${getApiBase()} with replay refreshes`
                : isLive
                    ? `Connected to ${getApiBase()} with refresh-based live updates`
                    : `Connected to ${getApiBase()} with sample refreshes`,
            'live',
        );
        setFeedPill(isDemo ? 'Replay refresh' : isLive ? 'Live refresh' : 'Sample refresh');
        document.getElementById('hero-feed').textContent = 'Refresh';
        document.getElementById('hero-status').textContent = isDemo ? 'Replay ready' : 'Ready';
    }

    refreshTimer = setInterval(() => {
        refreshSnapshot().catch(() => null);
    }, 15000);
}

async function boot() {
    document.getElementById('api-url').value = defaultApiUrl();
    document.getElementById('connect-btn').addEventListener('click', () => connectLive().catch(() => null));
    document.getElementById('refresh-btn').addEventListener('click', () => refreshSnapshot().catch(() => null));
    document.getElementById('disconnect-btn').addEventListener('click', disconnectLive);
    updateReceiverList();
    updateUI();
    const modeData = await loadSystemMode();
    if (modeData && modeData.demo_mode && modeData.demo_auto_connect) {
        connectLive().catch(() => null);
        return;
    }
    connectLive().catch(() => null);
}

boot().catch(() => null);

const map = L.map('map', { zoomControl: false }).setView([40.7128, -74.006], 7);
L.control.zoom({ position: 'topleft' }).addTo(map);
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '© OpenStreetMap © CARTO',
    subdomains: 'abcd',
    maxZoom: 20,
}).addTo(map);

const pageState = {
    aircraft: {},
    receivers: {},
    aircraftMarkers: {},
    receiverMarkers: {},
    aircraftPaths: {},
    aircraftGlowPaths: {},
    aircraftRecentSegments: {},
    aircraftHeadingStubs: {},
    aircraftConfidenceRings: {},
    relationshipLines: [],
    selectedAircraftId: null,
    selectedReceiverId: null,
    socket: null,
    refreshTimer: null,
    ageTimer: null,
    websocketAvailable: false,
    systemMode: null,
    health: null,
    lastBoundsFitAt: 0,
};

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

function fetchJson(path) {
    return fetch(`${getApiBase()}${path}`).then((response) => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status} for ${path}`);
        }
        return response.json();
    });
}

function escapeHtml(value) {
    return String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
}

function formatRelativeTime(epochSeconds) {
    if (!epochSeconds) return 'Awaiting updates';
    const delta = Math.max(0, Math.round((Date.now() / 1000) - Number(epochSeconds || 0)));
    if (delta < 60) return `${delta}s ago`;
    if (delta < 3600) return `${Math.round(delta / 60)}m ago`;
    return `${Math.round(delta / 3600)}h ago`;
}

function formatClock(epochSeconds) {
    if (!epochSeconds) return 'Awaiting timestamp';
    return new Date(epochSeconds * 1000).toLocaleTimeString();
}

function formatDateTime(epochSeconds) {
    if (!epochSeconds) return 'Awaiting timestamp';
    return new Date(epochSeconds * 1000).toLocaleString();
}

function formatCoordinate(lat, lon) {
    if (typeof lat !== 'number' || typeof lon !== 'number') return 'No coordinates';
    return `${lat.toFixed(3)}°, ${lon.toFixed(3)}°`;
}

function formatAltitude(meters) {
    if (typeof meters !== 'number') return 'Unknown altitude';
    return `${Math.round(meters).toLocaleString()}m`;
}

function formatUncertainty(meters) {
    if (typeof meters !== 'number') return 'Unknown uncertainty';
    return `±${Math.round(meters)}m`;
}

function formatQualityPercent(score) {
    if (typeof score !== 'number') return 'n/a';
    return `${Math.round(score * 100)}%`;
}

function formatQualityLabel(quality) {
    if (!quality) return 'No quality data';
    return `${formatQualityPercent(quality.score)} · ${quality.bucket || 'unknown'}`;
}

function formatResidualMeters(value) {
    if (typeof value !== 'number') return 'n/a';
    return `${value.toFixed(1)}m`;
}

function formatTimingSpan(seconds) {
    if (typeof seconds !== 'number') return 'n/a';
    if (seconds < 0.01) return `${(seconds * 1000).toFixed(1)} ms`;
    return `${seconds.toFixed(3)} s`;
}

function formatDistanceMeters(meters) {
    if (typeof meters !== 'number' || !Number.isFinite(meters)) return 'n/a';
    if (meters >= 1000) return `${(meters / 1000).toFixed(1)} km`;
    return `${Math.round(meters)} m`;
}

function formatSpeedKph(value) {
    if (typeof value !== 'number' || !Number.isFinite(value)) return 'n/a';
    return `${Math.round(value)} km/h`;
}

function formatVerticalRateMpm(value) {
    if (typeof value !== 'number' || !Number.isFinite(value)) return 'n/a';
    const rounded = Math.round(value);
    if (rounded === 0) return 'Level trend';
    return `${rounded > 0 ? '+' : ''}${rounded} m/min`;
}

function parseCapabilities(raw) {
    if (Array.isArray(raw)) return raw;
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

function getAircraftList() {
    return Object.values(pageState.aircraft).sort((a, b) => b.timestamp - a.timestamp);
}

function getReceiverList() {
    return Object.values(pageState.receivers).sort((a, b) => a.id.localeCompare(b.id));
}

function getSourceModeLabel(ui) {
    if (ui.isDemo) return 'Replay scenario';
    if (ui.isLive) return 'Live solved positions';
    if (ui.isSimulation) return 'Sample or synthetic positions';
    if (ui.isUnavailable) return 'Configured source waiting';
    return 'Source pending';
}

function getUpdateModeLabel(ui) {
    if (pageState.websocketAvailable) {
        if (ui.isDemo) return 'Replay stream connected';
        if (ui.isLive) return 'Live stream connected';
        if (ui.isSimulation) return 'Sample stream connected';
        return 'Stream connected';
    }
    if (ui.isDemo) return 'Replay refresh-only mode';
    if (ui.isLive) return 'Refresh-only mode';
    if (ui.isSimulation) return 'Sample refresh-only mode';
    if (ui.isUnavailable) return 'Refresh-only mode';
    return 'Refresh-only mode';
}

function titleCase(value) {
    return String(value || '')
        .replaceAll(/[_-]+/g, ' ')
        .replace(/\b\w/g, (match) => match.toUpperCase());
}

function getTrafficModeLabel(ui) {
    if (ui.isDemo) return 'Replay';
    if (ui.isLive) return 'Live';
    if (ui.isSimulation) return 'Sample';
    if (ui.isUnavailable) return 'Waiting for solved output';
    return 'Pending';
}

function getSolverModeLabel(modeData, ui) {
    if (modeData?.strict_production_mode && ui.isLive) return 'Strict live runtime';
    if (modeData?.strict_production_mode) return 'Strict live guardrail';
    if (ui.isDemo) return 'Replay walkthrough runtime';
    if (ui.isSimulation) return 'Synthetic demonstration runtime';
    if (ui.isLive) return 'Operational MLAT runtime';
    return 'Runtime not active';
}

function getDataSourceLabel(modeData, ui) {
    if (ui.isDemo) return modeData?.demo_label || 'Recorded scenario';
    if (ui.isSimulation) {
        if (modeData?.configured_transport) {
            return `${titleCase(modeData.configured_transport)} transport`;
        }
        return 'Synthetic traffic source';
    }
    if (ui.isLive) {
        return modeData?.runtime_telemetry_source || titleCase(modeData?.configured_transport || 'live transport');
    }
    return titleCase(modeData?.configured_transport || 'configured source');
}

function getScenarioLabel(modeData) {
    return modeData?.scenario?.label || modeData?.demo_label || null;
}

function getScenarioContextLabel(modeData) {
    const scenario = modeData?.scenario;
    if (!scenario) return null;
    return scenario.region || scenario.location || scenario.label || null;
}

function deriveUiState() {
    const modeData = pageState.systemMode;
    const aircraftList = getAircraftList();
    const receiverList = getReceiverList();
    const aircraftCount = aircraftList.length;
    const receiverCount = receiverList.length;
    const hasAircraft = aircraftCount > 0;
    const hasReceivers = receiverCount > 0;
    const runtimeStatus = modeData?.runtime_status || 'unavailable';
    const isDemo = Boolean(modeData?.demo_mode);
    const isSimulation = Boolean(modeData?.simulation_mode || modeData?.synthetic_feed_mode);
    const isLive = Boolean(modeData && runtimeStatus === 'active' && !isDemo && !isSimulation);
    const isUnavailable = runtimeStatus !== 'active' && !isDemo && !isSimulation;
    const scenarioLabel = getScenarioLabel(modeData) || 'Demo replay';
    const scenarioSummary = modeData?.scenario?.summary || 'Replay traffic is active for walkthrough mode.';

    let sourceTitle = 'Waiting for localization source';
    let sourceCopy = 'Checking whether positions are live, replayed, sampled, or unavailable.';
    let modePill = 'Waiting';
    let modeTone = 'mode-sim';
    let demoBanner = null;

    if (isDemo) {
        sourceTitle = `Replay operations view: ${scenarioLabel}`;
        sourceCopy = `${scenarioSummary} The page shows the latest solved-position evidence available from the replay payload rather than raw packet chronology.`;
        modePill = 'Replay source';
        demoBanner = {
            title: scenarioLabel,
            copy: 'Replay stream connected. This remains explicitly non-live while preserving the same operator-facing localization story.',
        };
    } else if (isSimulation) {
        sourceTitle = 'Sample localization source is active';
        sourceCopy = 'These positions are coming from sample or synthetic traffic. The page still explains receiver contribution, solver evidence, and publication freshness using current runtime payloads.';
        modePill = 'Sample source';
    } else if (isLive) {
        sourceTitle = 'Live MLAT localization source is active';
        sourceCopy = 'These aircraft positions are being solved from active receiver inputs. Select an aircraft to inspect contributing receivers, solver evidence, and how the derived position was published to the dashboard.';
        modePill = 'Live source';
        modeTone = 'mode-live';
    } else if (modeData?.mode === 'configured_live') {
        sourceTitle = 'Live transport is configured, but fresh solved positions are not available';
        sourceCopy = 'Receiver metadata may load before fresh solver output appears. Once solved positions arrive, the map and inspector will show a recent solve chain instead of a packet-level event ledger.';
        modePill = 'Source unavailable';
    }

    const feedLabel = getUpdateModeLabel({ isDemo, isLive, isSimulation, isUnavailable });

    let mapStatus = 'Waiting for positions';
    if (hasAircraft) {
        mapStatus = isDemo
            ? 'Replay positions visible'
            : isLive
                ? 'Live positions visible'
                : isSimulation
                    ? 'Sample positions visible'
                    : 'Positions visible';
    } else if (hasReceivers) {
        mapStatus = 'Receivers loaded. No aircraft positions available yet.';
    } else if (isUnavailable) {
        mapStatus = 'Disconnected from solved output';
    } else if (isDemo) {
        mapStatus = 'Waiting for replay positions';
    } else if (isLive) {
        mapStatus = 'Waiting for live positions';
    } else if (isSimulation) {
        mapStatus = 'Waiting for sample positions';
    }

    return {
        sourceTitle,
        sourceCopy,
        modePill,
        modeTone,
        feedLabel,
        heroMode: getTrafficModeLabel({ isDemo, isLive, isSimulation, isUnavailable }),
        heroFeed: feedLabel,
        heroStatus: mapStatus,
        mapStatus,
        hasAircraft,
        hasReceivers,
        isDemo,
        isLive,
        isSimulation,
        isUnavailable,
        aircraftCount,
        receiverCount,
        demoBanner,
        facts: {
            dataSource: getDataSourceLabel(modeData, { isDemo, isLive, isSimulation, isUnavailable }),
            scenario: getScenarioLabel(modeData),
            scenarioContext: getScenarioContextLabel(modeData),
            trafficMode: getTrafficModeLabel({ isDemo, isLive, isSimulation, isUnavailable }),
            solverMode: getSolverModeLabel(modeData, { isDemo, isLive, isSimulation, isUnavailable }),
            updateMode: feedLabel,
        },
    };
}

function setDockStatus(message, tone = 'neutral') {
    const dockStatus = document.getElementById('map-dock-status');
    if (!dockStatus) return;
    dockStatus.textContent = message;
    dockStatus.className = `map-dock-status tone-${tone}`;
}

function getConnectionPanelStatusLabel(tone, message) {
    if (tone === 'live') return message;
    if (tone === 'pending') return 'Connecting';
    if (tone === 'error') return 'Connection issue';
    return 'Disconnected';
}

function setConnectionStatus(message, tone = 'neutral') {
    const connectionNode = document.getElementById('connection-status');
    if (connectionNode) {
        connectionNode.textContent = message;
        connectionNode.className = `inline-pill ${tone === 'live' ? 'tone-live' : tone === 'error' ? 'tone-error' : tone === 'pending' ? 'tone-pending' : ''}`.trim();
    }
    setDockStatus(getConnectionPanelStatusLabel(tone, message), tone);
    const heroStatus = document.getElementById('hero-status');
    if (heroStatus && tone !== 'live') {
        heroStatus.textContent = getConnectionPanelStatusLabel(tone, message);
    }
}

function setFeedPill(message) {
    const node = document.getElementById('feed-pill');
    if (node) node.textContent = message;
}

function renderSourceFacts(ui) {
    const factsNode = document.getElementById('source-facts');
    if (!factsNode) return;
    const rows = [
        ['Source', ui.facts.dataSource],
        ...(ui.facts.scenario ? [['Scenario', ui.facts.scenario]] : []),
        ['Mode', ui.facts.trafficMode],
        ['Updates', ui.facts.updateMode],
    ];
    factsNode.innerHTML = rows.map(([label, value]) => `
        <div class="localization-source-fact">
            <strong>${escapeHtml(label)}</strong>
            <span>${escapeHtml(value || 'n/a')}</span>
        </div>
    `).join('');
}

function renderModeSummary() {
    const ui = deriveUiState();
    const modePill = document.getElementById('mode-pill');
    const sourceRuntimePill = document.getElementById('source-runtime-pill');
    const sourceTitle = document.getElementById('source-summary-title');
    const sourceCopy = document.getElementById('source-summary-copy');
    const heroMode = document.getElementById('hero-mode');
    const heroFeed = document.getElementById('hero-feed');
    const heroStatus = document.getElementById('hero-status');
    const mapHudStatus = document.getElementById('map-hud-status');
    const demoChip = document.getElementById('demo-chip');
    const demoBanner = document.getElementById('demo-banner');
    const demoBannerTitle = document.getElementById('demo-banner-title');
    const demoBannerCopy = document.getElementById('demo-banner-copy');

    modePill.textContent = ui.modePill;
    modePill.className = `status-pill ${ui.modeTone}`;
    sourceRuntimePill.textContent = ui.modePill;
    sourceRuntimePill.className = `status-pill ${ui.modeTone}`;
    sourceTitle.textContent = ui.sourceTitle;
    sourceCopy.textContent = ui.sourceCopy;
    heroMode.textContent = ui.heroMode;
    heroFeed.textContent = ui.heroFeed;
    heroStatus.textContent = ui.heroStatus;
    mapHudStatus.textContent = ui.mapStatus;
    mapHudStatus.className = `map-hud-status ${ui.isLive ? 'is-live connection-pulse' : ''}`.trim();
    setFeedPill(ui.feedLabel);
    renderSourceFacts(ui);

    demoChip.hidden = !ui.demoBanner;
    demoBanner.hidden = !ui.demoBanner;
    if (ui.demoBanner) {
        demoChip.textContent = 'Demo replay';
        demoBannerTitle.textContent = ui.demoBanner.title;
        demoBannerCopy.textContent = ui.demoBanner.copy;
    }
}

function clearAircraftState() {
    Object.values(pageState.aircraftMarkers).forEach((marker) => map.removeLayer(marker));
    Object.values(pageState.aircraftPaths).forEach((path) => map.removeLayer(path));
    Object.values(pageState.aircraftGlowPaths).forEach((path) => map.removeLayer(path));
    Object.values(pageState.aircraftRecentSegments).forEach((path) => map.removeLayer(path));
    Object.values(pageState.aircraftHeadingStubs).forEach((path) => map.removeLayer(path));
    Object.values(pageState.aircraftConfidenceRings).forEach((ring) => map.removeLayer(ring));
    pageState.aircraft = {};
    pageState.aircraftMarkers = {};
    pageState.aircraftPaths = {};
    pageState.aircraftGlowPaths = {};
    pageState.aircraftRecentSegments = {};
    pageState.aircraftHeadingStubs = {};
    pageState.aircraftConfidenceRings = {};
    pageState.selectedAircraftId = null;
}

function clearRelationshipLines() {
    pageState.relationshipLines.forEach((line) => map.removeLayer(line));
    pageState.relationshipLines = [];
}

function getAircraftPopup(ac) {
    return `
        <b>Aircraft ${escapeHtml(ac.id)}</b><br>
        Position: ${ac.lat.toFixed(4)}°, ${ac.lon.toFixed(4)}°<br>
        Altitude: ${Math.round(ac.alt)}m (${Math.round(ac.alt * 3.28084)}ft)<br>
        Receivers: ${ac.numReceivers || 0}<br>
        Confidence: ${formatQualityLabel(ac.quality)}<br>
        Estimated error: ${formatUncertainty(ac.uncertainty)}<br>
        Last update: ${formatClock(ac.timestamp)}
    `;
}

function getReceiverPopup(receiver) {
    return `
        <b>${escapeHtml(receiver.id)}</b><br>
        Position: ${receiver.lat.toFixed(4)}°, ${receiver.lon.toFixed(4)}°<br>
        Altitude: ${Math.round(receiver.alt)}m<br>
        Status: ${escapeHtml(receiver.status)}<br>
        Capabilities: ${escapeHtml(receiver.capabilities.join(', ') || 'n/a')}
    `;
}

function getReceiverUsageCount(receiverId) {
    return getAircraftList().filter((aircraft) => getReceiverIdsForAircraft(aircraft).includes(receiverId)).length;
}

function deriveReceiverHealth(receiver) {
    const status = String(receiver?.status || '').toLowerCase();
    const lastSeen = Number(receiver?.lastSeen || 0);
    if (['active', 'online'].includes(status) && lastSeen && ((Date.now() / 1000) - lastSeen) <= 20) {
        return { label: 'Online now', className: 'live' };
    }
    if (['active', 'online'].includes(status)) {
        return { label: 'Online, aging', className: '' };
    }
    if (lastSeen) {
        return { label: 'Recently seen', className: '' };
    }
    return { label: 'Status unknown', className: '' };
}

function upsertReceiver(receiver) {
    const model = {
        id: receiver.receiver_id,
        name: receiver.receiver_id,
        lat: receiver.latitude,
        lon: receiver.longitude,
        alt: receiver.altitude,
        status: receiver.status,
        capabilities: parseCapabilities(receiver.capabilities),
        lastSeen: receiver.last_seen,
        updatedAt: receiver.updated_at,
    };
    pageState.receivers[receiver.receiver_id] = model;

    if (pageState.receiverMarkers[receiver.receiver_id]) {
        pageState.receiverMarkers[receiver.receiver_id].setLatLng([model.lat, model.lon]);
        pageState.receiverMarkers[receiver.receiver_id].setPopupContent(getReceiverPopup(model));
    } else {
        pageState.receiverMarkers[receiver.receiver_id] = L.marker([model.lat, model.lon], { icon: receiverIcon })
            .addTo(map)
            .bindPopup(getReceiverPopup(model))
            .on('click', () => focusReceiver(receiver.receiver_id, true));
    }
}

function normalizeAircraftRecord(record) {
    const lat = record.position ? record.position.latitude : record.latitude;
    const lon = record.position ? record.position.longitude : record.longitude;
    const alt = record.position ? record.position.altitude : record.altitude;
    const receiverIds = Array.isArray(record.correlation?.receiver_ids) ? record.correlation.receiver_ids : [];
    return {
        id: record.aircraft_id,
        lat,
        lon,
        alt: alt || 0,
        uncertainty: record.uncertainty || 0,
        numReceivers: record.num_receivers || receiverIds.length || record.correlation?.receiver_count || 0,
        timestamp: record.timestamp || Date.now() / 1000,
        quality: record.quality || null,
        solver: record.solver || null,
        createdAt: record.created_at || null,
        correlation: {
            ...(record.correlation || {}),
            receiver_ids: receiverIds,
        },
    };
}

function getTrackPointFromAircraft(aircraft, point) {
    return {
        lat: point.latitude ?? point.lat,
        lon: point.longitude ?? point.lon,
        alt: point.altitude ?? point.alt ?? aircraft?.alt ?? null,
        time: point.timestamp ?? point.time ?? null,
        uncertainty: point.uncertainty ?? null,
        numReceivers: point.num_receivers ?? null,
        quality: point.quality ?? null,
        solver: point.solver ?? null,
        correlation: point.correlation ?? null,
        createdAt: point.created_at ?? null,
    };
}

function appendAircraftPosition(aircraft, point) {
    const normalizedPoint = getTrackPointFromAircraft(aircraft, point);
    const prior = aircraft.positions[aircraft.positions.length - 1];
    const isDuplicate = prior
        && prior.lat === normalizedPoint.lat
        && prior.lon === normalizedPoint.lon
        && prior.time === normalizedPoint.time;
    if (!isDuplicate) {
        aircraft.positions.push(normalizedPoint);
    }
    if (aircraft.positions.length > 80) {
        aircraft.positions = aircraft.positions.slice(-80);
    }
}

function refreshAircraftOverlays(aircraftId) {
    const aircraft = pageState.aircraft[aircraftId];
    if (!aircraft) return;
    const latLngs = aircraft.positions.map((point) => [point.lat, point.lon]);
    if (pageState.aircraftGlowPaths[aircraftId]) pageState.aircraftGlowPaths[aircraftId].setLatLngs(latLngs);
    if (pageState.aircraftPaths[aircraftId]) pageState.aircraftPaths[aircraftId].setLatLngs(latLngs);

    const recentSegment = latLngs.length >= 2 ? latLngs.slice(-2) : [];
    if (!pageState.aircraftRecentSegments[aircraftId]) {
        pageState.aircraftRecentSegments[aircraftId] = L.polyline([], {
            color: '#ffd2bc',
            weight: 4.8,
            opacity: 0.95,
            lineCap: 'round',
            lineJoin: 'round',
        }).addTo(map);
    }
    pageState.aircraftRecentSegments[aircraftId].setLatLngs(recentSegment);

    const headingStub = buildHeadingStub(aircraft.positions);
    if (!pageState.aircraftHeadingStubs[aircraftId]) {
        pageState.aircraftHeadingStubs[aircraftId] = L.polyline([], {
            color: 'rgba(255, 210, 188, 0.88)',
            weight: 2,
            opacity: 1,
            dashArray: '3 5',
            lineCap: 'round',
            interactive: false,
        }).addTo(map);
    }
    pageState.aircraftHeadingStubs[aircraftId].setLatLngs(headingStub ? [[headingStub.start.lat, headingStub.start.lon], [headingStub.end.lat, headingStub.end.lon]] : []);

    const ringRadius = getConfidenceRingRadiusMeters(aircraft.uncertainty);
    if (!pageState.aircraftConfidenceRings[aircraftId]) {
        pageState.aircraftConfidenceRings[aircraftId] = L.circle([aircraft.lat, aircraft.lon], {
            radius: 0,
            color: 'rgba(255, 186, 154, 0.95)',
            weight: 1.2,
            opacity: 0.9,
            fillColor: 'rgba(255, 124, 72, 0.08)',
            fillOpacity: 0.14,
            className: 'map-confidence-ring',
            interactive: false,
        }).addTo(map);
    }
    pageState.aircraftConfidenceRings[aircraftId].setLatLng([aircraft.lat, aircraft.lon]);
    pageState.aircraftConfidenceRings[aircraftId].setRadius(ringRadius || 0);
}

function upsertAircraftFromApi(record) {
    const normalized = normalizeAircraftRecord(record);
    if (typeof normalized.lat !== 'number' || typeof normalized.lon !== 'number') return;

    if (!pageState.aircraft[normalized.id]) {
        pageState.aircraft[normalized.id] = {
            ...normalized,
            positions: [],
        };
    }

    const aircraft = pageState.aircraft[normalized.id];
    Object.assign(aircraft, normalized);
    appendAircraftPosition(aircraft, {
        lat: normalized.lat,
        lon: normalized.lon,
        alt: normalized.alt,
        time: normalized.timestamp,
        uncertainty: normalized.uncertainty,
        quality: normalized.quality,
        solver: normalized.solver,
        correlation: normalized.correlation,
        created_at: normalized.createdAt,
    });

    if (!pageState.aircraftMarkers[normalized.id]) {
        pageState.aircraftMarkers[normalized.id] = L.marker([normalized.lat, normalized.lon], { icon: aircraftIcon })
            .addTo(map)
            .bindPopup(getAircraftPopup(aircraft))
            .on('click', () => focusAircraft(normalized.id, true));
    } else {
        pageState.aircraftMarkers[normalized.id].setLatLng([normalized.lat, normalized.lon]);
        pageState.aircraftMarkers[normalized.id].setPopupContent(getAircraftPopup(aircraft));
    }

    if (!pageState.aircraftGlowPaths[normalized.id]) {
        pageState.aircraftGlowPaths[normalized.id] = L.polyline([], {
            color: 'rgba(255, 100, 34, 0.12)',
            weight: 12,
            opacity: 1,
            lineCap: 'round',
            lineJoin: 'round',
            interactive: false,
        }).addTo(map);
        pageState.aircraftPaths[normalized.id] = L.polyline([], {
            color: '#ff6422',
            weight: 2,
            opacity: 0.82,
            lineCap: 'round',
            lineJoin: 'round',
            interactive: false,
        }).addTo(map);
    }

    refreshAircraftOverlays(normalized.id);
}

function maybeFitMap() {
    const now = Date.now();
    if (now - pageState.lastBoundsFitAt < 10000) return;
    const points = [
        ...Object.values(pageState.aircraft).map((ac) => [ac.lat, ac.lon]),
        ...Object.values(pageState.receivers).map((recv) => [recv.lat, recv.lon]),
    ];
    if (!points.length) return;
    pageState.lastBoundsFitAt = now;
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
        pageState.lastBoundsFitAt = Date.now();
        map.fitBounds([
            [bounds.south, bounds.west],
            [bounds.north, bounds.east],
        ], { padding: [56, 56], maxZoom: 9 });
    } catch (_error) {
        maybeFitMap();
    }
}

function applyScenarioMap(modeData) {
    const mapConfig = modeData?.scenario?.map;
    if (!mapConfig?.bounds) return;
    pageState.lastBoundsFitAt = Date.now();
    map.fitBounds([
        [mapConfig.bounds.south, mapConfig.bounds.west],
        [mapConfig.bounds.north, mapConfig.bounds.east],
    ], { padding: [56, 56], maxZoom: mapConfig.zoom || 9 });
}

function applyTrackToAircraft(aircraftId, track) {
    const aircraft = pageState.aircraft[aircraftId];
    if (!aircraft || !Array.isArray(track?.positions) || !track.positions.length) return;
    aircraft.positions = track.positions.map((position) => getTrackPointFromAircraft(aircraft, position)).slice(-80);
    refreshAircraftOverlays(aircraftId);
}

function getReceiverIdsForAircraft(aircraft) {
    return aircraft?.correlation?.receiver_ids || [];
}

function getVisibleReceiverRows(receiverIds) {
    return receiverIds.map((receiverId) => pageState.receivers[receiverId]).filter(Boolean);
}

function describeFreshness(aircraft) {
    const ageSeconds = Math.max(0, Math.round((Date.now() / 1000) - Number(aircraft?.timestamp || 0)));
    if (!aircraft?.timestamp) {
        return {
            label: 'Freshness unknown',
            reason: 'No recent timestamp is available for this aircraft position.',
        };
    }
    if (ageSeconds <= 10) {
        return {
            label: 'Fresh update',
            reason: `This aircraft position was updated ${formatRelativeTime(aircraft.timestamp)} and is still current on the map.`,
        };
    }
    if (ageSeconds <= 45) {
        return {
            label: 'Aging update',
            reason: `This aircraft position is ${formatRelativeTime(aircraft.timestamp)}, so the display may be slightly behind the latest traffic.`,
        };
    }
    return {
        label: 'Stale update',
        reason: `This aircraft position is ${formatRelativeTime(aircraft.timestamp)}, so confirm that live or replay updates are still arriving.`,
    };
}

function describeUncertainty(aircraft) {
    const value = aircraft?.uncertainty;
    if (typeof value !== 'number') {
        return {
            label: 'Estimated error unavailable',
            reason: 'The runtime did not expose an estimated position error for this aircraft update.',
        };
    }
    if (value <= 75) {
        return {
            label: 'Tight estimated error band',
            reason: `Estimated position error is ${formatUncertainty(value)}, which is relatively tight for this update.`,
        };
    }
    if (value <= 200) {
        return {
            label: 'Moderate estimated error band',
            reason: `Estimated position error is ${formatUncertainty(value)}, so treat the displayed position as approximate rather than exact.`,
        };
    }
    return {
        label: 'Wide estimated error band',
        reason: `Estimated position error is ${formatUncertainty(value)}, so confidence in the exact location is lower.`,
    };
}

function describeResidual(aircraft) {
    const value = aircraft?.solver?.residual_m;
    if (typeof value !== 'number') {
        return null;
    }
    if (value <= 100) return 'solver residual remains low';
    if (value <= 300) return 'solver residual is moderate';
    return 'solver residual remains elevated';
}

function buildQualityReason(aircraft) {
    const reasons = [];
    const receiverCount = getReceiverIdsForAircraft(aircraft).length || aircraft?.numReceivers || 0;
    if (receiverCount) {
        reasons.push(`${receiverCount} receiver${receiverCount === 1 ? '' : 's'} contributed`);
    }
    if (typeof aircraft?.correlation?.time_span_s === 'number') {
        reasons.push(`timing span ${formatTimingSpan(aircraft.correlation.time_span_s)}`);
    }
    if (typeof aircraft?.uncertainty === 'number') {
        reasons.push(`estimated error ${formatUncertainty(aircraft.uncertainty)}`);
    }
    if (typeof aircraft?.solver?.residual_m === 'number') {
        reasons.push(`residual ${formatResidualMeters(aircraft.solver.residual_m)}`);
    }
    if (typeof aircraft?.solver?.iterations === 'number') {
        reasons.push(`${aircraft.solver.iterations} solver iteration${aircraft.solver.iterations === 1 ? '' : 's'}`);
    }
    if (!reasons.length) {
        return 'Confidence interpretation is limited because the current payload does not include enough supporting evidence.';
    }
    return `Confidence is grounded in the latest solve evidence: ${reasons.join(', ')}.`;
}

function getQualityToneClass(score) {
    if (typeof score !== 'number') return 'tone-neutral';
    if (score >= 0.8) return 'tone-good';
    if (score >= 0.55) return 'tone-warn';
    return 'tone-risk';
}

function getRelationshipLineStyle(isSelected) {
    return {
        color: isSelected ? 'rgba(255, 184, 150, 0.92)' : 'rgba(255, 120, 82, 0.52)',
        weight: isSelected ? 2.4 : 1.6,
        opacity: 1,
        dashArray: isSelected ? '10 6' : '6 8',
        lineCap: 'round',
        interactive: false,
        className: isSelected ? 'map-relationship-line is-selected' : 'map-relationship-line',
    };
}

function getConfidenceRingRadiusMeters(uncertainty) {
    if (typeof uncertainty !== 'number' || uncertainty <= 0) return null;
    return Math.max(uncertainty, 35);
}

function toRadians(value) {
    return value * (Math.PI / 180);
}

function toDegrees(value) {
    return value * (180 / Math.PI);
}

function computeDistanceMeters(a, b) {
    if (!a || !b) return null;
    const lat1 = toRadians(a.lat);
    const lat2 = toRadians(b.lat);
    const dLat = lat2 - lat1;
    const dLon = toRadians(b.lon - a.lon);
    const hav = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) ** 2;
    const c = 2 * Math.atan2(Math.sqrt(hav), Math.sqrt(1 - hav));
    return 6371000 * c;
}

function computeBearingDegrees(a, b) {
    if (!a || !b) return null;
    const lat1 = toRadians(a.lat);
    const lat2 = toRadians(b.lat);
    const dLon = toRadians(b.lon - a.lon);
    const y = Math.sin(dLon) * Math.cos(lat2);
    const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLon);
    const bearing = (toDegrees(Math.atan2(y, x)) + 360) % 360;
    return Number.isFinite(bearing) ? bearing : null;
}

function bearingToCompass(bearing) {
    if (typeof bearing !== 'number') return null;
    const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
    return directions[Math.round(bearing / 45) % 8];
}

function destinationPoint(start, bearingDeg, distanceMeters) {
    const angularDistance = distanceMeters / 6371000;
    const bearing = toRadians(bearingDeg);
    const lat1 = toRadians(start.lat);
    const lon1 = toRadians(start.lon);

    const lat2 = Math.asin(
        Math.sin(lat1) * Math.cos(angularDistance)
        + Math.cos(lat1) * Math.sin(angularDistance) * Math.cos(bearing),
    );
    const lon2 = lon1 + Math.atan2(
        Math.sin(bearing) * Math.sin(angularDistance) * Math.cos(lat1),
        Math.cos(angularDistance) - Math.sin(lat1) * Math.sin(lat2),
    );

    return {
        lat: toDegrees(lat2),
        lon: toDegrees(lon2),
    };
}

function getRecentTrackPoints(aircraft, limit = 6) {
    return Array.isArray(aircraft?.positions) ? aircraft.positions.slice(-limit) : [];
}

function deriveTrackBehavior(aircraft) {
    const points = getRecentTrackPoints(aircraft, 6).filter((point) => typeof point.lat === 'number' && typeof point.lon === 'number' && typeof point.time === 'number');
    if (points.length < 2) {
        return {
            heading: null,
            headingLabel: null,
            speedKph: null,
            verticalRateMpm: null,
            trackAgeLabel: aircraft?.positions?.length ? `${aircraft.positions.length} recent solve${aircraft.positions.length === 1 ? '' : 's'}` : 'Single solved position',
            trackHistoryPoints: aircraft?.positions?.length || 0,
        };
    }

    const latest = points[points.length - 1];
    const previous = points[points.length - 2];
    const deltaSeconds = latest.time - previous.time;
    const distanceMeters = deltaSeconds > 0 ? computeDistanceMeters(previous, latest) : null;
    const heading = computeBearingDegrees(previous, latest);

    let speedKph = null;
    if (distanceMeters && deltaSeconds >= 5 && deltaSeconds <= 300) {
        speedKph = (distanceMeters / deltaSeconds) * 3.6;
        if (!Number.isFinite(speedKph) || speedKph > 1400) speedKph = null;
    }

    let verticalRateMpm = null;
    const altitudeDelta = (typeof latest.alt === 'number' && typeof previous.alt === 'number') ? latest.alt - previous.alt : null;
    if (typeof altitudeDelta === 'number' && deltaSeconds >= 10 && deltaSeconds <= 300) {
        verticalRateMpm = (altitudeDelta / deltaSeconds) * 60;
        if (!Number.isFinite(verticalRateMpm) || Math.abs(verticalRateMpm) > 6000) verticalRateMpm = null;
    }

    const trackAgeSeconds = Math.max(0, latest.time - points[0].time);
    let trackAgeLabel = 'Recent solve chain';
    if (trackAgeSeconds > 0) {
        trackAgeLabel = trackAgeSeconds < 60
            ? `${Math.round(trackAgeSeconds)}s solve chain`
            : `${Math.round(trackAgeSeconds / 60)}m solve chain`;
    }

    return {
        heading,
        headingLabel: heading != null ? `${Math.round(heading)}° ${bearingToCompass(heading)}` : null,
        speedKph,
        verticalRateMpm,
        trackAgeLabel,
        trackHistoryPoints: points.length,
    };
}

function buildHeadingStub(points) {
    const recent = points.filter((point) => typeof point.lat === 'number' && typeof point.lon === 'number' && typeof point.time === 'number').slice(-3);
    if (recent.length < 2) return null;
    const latest = recent[recent.length - 1];
    const previous = recent[recent.length - 2];
    const bearing = computeBearingDegrees(previous, latest);
    const baseDistance = computeDistanceMeters(previous, latest);
    if (bearing == null || !baseDistance) return null;
    const distance = Math.min(Math.max(baseDistance * 0.5, 120), 1200);
    return {
        start: { lat: latest.lat, lon: latest.lon },
        end: destinationPoint({ lat: latest.lat, lon: latest.lon }, bearing, distance),
    };
}

function getConfidenceBucketLabel(aircraft) {
    if (aircraft?.quality?.bucket) return titleCase(aircraft.quality.bucket);
    const score = aircraft?.quality?.score;
    if (typeof score !== 'number') return 'Unscored';
    if (score >= 0.8) return 'High confidence';
    if (score >= 0.55) return 'Moderate confidence';
    return 'Low confidence';
}

function getSourceModeDetail(aircraft) {
    const ui = deriveUiState();
    if (ui.isDemo) return 'Replay scenario payload';
    if (ui.isSimulation) return 'Synthetic or sample payload';
    const solverMethod = String(aircraft?.solver?.method || '').toLowerCase();
    if (solverMethod.includes('synthetic')) return 'Synthetic payload';
    return 'Current solved position payload';
}

function getProvenanceFreshnessLabel(aircraft, trackPoints) {
    const latestCreatedAt = aircraft?.createdAt;
    if (typeof latestCreatedAt === 'number') {
        return `Published ${formatRelativeTime(latestCreatedAt)} at ${formatDateTime(latestCreatedAt)}`;
    }
    const newestTrack = trackPoints[trackPoints.length - 1];
    if (newestTrack?.time) {
        return `Position timestamp ${formatRelativeTime(newestTrack.time)} at ${formatDateTime(newestTrack.time)}`;
    }
    return 'Publication freshness unavailable';
}

function buildProvenanceEvents(aircraft, receiverRows) {
    const events = [];
    const receiverIds = getReceiverIdsForAircraft(aircraft);
    const trackPoints = getRecentTrackPoints(aircraft, 8);
    const correlationSpan = aircraft?.correlation?.time_span_s;
    const solverMethod = aircraft?.solver?.method || 'Unknown solver';
    const residual = aircraft?.solver?.residual_m;
    const iterations = aircraft?.solver?.iterations;

    events.push({
        title: 'Receiver registry visible',
        detail: receiverRows.length
            ? `${receiverRows.length} named receiver${receiverRows.length === 1 ? '' : 's'} are loaded in the current registry for this solve chain.`
            : receiverIds.length
                ? `${receiverIds.length} receiver identifier${receiverIds.length === 1 ? '' : 's'} are referenced by the latest solved position payload, but registry metadata has not fully loaded.`
                : 'Receiver registry is loaded, but this payload did not expose contributing receiver identities.',
        meta: receiverRows.length
            ? receiverRows.map((receiver) => receiver.id).join(', ')
            : receiverIds.join(', ') || 'No receiver IDs exposed',
        tone: 'neutral',
    });

    events.push({
        title: 'Contributing receivers identified',
        detail: receiverIds.length
            ? `${receiverIds.length} receiver${receiverIds.length === 1 ? '' : 's'} are attached to the latest solve provenance.`
            : `${aircraft?.numReceivers || 0} receiver${(aircraft?.numReceivers || 0) === 1 ? '' : 's'} were counted in the solution, but individual IDs were not exposed here.`,
        meta: receiverIds.length ? `${receiverIds.length} in latest payload` : `${aircraft?.numReceivers || 0} counted`,
        tone: 'neutral',
    });

    events.push({
        title: 'Timestamp alignment evidence',
        detail: typeof correlationSpan === 'number'
            ? `The current solve references a cross-receiver timing span of ${formatTimingSpan(correlationSpan)}.`
            : 'Timing span was not included in this payload, so only receiver participation can be shown.',
        meta: typeof correlationSpan === 'number' ? formatTimingSpan(correlationSpan) : 'Timing span unavailable',
        tone: typeof correlationSpan === 'number' ? 'good' : 'neutral',
    });

    events.push({
        title: 'MLAT solver evidence',
        detail: `Solver method ${solverMethod}${typeof residual === 'number' ? ` produced residual ${formatResidualMeters(residual)}` : ''}${typeof iterations === 'number' ? ` over ${iterations} iteration${iterations === 1 ? '' : 's'}` : ''}.`,
        meta: solverMethod,
        tone: typeof residual === 'number' && residual <= 100 ? 'good' : typeof residual === 'number' && residual > 300 ? 'risk' : 'neutral',
    });

    events.push({
        title: 'Derived position timestamp',
        detail: aircraft?.timestamp
            ? `The current map position is tied to solve timestamp ${formatDateTime(aircraft.timestamp)}.`
            : 'Solve timestamp is unavailable for this selected aircraft.',
        meta: aircraft?.timestamp ? formatRelativeTime(aircraft.timestamp) : 'Awaiting timestamp',
        tone: 'neutral',
    });

    events.push({
        title: 'Stored and published output freshness',
        detail: typeof aircraft?.createdAt === 'number'
            ? `This solved position includes created_at, so publication freshness can be shown directly from stored output.`
            : 'This page is showing a recent solve chain derived from solved position payloads. created_at was not available on all history entries, so this is not a raw ingest timeline.',
        meta: getProvenanceFreshnessLabel(aircraft, trackPoints),
        tone: typeof aircraft?.createdAt === 'number' ? 'good' : 'neutral',
    });

    return events;
}

function buildPipeline(receiverRows, aircraft) {
    const receiverCount = receiverRows.length || aircraft.numReceivers || 0;
    return `
        <div class="localization-pipeline localization-pipeline-compact" aria-label="How this position was derived">
            <div class="localization-pipeline-step is-receivers">
                <strong>Receivers</strong>
                <span>${escapeHtml(`${receiverCount} used`)}</span>
            </div>
            <div class="localization-pipeline-arrow" aria-hidden="true">→</div>
            <div class="localization-pipeline-step">
                <strong>Timing</strong>
                <span>${escapeHtml(typeof aircraft.correlation?.time_span_s === 'number' ? formatTimingSpan(aircraft.correlation.time_span_s) : 'Compared')}</span>
            </div>
            <div class="localization-pipeline-arrow" aria-hidden="true">→</div>
            <div class="localization-pipeline-step is-solver">
                <strong>Solver</strong>
                <span>${escapeHtml(aircraft.solver?.method || 'MLAT')}</span>
            </div>
            <div class="localization-pipeline-arrow" aria-hidden="true">→</div>
            <div class="localization-pipeline-step is-output">
                <strong>Position</strong>
                <span>${escapeHtml(formatUncertainty(aircraft.uncertainty))}</span>
            </div>
        </div>
    `;
}

function renderReceiverList() {
    const list = document.getElementById('receiver-list');
    const receivers = getReceiverList();
    if (!receivers.length) {
        list.innerHTML = '<div class="empty-state">Receiver identities will appear here once registry data loads. Aircraft positions can still arrive before that metadata is ready.</div>';
        document.getElementById('receiver-count').textContent = '0';
        document.getElementById('receiver-detail').textContent = 'Waiting for receivers';
        return;
    }

    list.innerHTML = receivers.map((receiver) => {
        const health = deriveReceiverHealth(receiver);
        const supportCount = getReceiverUsageCount(receiver.id);
        return `
            <button class="receiver-item ${receiver.id === pageState.selectedReceiverId ? 'is-selected' : ''}" type="button" data-receiver-id="${escapeHtml(receiver.id)}">
                <div>
                    <strong>${escapeHtml(receiver.name)}</strong>
                    <span>${escapeHtml(`${health.label} · last seen ${formatRelativeTime(receiver.lastSeen)}`)}</span>
                    <span>${escapeHtml(`Supporting ${supportCount} visible aircraft`)}</span>
                </div>
                <div class="receiver-status ${health.className}">${escapeHtml(receiver.status || 'unknown')}</div>
            </button>
        `;
    }).join('');

    list.querySelectorAll('[data-receiver-id]').forEach((button) => {
        button.addEventListener('click', () => focusReceiver(button.dataset.receiverId, true));
    });

    document.getElementById('receiver-count').textContent = String(receivers.length);
    document.getElementById('receiver-detail').textContent = `${receivers.filter((recv) => ['active', 'online'].includes(String(recv.status).toLowerCase())).length} currently reporting`;
}

function renderAircraftList() {
    const list = document.getElementById('aircraft-list');
    const aircraft = getAircraftList();
    const ui = deriveUiState();

    if (!aircraft.length) {
        const message = ui.hasReceivers
            ? 'Receivers loaded. No aircraft positions available yet. Replay may not have started, live solved output may not be fresh yet, or updates may be disconnected.'
            : ui.isDemo
                ? 'Waiting for replay positions. The replay session is connected, but recorded aircraft positions have not appeared yet.'
                : ui.isLive
                    ? 'Waiting for live positions. Receivers may still be collecting enough fresh timing data for the solver.'
                    : ui.isSimulation
                        ? 'Waiting for sample positions. Synthetic or sample traffic has not appeared yet.'
                        : 'Updates disconnected. Reconnect the session or refresh the source to load positions.';
        list.innerHTML = `<div class="empty-state">${escapeHtml(message)}</div>`;
        return;
    }

    list.innerHTML = aircraft.map((ac, index) => `
        <button class="aircraft-item ${ac.id === pageState.selectedAircraftId ? 'is-selected' : ''}" type="button" data-aircraft-id="${escapeHtml(ac.id)}">
            <div>
                <strong>${escapeHtml(index === 0 ? `${ac.id} · newest` : ac.id)}</strong>
                <span>${escapeHtml(formatDateTime(ac.timestamp))} · ${escapeHtml(formatAltitude(ac.alt))}</span>
                <span>${escapeHtml(`${getConfidenceBucketLabel(ac)} · ${formatUncertainty(ac.uncertainty)}`)}</span>
            </div>
        </button>
    `).join('');

    list.querySelectorAll('[data-aircraft-id]').forEach((button) => {
        button.addEventListener('click', () => focusAircraft(button.dataset.aircraftId, true));
    });
}

function buildConfidenceEvidenceRows(_aircraft, qualityReason, uncertainty, freshness, receiverIds) {
    return `
        <div class="localization-reason-list localization-reason-list-compact">
            <div class="localization-reason-row"><strong>Why this score</strong><span>${escapeHtml(qualityReason)}</span></div>
            <div class="localization-reason-row"><strong>Freshness</strong><span>${escapeHtml(freshness.reason)}</span></div>
            ${receiverIds.length ? `<div class="localization-reason-row"><strong>Receivers</strong><span>${escapeHtml(`${receiverIds.length} receiver IDs are attached to this solved position payload.`)}</span></div>` : ''}
        </div>
    `;
}

function renderSelectedAircraftDetail() {
    const panel = document.getElementById('selection-detail-panel');
    const aircraft = pageState.selectedAircraftId ? pageState.aircraft[pageState.selectedAircraftId] : null;
    if (!aircraft) {
        const ui = deriveUiState();
        panel.innerHTML = `
            <div class="panel-head"><div><h2>No aircraft selected</h2><p>${escapeHtml(ui.hasAircraft ? 'Select an aircraft on the map or from the list.' : ui.mapStatus)}</p></div></div>
        `;
        return;
    }

    const receiverIds = getReceiverIdsForAircraft(aircraft);
    const receiverRows = getVisibleReceiverRows(receiverIds);
    const freshness = describeFreshness(aircraft);
    const uncertainty = describeUncertainty(aircraft);
    const qualityReason = buildQualityReason(aircraft);
    const qualityClass = getQualityToneClass(aircraft.quality?.score);
    const signalTimingSpanLabel = typeof aircraft.correlation?.time_span_s === 'number'
        ? formatTimingSpan(aircraft.correlation.time_span_s)
        : 'n/a';
    const derivedTrack = deriveTrackBehavior(aircraft);

    panel.innerHTML = `
        <div class="localization-detail-stack localization-detail-stack-compact">
            <div class="panel-head">
                <div>
                    <h2>${escapeHtml(aircraft.id)}</h2>
                    <p>Selected aircraft</p>
                </div>
                <span class="status-pill ${qualityClass === 'tone-good' ? 'mode-live' : 'mode-sim'}">${escapeHtml(getConfidenceBucketLabel(aircraft))}</span>
            </div>
            ${buildPipeline(receiverRows, aircraft)}
            <div class="localization-inspector-section">
                <div class="traffic-section-head"><strong>Summary</strong><span>${escapeHtml(formatRelativeTime(aircraft.timestamp))}</span></div>
                <div class="detail-kv localization-detail-body">
                    <div class="detail-kv-row"><strong>Position</strong><span>${escapeHtml(formatCoordinate(aircraft.lat, aircraft.lon))}</span></div>
                    <div class="detail-kv-row"><strong>Altitude</strong><span>${escapeHtml(formatAltitude(aircraft.alt))}</span></div>
                    <div class="detail-kv-row"><strong>Confidence</strong><span>${escapeHtml(formatQualityPercent(aircraft.quality?.score))}</span></div>
                    <div class="detail-kv-row"><strong>Error</strong><span>${escapeHtml(formatUncertainty(aircraft.uncertainty))}</span></div>
                    <div class="detail-kv-row"><strong>Receivers</strong><span>${escapeHtml(String(receiverIds.length || aircraft.numReceivers || 0))}</span></div>
                    <div class="detail-kv-row"><strong>Timing span</strong><span>${escapeHtml(signalTimingSpanLabel)}</span></div>
                    ${derivedTrack.headingLabel ? `<div class="detail-kv-row"><strong>Heading</strong><span>${escapeHtml(derivedTrack.headingLabel)}</span></div>` : ''}
                    <div class="detail-kv-row"><strong>Updated</strong><span>${escapeHtml(formatDateTime(aircraft.timestamp))}</span></div>
                </div>
            </div>
            <div class="localization-inspector-section">
                <div class="traffic-section-head"><strong>Confidence</strong><span>${escapeHtml(freshness.label)}</span></div>
                <div class="localization-confidence-grid localization-confidence-grid-compact">
                    <article class="confidence-card ${qualityClass}">
                        <span>Confidence</span>
                        <strong>${escapeHtml(formatQualityPercent(aircraft.quality?.score))}</strong>
                        <small>${escapeHtml(getConfidenceBucketLabel(aircraft))}</small>
                    </article>
                    <article class="confidence-card">
                        <span>Error</span>
                        <strong>${escapeHtml(formatUncertainty(aircraft.uncertainty))}</strong>
                        <small>${escapeHtml(uncertainty.label)}</small>
                    </article>
                    <article class="confidence-card">
                        <span>Residual</span>
                        <strong>${escapeHtml(formatResidualMeters(aircraft.solver?.residual_m))}</strong>
                        <small>${escapeHtml(typeof aircraft.solver?.iterations === 'number' ? `${aircraft.solver.iterations} iter` : 'Iterations n/a')}</small>
                    </article>
                    <article class="confidence-card">
                        <span>Freshness</span>
                        <strong>${escapeHtml(formatRelativeTime(aircraft.createdAt || aircraft.timestamp))}</strong>
                        <small>${escapeHtml(freshness.label)}</small>
                    </article>
                </div>
                ${buildConfidenceEvidenceRows(aircraft, qualityReason, uncertainty, freshness, receiverIds)}
            </div>
            <div class="localization-inspector-section">
                <div class="traffic-section-head"><strong>Contributing receivers</strong><span>${escapeHtml(String(receiverIds.length || aircraft.numReceivers || 0))}</span></div>
                <div class="relationship-list relationship-list-compact">
                    ${receiverRows.length ? receiverRows.map((receiver) => {
                        const health = deriveReceiverHealth(receiver);
                        return `
                            <div class="relationship-row">
                                <div>
                                    <strong>${escapeHtml(receiver.id)}</strong>
                                    <span>${escapeHtml(formatRelativeTime(receiver.lastSeen))} · ${escapeHtml(`${getReceiverUsageCount(receiver.id)} visible aircraft`)}</span>
                                </div>
                                <span class="receiver-status ${health.className}">${escapeHtml(health.label)}</span>
                            </div>
                        `;
                    }).join('') : '<div class="empty-state">Receiver metadata is not available for this selection yet.</div>'}
                </div>
            </div>
        </div>
    `;
}

function renderSelectedReceiverDetail() {
    const panel = document.getElementById('selection-detail-panel');
    const receiver = pageState.selectedReceiverId ? pageState.receivers[pageState.selectedReceiverId] : null;
    if (!receiver || pageState.selectedAircraftId) {
        renderSelectedAircraftDetail();
        return;
    }

    const relatedAircraft = getAircraftList().filter((aircraft) => getReceiverIdsForAircraft(aircraft).includes(receiver.id));
    const health = deriveReceiverHealth(receiver);

    panel.innerHTML = `
        <div class="localization-detail-stack">
            <div class="panel-head">
                <div>
                    <h2>${escapeHtml(receiver.id)}</h2>
                    <p>Receiver inspector</p>
                </div>
                <span class="status-pill ${health.className === 'live' ? 'mode-live' : 'mode-sim'}">${escapeHtml(receiver.status)}</span>
            </div>
            <div class="localization-explainer">
                <strong>Receiver context</strong>
                <span>Receivers contribute signal timing measurements to MLAT solutions. Select an aircraft to see this receiver as part of the full localization provenance chain.</span>
            </div>
            <div class="detail-kv localization-detail-body">
                <div class="detail-kv-row"><strong>Health</strong><span>${escapeHtml(health.label)}</span></div>
                <div class="detail-kv-row"><strong>Position</strong><span>${escapeHtml(formatCoordinate(receiver.lat, receiver.lon))}</span></div>
                <div class="detail-kv-row"><strong>Altitude</strong><span>${escapeHtml(formatAltitude(receiver.alt))}</span></div>
                <div class="detail-kv-row"><strong>Capabilities</strong><span>${escapeHtml(receiver.capabilities.join(', ') || 'n/a')}</span></div>
                <div class="detail-kv-row"><strong>Last seen</strong><span>${escapeHtml(formatDateTime(receiver.lastSeen))}</span></div>
                <div class="detail-kv-row"><strong>Last updated</strong><span>${escapeHtml(formatDateTime(receiver.updatedAt || receiver.lastSeen))}</span></div>
                <div class="detail-kv-row"><strong>Visible aircraft supported</strong><span>${escapeHtml(String(relatedAircraft.length))}</span></div>
            </div>
            <div class="traffic-section-head"><strong>Aircraft currently referencing this receiver</strong><span>${escapeHtml(String(relatedAircraft.length))} aircraft</span></div>
            <div class="relationship-list">
                ${relatedAircraft.length ? relatedAircraft.slice(0, 8).map((aircraft) => `
                    <div class="relationship-row">
                        <div>
                            <strong>${escapeHtml(aircraft.id)}</strong>
                            <span>${escapeHtml(formatQualityLabel(aircraft.quality))} · estimated error ${escapeHtml(formatUncertainty(aircraft.uncertainty))}</span>
                        </div>
                        <span>${escapeHtml(formatRelativeTime(aircraft.timestamp))}</span>
                    </div>
                `).join('') : '<div class="empty-state">No visible aircraft in the current snapshot reference this receiver yet.</div>'}
            </div>
        </div>
    `;
}

function renderSelectionDetail() {
    if (pageState.selectedAircraftId) {
        renderSelectedAircraftDetail();
    } else {
        renderSelectedReceiverDetail();
    }
}

function renderMetrics() {
    const aircraft = getAircraftList();
    const ui = deriveUiState();
    const avgQualityScore = aircraft.length
        ? Math.round((aircraft.reduce((sum, item) => sum + (item.quality?.score || 0), 0) / aircraft.length) * 100)
        : 0;
    const avgUncertainty = aircraft.length
        ? Math.round(aircraft.reduce((sum, item) => sum + (item.uncertainty || 0), 0) / aircraft.length)
        : 0;

    document.getElementById('aircraft-count').textContent = String(ui.aircraftCount);
    document.getElementById('receiver-count').textContent = String(ui.receiverCount);
    document.getElementById('quality-score').textContent = `${avgQualityScore}%`;
    document.getElementById('avg-uncertainty').textContent = `${avgUncertainty}m`;
    document.getElementById('aircraft-detail').textContent = aircraft.length
        ? `${formatRelativeTime(aircraft[0].timestamp)} latest solved aircraft update`
        : ui.isDemo
            ? 'Waiting for replay positions'
            : ui.isLive
                ? 'Waiting for live positions'
                : ui.isSimulation
                    ? 'Waiting for sample positions'
                    : 'No aircraft available';
    document.getElementById('quality-detail').textContent = aircraft.length
        ? 'Average visible localization confidence'
        : 'No solved aircraft positions yet';
    document.getElementById('uncertainty-detail').textContent = aircraft.length
        ? 'Average visible estimated error'
        : 'No solved aircraft positions yet';
}

function updateSelectionClasses() {
    document.querySelectorAll('.aircraft-item[data-aircraft-id]').forEach((node) => {
        node.classList.toggle('is-selected', node.dataset.aircraftId === pageState.selectedAircraftId);
    });
    document.querySelectorAll('.receiver-item[data-receiver-id]').forEach((node) => {
        node.classList.toggle('is-selected', node.dataset.receiverId === pageState.selectedReceiverId);
    });

    Object.entries(pageState.aircraftMarkers).forEach(([id, marker]) => {
        const node = marker.getElement()?.querySelector('.map-aircraft-marker');
        if (node) node.classList.toggle('is-selected', id === pageState.selectedAircraftId);
    });

    const selectedAircraft = pageState.selectedAircraftId ? pageState.aircraft[pageState.selectedAircraftId] : null;
    const relatedReceiverIds = new Set(selectedAircraft ? getReceiverIdsForAircraft(selectedAircraft) : []);

    Object.entries(pageState.receiverMarkers).forEach(([id, marker]) => {
        const node = marker.getElement()?.querySelector('.map-receiver-marker');
        if (!node) return;
        const receiver = pageState.receivers[id];
        const health = deriveReceiverHealth(receiver);
        node.classList.toggle('is-selected', id === pageState.selectedReceiverId);
        node.classList.toggle('is-related', relatedReceiverIds.has(id));
        node.classList.toggle('is-dimmed', Boolean(pageState.selectedAircraftId) && !relatedReceiverIds.has(id));
        node.classList.toggle('is-active', health.className === 'live');
    });

    Object.entries(pageState.aircraftPaths).forEach(([id, path]) => {
        const isSelected = id === pageState.selectedAircraftId;
        path.setStyle({
            color: isSelected ? '#ffb38b' : '#ff6422',
            weight: isSelected ? 3.1 : 1.8,
            opacity: isSelected ? 0.95 : 0.26,
        });
    });

    Object.entries(pageState.aircraftGlowPaths).forEach(([id, path]) => {
        const isSelected = id === pageState.selectedAircraftId;
        path.setStyle({
            color: isSelected ? 'rgba(255, 136, 88, 0.42)' : 'rgba(255, 100, 34, 0.08)',
            weight: isSelected ? 14 : 6,
            opacity: isSelected ? 1 : 0.5,
        });
    });

    Object.entries(pageState.aircraftRecentSegments).forEach(([id, path]) => {
        const isSelected = id === pageState.selectedAircraftId;
        path.setStyle({
            opacity: isSelected ? 1 : 0.22,
            weight: isSelected ? 5.2 : 2.4,
        });
    });

    Object.entries(pageState.aircraftHeadingStubs).forEach(([id, path]) => {
        const isSelected = id === pageState.selectedAircraftId;
        path.setStyle({ opacity: isSelected ? 1 : 0 });
    });

    Object.entries(pageState.aircraftConfidenceRings).forEach(([id, ring]) => {
        const isSelected = id === pageState.selectedAircraftId;
        ring.setStyle({
            opacity: isSelected ? 0.95 : 0,
            fillOpacity: isSelected ? 0.14 : 0,
        });
    });
}

function renderRelationshipLines() {
    clearRelationshipLines();
    const selected = pageState.selectedAircraftId ? pageState.aircraft[pageState.selectedAircraftId] : null;
    if (!selected) return;

    getReceiverIdsForAircraft(selected).forEach((receiverId) => {
        const receiver = pageState.receivers[receiverId];
        if (!receiver) return;
        const line = L.polyline([
            [receiver.lat, receiver.lon],
            [selected.lat, selected.lon],
        ], getRelationshipLineStyle(true)).addTo(map);
        pageState.relationshipLines.push(line);
    });
}

function renderAll() {
    renderModeSummary();
    renderMetrics();
    renderReceiverList();
    renderAircraftList();
    renderSelectionDetail();
    renderRelationshipLines();
    updateSelectionClasses();
}

function ensureDefaultSelection() {
    const aircraft = getAircraftList();
    if (aircraft.length && !pageState.selectedAircraftId) {
        pageState.selectedAircraftId = aircraft[0].id;
        pageState.selectedReceiverId = null;
        return;
    }
    if (!aircraft.length && pageState.selectedAircraftId) {
        pageState.selectedAircraftId = null;
    }
    if (pageState.selectedReceiverId && !pageState.receivers[pageState.selectedReceiverId]) {
        pageState.selectedReceiverId = null;
    }
}

async function loadReceivers() {
    const data = await fetchJson('/api/receivers');
    Object.values(pageState.receiverMarkers).forEach((marker) => map.removeLayer(marker));
    pageState.receiverMarkers = {};
    pageState.receivers = {};
    data.receivers.forEach(upsertReceiver);
}

async function loadPositions() {
    clearAircraftState();
    const data = await fetchJson('/api/positions/recent?seconds=600&limit=500');
    [...data.positions].sort((a, b) => a.timestamp - b.timestamp).forEach(upsertAircraftFromApi);
}

async function loadHealth() {
    try {
        pageState.health = await fetchJson('/api/health');
    } catch (_error) {
        pageState.health = null;
    }
}

async function loadSystemMode() {
    try {
        const data = await fetchJson('/api/system/mode');
        pageState.systemMode = data;
        pageState.websocketAvailable = Boolean(data.websocket_available);
        return data;
    } catch (_error) {
        pageState.systemMode = null;
        pageState.websocketAvailable = false;
        return null;
    }
}

async function hydrateSelectedAircraft(aircraftId, centerMap = false) {
    const fallback = pageState.aircraft[aircraftId];
    if (!fallback) return;

    try {
        const [latest, track] = await Promise.all([
            fetchJson(`/api/aircraft/${encodeURIComponent(aircraftId)}/latest`),
            fetchJson(`/api/aircraft/${encodeURIComponent(aircraftId)}/track?limit=100`),
        ]);
        upsertAircraftFromApi(latest);
        applyTrackToAircraft(aircraftId, track);
    } catch (_error) {
        // Keep snapshot state when detail fetch fails.
    }

    const aircraft = pageState.aircraft[aircraftId];
    if (!aircraft) return;
    if (centerMap) {
        map.setView([aircraft.lat, aircraft.lon], 10);
        if (pageState.aircraftMarkers[aircraftId]) {
            pageState.aircraftMarkers[aircraftId].openPopup();
        }
    }
    renderAll();
}

function focusAircraft(aircraftId, centerMap = true) {
    if (!pageState.aircraft[aircraftId]) return;
    pageState.selectedAircraftId = aircraftId;
    pageState.selectedReceiverId = null;
    renderAll();
    hydrateSelectedAircraft(aircraftId, centerMap).catch(() => null);
}

function focusReceiver(receiverId, centerMap = true) {
    const receiver = pageState.receivers[receiverId];
    if (!receiver) return;
    pageState.selectedReceiverId = receiverId;
    pageState.selectedAircraftId = null;
    if (centerMap) map.setView([receiver.lat, receiver.lon], 9);
    if (pageState.receiverMarkers[receiverId]) pageState.receiverMarkers[receiverId].openPopup();
    renderAll();
}

async function refreshSnapshot() {
    setConnectionStatus('Refreshing operational map state…', 'pending');
    try {
        const [modeData] = await Promise.all([
            loadSystemMode(),
            loadHealth(),
            loadReceivers(),
            loadPositions(),
        ]);
        ensureDefaultSelection();
        if (modeData?.demo_mode) {
            applyScenarioMap(modeData);
        } else {
            await fitBoundsFromApi();
        }
        renderAll();
        setConnectionStatus(pageState.websocketAvailable ? 'Refresh complete. Stream available.' : 'Refresh complete. Refresh-only mode.', pageState.websocketAvailable ? 'live' : 'neutral');
        if (pageState.selectedAircraftId) {
            hydrateSelectedAircraft(pageState.selectedAircraftId, false).catch(() => null);
        }
    } catch (error) {
        setConnectionStatus(`Refresh failed: ${error.message}`, 'error');
        renderAll();
    }
}

function disconnectLive() {
    if (pageState.socket) {
        pageState.socket.disconnect();
        pageState.socket = null;
    }
    if (pageState.refreshTimer) {
        clearInterval(pageState.refreshTimer);
        pageState.refreshTimer = null;
    }
    setFeedPill('Updates disconnected');
    setConnectionStatus('Disconnected', 'neutral');
    renderAll();
}

async function connectLive() {
    disconnectLive();
    setConnectionStatus('Connecting to operational source…', 'pending');
    setFeedPill('Feed pending');

    try {
        await refreshSnapshot();
    } catch (_error) {
        return;
    }

    if (pageState.websocketAvailable && typeof io === 'function') {
        pageState.socket = io(getApiBase(), { transports: ['websocket', 'polling'] });

        pageState.socket.on('connect', () => {
            const ui = deriveUiState();
            setConnectionStatus(
                ui.isDemo
                    ? 'Replay stream connected'
                    : ui.isLive
                        ? 'Live stream connected'
                        : ui.isSimulation
                            ? 'Sample stream connected'
                            : 'Stream connected',
                'live',
            );
            renderAll();
        });

        pageState.socket.on('disconnect', () => {
            setConnectionStatus('Disconnected', 'neutral');
            setFeedPill('Updates disconnected');
            renderAll();
        });

        pageState.socket.on('connect_error', (error) => {
            setConnectionStatus(`Stream unavailable: ${error.message}`, 'error');
            setFeedPill('Refresh-only mode');
            renderAll();
        });

        pageState.socket.on('position_update', (payload) => {
            if (!payload?.aircraft_id || !payload?.position) return;
            const record = payload.position.position
                ? payload.position
                : {
                    aircraft_id: payload.aircraft_id,
                    timestamp: payload.position.timestamp,
                    uncertainty: payload.position.uncertainty,
                    num_receivers: payload.position.num_receivers,
                    quality: payload.position.quality,
                    solver: payload.position.solver,
                    correlation: payload.position.correlation,
                    created_at: payload.position.created_at,
                    position: {
                        latitude: payload.position.latitude,
                        longitude: payload.position.longitude,
                        altitude: payload.position.altitude,
                    },
                };
            upsertAircraftFromApi({ ...record, aircraft_id: payload.aircraft_id });
            ensureDefaultSelection();
            renderAll();
        });
    }

    pageState.refreshTimer = setInterval(() => {
        refreshSnapshot().catch(() => null);
    }, 15000);
}

function startAgeTicker() {
    if (pageState.ageTimer) return;
    pageState.ageTimer = window.setInterval(() => {
        renderAll();
    }, 5000);
}

async function boot() {
    document.getElementById('api-url').value = defaultApiUrl();
    document.getElementById('connect-btn').addEventListener('click', () => connectLive().catch(() => null));
    document.getElementById('refresh-btn').addEventListener('click', () => refreshSnapshot().catch(() => null));
    document.getElementById('disconnect-btn').addEventListener('click', disconnectLive);
    renderAll();
    startAgeTicker();
    const modeData = await loadSystemMode();
    renderAll();
    if (modeData?.demo_mode && modeData?.demo_auto_connect) {
        connectLive().catch(() => null);
        return;
    }
    connectLive().catch(() => null);
}

boot().catch(() => null);

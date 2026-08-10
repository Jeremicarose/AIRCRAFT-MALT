'use client';

import * as maplibregl from 'maplibre-gl';
import type { GeoJSONSource, LayerSpecification, Map as MapLibreMap, MapMouseEvent, Marker, StyleSpecification } from 'maplibre-gl';
import { useEffect, useMemo, useRef, useState } from 'react';
import type { Position, Receiver } from '@/lib/types';
import { formatCoordinate, percent, positionCoordinates } from '@/lib/format';

type Coordinates = [number, number];

interface AirspaceMapProps {
  aircraft: Position[];
  receivers: Receiver[];
  selectedAircraftId?: string | null;
  selectedReceiverId?: string | null;
  onSelectAircraft?: (id: string) => void;
  onSelectReceiver?: (id: string) => void;
  showReceiverLinks?: boolean;
  showUncertainty?: boolean;
  track?: Position[];
  coveragePositions?: Position[];
  fitRequest?: number;
  className?: string;
}

const baseStyle: StyleSpecification = {
  version: 8,
  sources: {
    carto: {
      type: 'raster',
      tiles: ['https://a.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}@2x.png', 'https://b.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}@2x.png'],
      tileSize: 256,
      attribution: '© OpenStreetMap © CARTO',
    },
  },
  layers: [
    { id: 'base', type: 'background', paint: { 'background-color': '#090c10' } },
    { id: 'carto', type: 'raster', source: 'carto', paint: { 'raster-opacity': 0.72, 'raster-saturation': -0.72, 'raster-contrast': 0.14 } },
  ],
};

function validReceiverCoordinates(receiver: Receiver): Coordinates | null {
  const latitude = Number(receiver.latitude);
  const longitude = Number(receiver.longitude);
  return Number.isFinite(latitude) && Number.isFinite(longitude) ? [longitude, latitude] : null;
}

function circlePolygon(center: Coordinates, radiusMeters: number, steps = 64): Coordinates[] {
  const [longitude, latitude] = center;
  const latRadians = latitude * Math.PI / 180;
  return Array.from({ length: steps + 1 }, (_, index) => {
    const angle = index / steps * Math.PI * 2;
    const latitudeOffset = radiusMeters / 111_320 * Math.sin(angle);
    const longitudeOffset = radiusMeters / (111_320 * Math.max(0.1, Math.cos(latRadians))) * Math.cos(angle);
    return [longitude + longitudeOffset, latitude + latitudeOffset];
  });
}

function convexHull(points: Coordinates[]): Coordinates[] {
  if (points.length < 3) return [];
  const sorted = [...points].sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const cross = (origin: Coordinates, a: Coordinates, b: Coordinates) => (a[0] - origin[0]) * (b[1] - origin[1]) - (a[1] - origin[1]) * (b[0] - origin[0]);
  const lower: Coordinates[] = [];
  sorted.forEach((point) => { while (lower.length >= 2 && cross(lower.at(-2)!, lower.at(-1)!, point) <= 0) lower.pop(); lower.push(point); });
  const upper: Coordinates[] = [];
  [...sorted].reverse().forEach((point) => { while (upper.length >= 2 && cross(upper.at(-2)!, upper.at(-1)!, point) <= 0) upper.pop(); upper.push(point); });
  lower.pop();
  upper.pop();
  const hull = [...lower, ...upper];
  return hull.length ? [...hull, hull[0]] : [];
}

function popupContent(title: string, lines: string[]): HTMLElement {
  const wrapper = document.createElement('div');
  const heading = document.createElement('strong');
  heading.className = 'block text-xs font-semibold text-ink';
  heading.textContent = title;
  wrapper.appendChild(heading);
  lines.forEach((line) => {
    const row = document.createElement('p');
    row.className = 'mt-1 text-[11px] text-ink-quiet';
    row.textContent = line;
    wrapper.appendChild(row);
  });
  return wrapper;
}

function upsertGeoJson(map: MapLibreMap, id: string, data: GeoJSON.FeatureCollection, layer: LayerSpecification) {
  const source = map.getSource(id) as GeoJSONSource | undefined;
  if (source) {
    source.setData(data);
    return;
  }
  map.addSource(id, { type: 'geojson', data });
  map.addLayer(layer);
}

export default function AirspaceMap({ aircraft, receivers, selectedAircraftId, selectedReceiverId, onSelectAircraft, onSelectReceiver, showReceiverLinks = true, showUncertainty = true, track = [], coveragePositions = [], fitRequest = 0, className }: AirspaceMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const markersRef = useRef<Marker[]>([]);
  const [ready, setReady] = useState(false);

  const selectedAircraft = useMemo(() => aircraft.find((item) => item.aircraft_id === selectedAircraftId) ?? aircraft[0] ?? null, [aircraft, selectedAircraftId]);
  const selectedReceiver = useMemo(() => receivers.find((item) => item.receiver_id === selectedReceiverId) ?? null, [receivers, selectedReceiverId]);
  const contributingReceivers = useMemo(() => {
    const ids = selectedAircraft?.correlation?.receiver_ids ?? [];
    return receivers.filter((receiver) => ids.includes(receiver.receiver_id));
  }, [receivers, selectedAircraft]);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const firstPosition = aircraft.map(positionCoordinates).find(Boolean) as Coordinates | undefined;
    const firstReceiver = receivers.map(validReceiverCoordinates).find(Boolean) as Coordinates | undefined;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: baseStyle,
      center: firstPosition ?? firstReceiver ?? [-74.35, 40.82],
      zoom: firstPosition || firstReceiver ? 7 : 4,
      minZoom: 2,
      maxZoom: 16,
      attributionControl: false,
      cooperativeGestures: true,
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: true, visualizePitch: true }), 'top-right');
    map.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-right');
    map.on('load', () => setReady(true));
    map.on('contextmenu', (event: MapMouseEvent) => {
      new maplibregl.Popup({ closeButton: false, offset: 10 })
        .setLngLat(event.lngLat)
        .setDOMContent(popupContent('Map location', [formatCoordinate(event.lngLat.lat, event.lngLat.lng), 'Right-click inspection point']))
        .addTo(map);
    });
    mapRef.current = map;
    return () => {
      markersRef.current.forEach((marker) => marker.remove());
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    markersRef.current.forEach((marker) => marker.remove());
    markersRef.current = [];

    receivers.forEach((receiver) => {
      const coordinates = validReceiverCoordinates(receiver);
      if (!coordinates) return;
      const element = document.createElement('button');
      element.type = 'button';
      element.className = `receiver-map-marker${selectedReceiverId === receiver.receiver_id ? ' is-selected' : ''}`;
      element.setAttribute('aria-label', `Select receiver ${receiver.receiver_id}`);
      element.addEventListener('click', () => onSelectReceiver?.(receiver.receiver_id));
      const marker = new maplibregl.Marker({ element, anchor: 'center' }).setLngLat(coordinates).setPopup(new maplibregl.Popup({ offset: 12, closeButton: false }).setDOMContent(popupContent(receiver.receiver_id, [formatCoordinate(receiver.latitude, receiver.longitude), receiver.status || 'Status unknown']))).addTo(map);
      markersRef.current.push(marker);
    });

    aircraft.forEach((item) => {
      const coordinates = positionCoordinates(item);
      if (!coordinates) return;
      const element = document.createElement('button');
      element.type = 'button';
      element.className = `aircraft-map-marker${selectedAircraft?.aircraft_id === item.aircraft_id ? ' is-selected' : ''}`;
      element.setAttribute('aria-label', `Select aircraft ${item.aircraft_id}`);
      element.addEventListener('click', () => onSelectAircraft?.(item.aircraft_id));
      const marker = new maplibregl.Marker({ element, anchor: 'center' }).setLngLat(coordinates).setPopup(new maplibregl.Popup({ offset: 12, closeButton: false }).setDOMContent(popupContent(item.aircraft_id, [`${percent(item.quality?.score, 0)} confidence`, `${item.correlation?.receiver_count ?? item.num_receivers ?? 0} receivers`]))).addTo(map);
      markersRef.current.push(marker);
    });
  }, [aircraft, onSelectAircraft, onSelectReceiver, ready, receivers, selectedAircraft, selectedReceiverId]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    const selectedCoordinates = positionCoordinates(selectedAircraft);
    const lineFeatures: GeoJSON.Feature<GeoJSON.LineString>[] = [];
    if (showReceiverLinks && selectedCoordinates) {
      contributingReceivers.forEach((receiver) => {
        const coordinates = validReceiverCoordinates(receiver);
        if (coordinates) lineFeatures.push({ type: 'Feature', properties: {}, geometry: { type: 'LineString', coordinates: [selectedCoordinates, coordinates] } });
      });
    }
    upsertGeoJson(map, 'receiver-links', { type: 'FeatureCollection', features: lineFeatures }, { id: 'receiver-links', type: 'line', source: 'receiver-links', paint: { 'line-color': '#5b9cff', 'line-width': 1.25, 'line-opacity': 0.52, 'line-dasharray': [2, 2] } });

    const uncertainty = Number(selectedAircraft?.quality?.uncertainty_m ?? selectedAircraft?.uncertainty ?? 0);
    const uncertaintyFeatures: GeoJSON.Feature<GeoJSON.Polygon>[] = showUncertainty && selectedCoordinates && uncertainty > 0 ? [{ type: 'Feature', properties: {}, geometry: { type: 'Polygon', coordinates: [circlePolygon(selectedCoordinates, uncertainty)] } }] : [];
    upsertGeoJson(map, 'uncertainty', { type: 'FeatureCollection', features: uncertaintyFeatures }, { id: 'uncertainty-fill', type: 'fill', source: 'uncertainty', paint: { 'fill-color': '#5b9cff', 'fill-opacity': 0.12, 'fill-outline-color': '#78adff' } });

    const trackCoordinates = track.map(positionCoordinates).filter(Boolean) as Coordinates[];
    const trackFeatures: GeoJSON.Feature<GeoJSON.LineString>[] = trackCoordinates.length > 1 ? [{ type: 'Feature', properties: {}, geometry: { type: 'LineString', coordinates: trackCoordinates } }] : [];
    upsertGeoJson(map, 'aircraft-track', { type: 'FeatureCollection', features: trackFeatures }, { id: 'aircraft-track', type: 'line', source: 'aircraft-track', paint: { 'line-color': '#dce9ff', 'line-width': 2, 'line-opacity': 0.64 } });

    const hull = convexHull(coveragePositions.map(positionCoordinates).filter(Boolean) as Coordinates[]);
    const coverageFeatures: GeoJSON.Feature<GeoJSON.Polygon>[] = hull.length ? [{ type: 'Feature', properties: {}, geometry: { type: 'Polygon', coordinates: [hull] } }] : [];
    upsertGeoJson(map, 'observed-coverage', { type: 'FeatureCollection', features: coverageFeatures }, { id: 'observed-coverage-fill', type: 'fill', source: 'observed-coverage', paint: { 'fill-color': '#68d5e8', 'fill-opacity': 0.08, 'fill-outline-color': '#68d5e8' } });
  }, [contributingReceivers, coveragePositions, ready, selectedAircraft, showReceiverLinks, showUncertainty, track]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    const points: Coordinates[] = [];
    const selectedCoordinates = positionCoordinates(selectedAircraft);
    const receiverCoordinates = selectedReceiver ? validReceiverCoordinates(selectedReceiver) : null;
    if (selectedCoordinates) points.push(selectedCoordinates);
    if (receiverCoordinates) points.push(receiverCoordinates);
    contributingReceivers.forEach((receiver) => {
      const coordinates = validReceiverCoordinates(receiver);
      if (coordinates) points.push(coordinates);
    });
    if (!points.length) {
      aircraft.map(positionCoordinates).filter(Boolean).forEach((point) => points.push(point as Coordinates));
      receivers.map(validReceiverCoordinates).filter(Boolean).forEach((point) => points.push(point as Coordinates));
    }
    if (points.length === 1) map.easeTo({ center: points[0], zoom: Math.max(map.getZoom(), 9), duration: 180 });
    if (points.length > 1) {
      const bounds = points.reduce((value, point) => value.extend(point), new maplibregl.LngLatBounds(points[0], points[0]));
      map.fitBounds(bounds, { padding: 72, maxZoom: 10, duration: 180 });
    }
  }, [aircraft, contributingReceivers, fitRequest, ready, receivers, selectedAircraft, selectedReceiver]);

  return <div ref={containerRef} className={className ?? 'h-full min-h-[420px] w-full'} role="region" aria-label="Interactive aircraft and receiver map" />;
}

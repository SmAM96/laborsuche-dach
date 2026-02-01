import React, { useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

function FlyTo({ center }) {
  const map = useMap();

  React.useEffect(() => {
    if (!center) return;
    map.flyTo([center.lat, center.lng], center.zoom, { duration: 0.6 });
  }, [center, map]);

  return null;
}

function markerIcon(category) {
  const color = category === 'dexa' ? '#2563eb' : '#16a34a'; // blue vs green

  return L.divIcon({
    className: '',
    html: `<div style="
      width: 14px; height: 14px;
      border-radius: 999px;
      background: ${color};
      border: 2px solid white;
      box-shadow: 0 6px 16px rgba(0,0,0,0.18);
    "></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
    popupAnchor: [0, -8],
  });
}

function normalizeLatLng(x) {
  const lat = Number(x.lat);
  const lng = Number(x.lng);
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;
  return { lat, lng };
}

export default function MapView({ items, center, selectedId, onSelect }) {
  const markers = useMemo(() => {
    return items
      .map((x) => {
        const p = normalizeLatLng(x);
        if (!p) return null;
        return { ...x, _p: p };
      })
      .filter(Boolean);
  }, [items]);

  return (
    <MapContainer
      className="map"
      center={[center.lat, center.lng]}
      zoom={center.zoom}
      scrollWheelZoom
    >
      <FlyTo center={center} />

      <TileLayer
        attribution="&copy; OpenStreetMap contributors"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {markers.map((x) => (
        <Marker
          key={x._id}
          position={[x._p.lat, x._p.lng]}
          icon={markerIcon(x.category)}
          eventHandlers={{
            click: () => onSelect(x._id),
          }}
        >
          <Popup>
            <div className="popup">
              <div className="popupTitle">{x.name ?? 'Unbekannt'}</div>

              <div className="popupMeta">
                <span
                  className={x.category === 'dexa' ? 'tag blue' : 'tag green'}
                >
                  {x.category === 'dexa' ? 'DEXA' : 'Blutlabor'}
                </span>
                <span className="tag">{x.city}</span>
                {x.google_category ? (
                  <span className="tag">{x.google_category}</span>
                ) : null}
              </div>

              {x.domain ? (
                <div className="popupLine">
                  <span className="muted">Domain:</span> {x.domain}
                </div>
              ) : null}

              {x.address ? (
                <div className="popupLine">
                  <span className="muted">Adresse:</span> {x.address}
                </div>
              ) : null}

              {x.phone ? (
                <div className="popupLine">
                  <span className="muted">Telefon:</span>{' '}
                  <a className="popupLink" href={`tel:${x.phone}`}>
                    {x.phone}
                  </a>
                </div>
              ) : null}

              {x.website ? (
                <a
                  className="primaryLink"
                  href={x.website}
                  target="_blank"
                  rel="noreferrer"
                >
                  Website öffnen
                </a>
              ) : null}
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}

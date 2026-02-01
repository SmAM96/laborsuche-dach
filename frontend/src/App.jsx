import React, { useEffect, useMemo, useState } from 'react';
import { fetchDatasets, fetchProviders } from './api/client';
import TopBar from './components/TopBar';
import MapView from './components/MapView';
import Sidebar from './components/Sidebar';

function computeCenter(items) {
  const points = items
    .map((x) => ({ lat: Number(x.lat), lng: Number(x.lng) }))
    .filter((p) => Number.isFinite(p.lat) && Number.isFinite(p.lng));

  if (points.length === 0) return { lat: 47.5, lng: 9.5, zoom: 6 };

  const lat = points.reduce((s, p) => s + p.lat, 0) / points.length;
  const lng = points.reduce((s, p) => s + p.lng, 0) / points.length;

  return { lat, lng, zoom: 11 };
}

function makeStableId(x) {
  const a = x.domain ?? '';
  const b = x.address ?? '';
  const c = x.name ?? '';
  const d = x.city ?? '';
  const e = x.category ?? '';
  return `${e}|${d}|${a}|${b}|${c}`;
}

export default function App() {
  const [datasets, setDatasets] = useState([]);
  const [city, setCity] = useState('Berlin');
  const [category, setCategory] = useState('all'); // all | dexa | blood

  const [items, setItems] = useState([]);
  const [selectedId, setSelectedId] = useState(null);

  const selected = useMemo(() => {
    if (!selectedId) return null;
    return items.find((x) => String(x._id) === String(selectedId)) ?? null;
  }, [items, selectedId]);

  const center = useMemo(() => computeCenter(items), [items]);

  useEffect(() => {
    (async () => {
      const ds = await fetchDatasets();
      setDatasets(ds);

      const cities = [...new Set(ds.map((d) => d.city))];
      if (!cities.includes('Berlin') && cities.length > 0) setCity(cities[0]);
    })().catch(console.error);
  }, []);

  useEffect(() => {
    setSelectedId(null);
    (async () => {
      const data = await fetchProviders({ city, category });
      const normalized = data.map((x) => ({
        ...x,
        _id: makeStableId(x),
      }));
      setItems(normalized);
    })().catch(console.error);
  }, [city, category]);

  return (
    <div className="app">
      <TopBar
        datasets={datasets}
        city={city}
        setCity={setCity}
        category={category}
        setCategory={setCategory}
        count={items.length}
      />

      <div className="content">
        <div className="mapWrap">
          <MapView
            items={items}
            center={center}
            selectedId={selectedId}
            onSelect={(id) => setSelectedId(id)}
          />
        </div>

        <Sidebar
          items={items}
          selected={selected}
          selectedId={selectedId}
          onSelect={(id) => setSelectedId(id)}
        />
      </div>
    </div>
  );
}

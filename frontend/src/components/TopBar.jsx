import React, { useMemo } from 'react';

export default function TopBar({
  datasets,
  city,
  setCity,
  category,
  setCategory,
  count,
}) {
  const cities = useMemo(() => {
    const s = new Set(datasets.map((d) => d.city));
    return Array.from(s).sort((a, b) => a.localeCompare(b));
  }, [datasets]);

  return (
    <div className="topbar">
      <div className="brand">
        <div className="title">Laborsuche DACH</div>
        <div className="subtitle">
          DEXA Body Composition + Blutlabor (Selbstzahler)
        </div>
      </div>

      <div className="controls">
        <label className="field">
          <span>Stadt</span>
          <select value={city} onChange={(e) => setCity(e.target.value)}>
            {cities.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>

        <div className="seg">
          <button
            className={category === 'all' ? 'active' : ''}
            onClick={() => setCategory('all')}
          >
            Alle
          </button>
          <button
            className={category === 'dexa' ? 'active' : ''}
            onClick={() => setCategory('dexa')}
          >
            DEXA
          </button>
          <button
            className={category === 'blood' ? 'active' : ''}
            onClick={() => setCategory('blood')}
          >
            Blutlabor
          </button>
        </div>

        <div className="kpi">
          <span className="pill">{count} Treffer</span>
        </div>
      </div>
    </div>
  );
}

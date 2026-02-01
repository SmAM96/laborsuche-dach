import React from 'react';

function prettyCategory(c) {
  return c === 'dexa' ? 'DEXA Body Composition' : 'Blutlabor (Selbstzahler)';
}

export default function Sidebar({ items, selected, selectedId, onSelect }) {
  return (
    <div className="sidebar">
      <div className="sidebarHeader">Ergebnisse</div>

      <div className="list">
        {items.map((x) => {
          const active = String(selectedId) === String(x._id);
          return (
            <button
              key={x._id}
              className={`row ${active ? 'active' : ''}`}
              onClick={() => onSelect(x._id)}
            >
              <div className="rowTop">
                <div className="rowTitle">{x.name ?? 'Unbekannt'}</div>
                <span
                  className={x.category === 'dexa' ? 'chip blue' : 'chip green'}
                >
                  {x.category === 'dexa' ? 'DEXA' : 'Blut'}
                </span>
              </div>
              <div className="rowSub">{x.address ?? x.domain ?? x.city}</div>
            </button>
          );
        })}
      </div>

      <div className="details">
        {!selected ? (
          <div className="empty">Marker oder Eintrag auswählen</div>
        ) : (
          <>
            <div className="detailsTitle">{selected.name ?? 'Unbekannt'}</div>

            <div className="detailsMeta">
              {prettyCategory(selected.category)}
              {selected.google_category ? ` • ${selected.google_category}` : ''}
            </div>

            {selected.domain ? (
              <div className="detailsLine">
                <div className="label">Domain</div>
                <div className="value">{selected.domain}</div>
              </div>
            ) : null}

            {selected.address ? (
              <div className="detailsLine">
                <div className="label">Adresse</div>
                <div className="value">{selected.address}</div>
              </div>
            ) : null}

            <div className="detailsGrid">
              {selected.phone ? (
                <div>
                  <div className="label">Telefon</div>
                  <div className="value">
                    <a className="popupLink" href={`tel:${selected.phone}`}>
                      {selected.phone}
                    </a>
                  </div>
                </div>
              ) : null}

              {selected.city ? (
                <div>
                  <div className="label">Stadt</div>
                  <div className="value">{selected.city}</div>
                </div>
              ) : null}
            </div>

            {selected.website ? (
              <a
                className="primaryLink"
                href={selected.website}
                target="_blank"
                rel="noreferrer"
              >
                Website öffnen
              </a>
            ) : null}
          </>
        )}
      </div>
    </div>
  );
}

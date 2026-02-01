# Laborsuche DACH

Interaktive, datengetriebene Webanwendung zur Identifikation von:

- **DEXA Body Composition Anbietern** (nicht nur Knochendichte)
- **Blutlaboren für Selbstzahler ohne Überweisung**

Der Fokus liegt auf **Datenqualität, klarer Entscheidungslogik und Auditierbarkeit**, nicht auf maximaler Trefferanzahl.

---

# Inhaltsverzeichnis

- [Executive Summary](#executive-summary)
- [Schnellstart mit Docker](#schnellstart-mit-docker)
- [Systemarchitektur](#systemarchitektur)
- [Designentscheidungen und Begründung](#designentscheidungen-und-begründung)
- [Scraper – Pipeline im Detail](#scraper--pipeline-im-detail)
- [Validierungslogik](#validierungslogik)
- [Output-Struktur](#output-struktur)
- [Backend](#backend)
- [Frontend](#frontend)
- [Konfiguration](#konfiguration)
- [Reviewer Guide](#reviewer-guide)
- [Erweiterungsmöglichkeiten](#erweiterungsmöglichkeiten)

---

# Executive Summary

Dieses Projekt löst ein reales Problem:

Es existiert keine zentrale, verlässliche Übersicht für:

1. **DXA/DEXA Body Composition**
   Messung von Körperfett, Muskelmasse, Lean Mass etc.
   Reine Osteoporose-Diagnostik gilt nicht als Body Composition.

2. **Blutuntersuchungen für Selbstzahler ohne ärztliche Anforderung**

Die Herausforderung liegt nicht im Finden von “DEXA” oder “Labor”,
sondern in der **präzisen Abgrenzung**.

Deshalb wurde eine evidenzbasierte Datenpipeline entwickelt,
die jede Entscheidung nachvollziehbar macht.

---

# Schnellstart mit Docker

## 1. .env anlegen (für API-Keys des Scrapers)

```bash
cp .env.example .env
```

Dann in `.env` eintragen:

```env
APIFY_TOKEN=apify_api_your_token_here
OPENAI_API_KEY=sk_your_key_here
```

Wird benötigt für:

- Apify (Places, Search, Scraping)
- OpenAI (LLM Validierung)

## 2. Backend und Frontend starten

```bash
docker compose up --build
```

Services:

- Backend → http://localhost:8000/docs
- Frontend → http://localhost:3000

Das `data/` Verzeichnis ist als Volume gemountet.
Neue Scraper-Ergebnisse werden automatisch verfügbar.

## 3. Scraper separat ausführen

```bash
docker compose --profile tools run --rm scraper
```

# Systemarchitektur

Modularer Aufbau:

- **Scraper**
  Discovery → Sniper Search → Text-Extraktion → LLM-Validierung

- **Backend (FastAPI)**
  Liest validierte JSON-Dateien und stellt API bereit

- **Frontend (React + Leaflet)**
  Visualisiert Anbieter auf einer interaktiven Karte

High-Level Flow:

1. Stadt + Ländercode
2. Google Places Discovery
3. Domain-Deduplizierung
4. Sniper Search (`site:domain`)
5. Selektive Deep-Link-Extraktion
6. LLM-Validierung mit Evidence Quote
7. Speicherung in `data/`
8. Backend API
9. Frontend Rendering

---

# Designentscheidungen und Begründung

Dieses Projekt ist kein klassischer Webcrawler,
sondern eine kontrollierte, kostenoptimierte Datenpipeline.

## 1. Google Places über Apify statt direkte Google API

- Kein OAuth-Handling
- Keine eigene Quota-Verwaltung
- Strukturierte Datenausgabe
- Schnelle Integration
- Skalierbarkeit ohne eigene Infrastruktur

## 2. Kein Full-Crawl – Sniper-Ansatz

Statt komplette Websites zu crawlen:

```
site:domain (DEXA OR Muskelmasse OR Körperfett ...)
```

Google übernimmt die Relevanzbewertung.

Vorteile:

- Massive Zeitersparnis
- Geringere Token-Kosten
- Höhere Präzision
- Weniger Noise

## 3. Cheerio über Apify statt eigener BeautifulSoup-Infrastruktur

- Parallele Verarbeitung
- Kein eigener Proxy-Stack
- Keine Retry-Logik notwendig
- Serverseitige DOM-Extraktion
- Schnellere Ausführung

Noise-Elemente werden entfernt:
script, style, nav, footer, header, iframe, Cookie-Banner.

## 4. LLM-Validierung mit gpt-4-turbo

Tests zeigten:

- Kleinere Modelle produzierten vereinzelte False Negatives.
- gpt-4-turbo zeigte konsistente Entscheidungsqualität.

Prompt-Härtung:

- Strikte YES / NO / QUESTIONABLE Logik
- Verbot impliziter Annahmen
- Evidence Quote verpflichtend
- Klare Abgrenzung Body Composition vs. Knochendichte
- Klare Abgrenzung Selbstzahler vs. Zuweiser-Service

## 5. VALID JSON + REJECTED CSV

- VALID → API-ready
- REJECTED → menschlich prüfbar

Ermöglicht iterative Qualitätsverbesserung.

## 6. Erweiterbarkeit

Neue Städte:

1. Scraper starten
2. Stadt + Ländercode eingeben
3. Neue Dateien erscheinen in `data/`

Backend erkennt sie automatisch.
Frontend zeigt sie an.

Keine DB-Migration.
Kein Redeploy.

## 7. Regulatorischer Kontext DEXA in Deutschland

DEXA Body Composition ist in Deutschland regulatorisch sensibel
und deutlich seltener verfügbar als in anderen Ländern.

Hintergrund:
https://www.sport-longevity.de/artikel/dexa-koerperfettmessung-muenchen-und-deutschland/

Dies erklärt die begrenzte Anbieteranzahl
und unterstreicht die Notwendigkeit präziser Validierung.

---

# Scraper – Pipeline im Detail

1. Discovery über Google Places
2. Domain-Deduplizierung
3. Sniper Search über Google Index
4. Cheerio Text-Extraktion
5. LLM-Validierung
6. Speicherung als JSON + CSV

---

# Validierungslogik

## DEXA

YES nur wenn:

- DXA/DEXA explizit mit Körperfett oder Muskelmasse verknüpft

NO wenn:

- Nur Knochendichte / Osteoporose Kontext

NO wenn:

- MRT, BIA, InBody oder andere Verfahren

## Blutlabor

YES nur wenn:

- Explizit “ohne Überweisung” oder äquivalente Aussage

NO wenn:

- Überweisungspflicht genannt

QUESTIONABLE:

- Keine klare Evidenz

Evidence Quote ist Pflichtbestandteil jeder positiven Entscheidung.

---

# Output Struktur

Pro Stadt:

- `<City>_DEXA_VALID.json`
- `<City>_DEXA_REJECTED.csv`
- `<City>_BLOOD_VALID.json`
- `<City>_BLOOD_REJECTED.csv`

VALID JSON enthält:

- name
- website
- google_category
- domain
- address
- phone
- lat
- lng
- status
- evidence_quote

---

# Backend

- Lädt `*_VALID.json`
- Annotiert city + category
- API Endpunkte:
  - GET /api/datasets
  - GET /api/providers

Optional filterbar nach city, category, status.

---

# Frontend

- React + Leaflet
- City Dropdown
- Kategorie Filter
- KPI Anzeige
- Marker mit Popup
- Sidebar mit Detailansicht

API Base:

- `VITE_API_BASE`
- Fallback: http://localhost:8000

---

# Konfiguration

## .env für Scraper

```
APIFY_TOKEN=...
OPENAI_API_KEY=...
```

## Limits

- MAX_CRAWLED_PLACES_PER_SEARCH = 30
- MAX_PAGES_PER_QUERY = 1

Erhöhbar bei Bedarf.

---

# Reviewer Guide

1. VALID JSON prüfen (status + evidence_quote)
2. REJECTED CSV stichprobenartig kontrollieren
3. Docker Compose starten
4. Filter testen
5. Neue Stadt scrapen und UI aktualisieren

---

# Erweiterungsmöglichkeiten

- PDF Parsing
- URL Caching
- Regression Test Set
- Marker Clustering
- Optional DB Layer bei Skalierung

---

# Fazit

Dieses Projekt ist eine kontrollierte,
evidenzbasierte Datenpipeline mit klarer Entscheidungslogik.

Nicht Keyword-Scraping,
sondern reproduzierbare Qualitätsselektion.

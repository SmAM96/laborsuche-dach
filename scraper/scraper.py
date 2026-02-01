from apify_client import ApifyClient
from tenacity import retry, stop_after_attempt, wait_exponential
from .config import APIFY_TOKEN, MAX_CRAWLED_PLACES_PER_SEARCH, MAX_PAGES_PER_QUERY
from .utils import get_domain

apify = ApifyClient(APIFY_TOKEN)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def find_places_discovery(city, queries):
    """
    Schritt 1: Breite Suche via Google Places.
    Holt Basisdaten (Name, URL, Koordinaten) für alle potenziellen Kandidaten.
    """
    print(f"\n🌍 DISCOVERY: Suche in '{city}' nach: {', '.join(queries)}")

    run_input = {
        "searchStringsArray": queries,
        "locationQuery": city,
        "maxCrawledPlacesPerSearch": MAX_CRAWLED_PLACES_PER_SEARCH,
        "language": "de",
    }

    # Wir nutzen den compass/crawler-google-places Actor, der ist zuverlässig
    run = apify.actor("compass/crawler-google-places").call(run_input=run_input)
    dataset = apify.dataset(run["defaultDatasetId"]).list_items().items

    candidates = []
    seen_domains = set()

    print(f"\n   📋 Gefundene Kandidaten (Raw):")
    for item in dataset:
        url = (item.get("website") or "").strip()
        name = item.get("title", "Unbekannt")
        category = item.get("categoryName", "Unbekannt")

        # Koordinaten sind im location-Objekt versteckt
        location = item.get("location", {}) or {}
        lat = location.get("lat")
        lng = location.get("lng")

        if url and url not in ["", "http://", "https://"]:
            domain = get_domain(url)
            # Einfache Deduplizierung über die Domain
            if domain and domain not in seen_domains and len(domain) > 4:
                seen_domains.add(domain)
                candidates.append({
                    "name": name,
                    "website": url,
                    "google_category": category,
                    "domain": domain,
                    "address": item.get("address", ""),
                    "phone": item.get("phone", ""),
                    "lat": lat,
                    "lng": lng
                })
                print(f"      • {name[:40]:<40} | 📍 {lat},{lng}")

    print(f"   -> Eindeutige Kandidaten: {len(candidates)}")
    return candidates

def sniper_search_and_scrape(candidates, search_keywords, country_code):
    """
    Schritt 2: Gezielte Google-Suche (site:domain.com keywords).
    Statt die ganze Seite zu crawlen, suchen wir im Google Index direkt nach den relevanten Unterseiten
    und scrapen nur diese via Cheerio. Spart massiv Zeit und Kosten.
    """
    if not candidates:
        return {}

    print(f"\n🎯 SNIPER: Generiere Suchanfragen für {len(candidates)} Seiten...")

    search_queries = []
    candidate_map = {}
    keyword_string = " OR ".join(search_keywords)

    # Bauen der "site:" Queries
    for cand in candidates:
        domain = cand['domain']
        if not domain: continue
        
        candidate_map[domain] = cand
        query = f"site:{domain} ({keyword_string})"
        search_queries.append(query)
        # Debug output für den ersten
        if len(search_queries) == 1:
            print(f"      🔎 Beispiel-Query: {query}")

    print(f"   -> Starte {len(search_queries)} Google-Suche(n) via Apify...")

    # Google Search Scraper Konfiguration
    search_input = {
        "queries": "\n".join(search_queries),
        "countryCode": country_code.lower(),
        "languageCode": "de",
        "maxPagesPerQuery": MAX_PAGES_PER_QUERY,
    }

    search_run = apify.actor("apify/google-search-scraper").call(run_input=search_input)
    search_results = apify.dataset(search_run["defaultDatasetId"]).list_items().items

    urls_to_scrape = []

    # Filterung: Wir nehmen nur URLs, die wirklich zur Domain des Kandidaten gehören
    print(f"\n   🔗 Relevante Deep-Links gefunden:")
    for item in search_results:
        for res in item.get("organicResults", []):
            url = res.get("url")
            if url:
                domain = get_domain(url)
                # Check, ob die gefundene URL zu einem unserer Kandidaten gehört
                for cand_domain in candidate_map:
                    if cand_domain in domain or domain in cand_domain:
                        urls_to_scrape.append({"url": url})
                        # Nur den ersten Treffer pro Domain loggen, sonst spammt es die Konsole voll
                        break

    print(f"   -> Scrape jetzt {len(urls_to_scrape)} spezifische Unterseiten...")

    if not urls_to_scrape:
        return {}

    # Cheerio Scraper: Schnell und günstig für reinen Text
    scrape_input = {
        "startUrls": urls_to_scrape,
        "maxRequestRetries": 1,
        "proxyConfiguration": {"useApifyProxy": True},
        "ignoreSslErrors": True,
        # Wir entfernen direkt alles, was kein Content ist (Navi, Footer, Cookie-Banner)
        "pageFunction": """
            async function pageFunction(context) {
                const { $ } = context;
                
                // Weg mit dem Müll
                $('script, style, nav, footer, header, iframe, noscript').remove();
                $('.cookie-banner, #cookie-consent, .modal, .popup, .map-placeholder').remove();

                // Versuch den Hauptinhalt zu greifen
                let content = $('main, #content, .content, article').text();
                
                // Fallback auf Body, wenn main leer ist
                if (content.length < 200) {
                    content = $('body').text();
                }

                return {
                    url: context.request.url,
                    text: content.replace(/\\s\\s+/g, ' ').trim()
                };
            }
        """
    }

    scrape_run = apify.actor("apify/cheerio-scraper").call(run_input=scrape_input)
    scraped_items = apify.dataset(scrape_run["defaultDatasetId"]).list_items().items

    # Text den Kandidaten zuordnen
    content_map = {}
    for item in scraped_items:
        url = item.get("url")
        if not url: continue
        
        text = item.get("text", "") or ""
        domain = get_domain(url)
        
        for cand_domain, info in candidate_map.items():
            if cand_domain in domain or domain in cand_domain:
                main_url = info['website']
                if main_url not in content_map:
                    content_map[main_url] = ""
                # Wir hängen den Text an, falls wir mehrere Unterseiten pro Domain haben
                content_map[main_url] += f"\n\n--- SOURCE: {url} ---\n{text[:25000]}"
                break

    return content_map
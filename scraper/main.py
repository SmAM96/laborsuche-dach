import os
import json
import pandas as pd
from .config import DATA_DIR
from .scraper import find_places_discovery, sniper_search_and_scrape
from .validator import validate_dexa, validate_blood

def run_pipeline(city, country_code, category, queries, keywords, validate_func):
    print(f"\n{'='*60}")
    print(f"🚀 START PIPELINE: {category} in {city} ({country_code.upper()})")
    print(f"{'='*60}")

    # 1. Kandidaten finden
    candidates = find_places_discovery(city, queries)

    # 2. Relevante Texte scrapen (Sniper-Methode)
    content_map = sniper_search_and_scrape(candidates, keywords, country_code)

    # 3. Validierung durch AI
    valid_results = []
    rejected_results = []

    print(f"\n🧠 VALIDIERE {len(candidates)} Kandidaten...")
    print(f"{'-'*80}")
    print(f"{'NAME':<40} | {'STATUS':<12} | {'QUOTE'}")
    print(f"{'-'*80}")

    for cand in candidates:
        text = content_map.get(cand["website"], "")
        res = validate_func(text, cand["name"])

        cand.update(res)
        
        # Output formatieren für bessere Lesbarkeit
        quote = (res.get("evidence_quote") or "")
        quote_snippet = (quote[:40].replace("\n", " ") + "...") if quote else ""
        
        if res["status"] == "YES":
            print(f"✅ {cand['name'][:38]:<38} | YES          | {quote_snippet}")
            valid_results.append(cand)
        else:
            print(f"❌ {cand['name'][:38]:<38} | {res['status']:<12} | {res.get('reason', '')}")
            rejected_results.append(cand)

    return valid_results, rejected_results

def main():
    city = input("Stadt (z.B. Berlin / Wien / Zürich): ").strip()
    country_code = input("Ländercode (de/at/ch): ").strip().lower()

    if not city or country_code not in {"de", "at", "ch"}:
        print("❌ Ungültige Eingabe.")
        return

    # Sicherstellen, dass der ../data Ordner existiert
    os.makedirs(DATA_DIR, exist_ok=True)
    print(f"📂 Speicherort für Daten: {os.path.abspath(DATA_DIR)}")

    # --- DEXA SUCHE ---
    dexa_valid, dexa_rejected = run_pipeline(
        city, country_code, "DEXA",
        queries=[f"{city} DEXA Body Scan", f"{city} DXA Scan", f"{city} DEXA Körperanalyse"],
        keywords=["Körperfett", "Muskelmasse", "Body Composition", "Viszeralfett", "DXA", "Weichteilanalyse"],
        validate_func=validate_dexa
    )

    # Speichern
    with open(os.path.join(DATA_DIR, f"{city}_DEXA_VALID.json"), "w", encoding="utf-8") as f:
        json.dump(dexa_valid, f, indent=2, ensure_ascii=False)
    
    # Abgelehnte speichern wir als CSV, falls wir manuell drüberschauen wollen
    if dexa_rejected:
        pd.DataFrame(dexa_rejected).to_csv(os.path.join(DATA_DIR, f"{city}_DEXA_REJECTED.csv"), index=False)

    # --- BLUTLABOR SUCHE ---
    blood_valid, blood_rejected = run_pipeline(
        city, country_code, "BLOOD",
        queries=[f"{city} Privatlabor", f"{city} Blutabnahme Selbstzahler", f"{city} Direktlabor"],
        keywords=["Selbstzahler", "ohne Überweisung", "Preisliste", "Health Check", "Direktlabor"],
        validate_func=validate_blood
    )

    with open(os.path.join(DATA_DIR, f"{city}_BLOOD_VALID.json"), "w", encoding="utf-8") as f:
        json.dump(blood_valid, f, indent=2, ensure_ascii=False)

    if blood_rejected:
        pd.DataFrame(blood_rejected).to_csv(os.path.join(DATA_DIR, f"{city}_BLOOD_REJECTED.csv"), index=False)

    print(f"\n🏁 FERTIG. Daten liegen in {DATA_DIR}")

if __name__ == "__main__":
    main()
import json
from openai import OpenAI
from .config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def validate_dexa(text, name):
    """
    Prüft via LLM, ob es sich wirklich um Body Composition handelt 
    oder nur um Knochendichte (Osteoporose).
    """
    if not text:
        return {"status": "QUESTIONABLE", "reason": "Kein Text gescrapt", "evidence_quote": None}

    prompt = f"""You are a strict compliance auditor for a healthcare provider directory.

Goal:
Decide if provider "{name}" offers a **DXA/DEXA Body Composition** scan (fat %, muscle mass, lean mass, visceral fat) as a patient service.

- LOOK FOR: "Körperfett", "Muskelmasse", "Fettanteil", "Viszeralfett", "DXA", "Body Scan".
- IGNORE: "Knochendichte" (Osteoporosis) if it's the ONLY mention.
- IGNORE: Cookie banners, Google Maps placeholders.
CRITICAL RULES:
1. ✅ YES: Found specific sentence linking "DEXA"/"DXA" directly with "Körperfett", "Fettanteil", "Muskelmasse", "Weichteilanalyse" or "Gewebe".
2. ❌ NO: If "DEXA" is mentioned ONLY in the context of "Knochendichte", "Osteoporose", "T-Wert", "Lendenwirbelsäule".
3. ❌ NO: If body composition is done via "MRI", "Ganzkörper-MRI", "MRT", "BIA", "Bioimpedanz", "InBody", "Seca". (MRI is NOT DEXA).
4. ❌ NO: If "Sportmedizin" and "DEXA" are mentioned separately without grammatical link.

Text Snippets:
{text[:25000]}

Response JSON: {{"status":"YES"|"NO"|"QUESTIONABLE", "evidence_quote": "..."}}"""

    return _call_openai(prompt)

def validate_blood(text, name):
    """
    Prüft, ob Blutabnahme ohne ärztliche Überweisung (Selbstzahler) möglich ist.
    """
    if not text:
        return {"status": "QUESTIONABLE", "reason": "Kein Text gescrapt", "evidence_quote": None}

    prompt = f"""
Du bist ein strenger Auditor für DACH-Gesundheitsanbieter. Du darfst NICHT raten.

AUFGABE
Prüfe anhand des gegebenen Textes, ob der Anbieter "{name}" Blut-/Laboruntersuchungen
für Patienten als Selbstzahler OHNE ärztliche Überweisung / ohne ärztliche Anforderung anbietet.

STRICT DECISION RULES (keine Heuristiken)
- YES nur wenn im Text explizit steht, dass Patienten ohne Überweisung / ohne Rezept / ohne ärztliche Anforderung
  Tests beauftragen können (Synonyme ok: "ohne ärztliche Verordnung", "ohne Arzt", "Direktauftrag",
  "Patientenauftrag", "Direktlabor", "ohne Überweisungsschein").
- NO wenn explizit steht: nur mit Überweisung / nur ärztliche Anforderung / Zuweiser/Einsender-only / Auftrag durch Arzt.
- NO wenn alle Angebote, die sich ausschließlich auf folgende Themen beziehen: covid, testzentrum, schnelltest, pcr, corona, impfen
- QUESTIONABLE wenn:
  
  - es wie ein Service für Ärzte/Kooperationspartner wirkt, ohne klare Patienten-Selbstbeauftragung.

EVIDENZ-PFLICHT
- Gib IMMER eine evidence_quote als wörtliches Zitat (copy/paste) aus dem Text.
- Für YES muss evidence_quote die "ohne Überweisung/ohne Rezept/ohne ärztliche Anforderung"-Aussage, ohne ärztliche Verordnung", "ohne Arzt", "Direktauftrag ...  enthalten.
- Für NO muss evidence_quote die Pflicht zur Überweisung/ärztlichen Anforderung enthalten.
- Wenn keine passende, wörtliche Evidenz existiert: QUESTIONABLE.

Provider: {name}

Text Snippets:
{text[:25000]}

Response JSON: {{"status":"YES"|"NO"|"QUESTIONABLE", "evidence_quote": "..."}}"""

    return _call_openai(prompt)

def _call_openai(prompt):
    try:
        res = client.chat.completions.create(
            model="gpt-4-turbo", 
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(res.choices[0].message.content)
    except Exception as e:
        return {"status": "QUESTIONABLE", "reason": f"AI Error: {str(e)}", "evidence_quote": None}
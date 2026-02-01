import os
from dotenv import load_dotenv

load_dotenv() # Load variables from .env file

APIFY_TOKEN = os.getenv("APIFY_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Scraping Limits
MAX_CRAWLED_PLACES_PER_SEARCH = 30
MAX_PAGES_PER_QUERY = 1  # 1 Seite ≈ 10 Ergebnisse

# Pfad für den Output: Ein Ordner über dem aktuellen Skript (../data)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
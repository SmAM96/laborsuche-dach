from urllib.parse import urlparse

def get_domain(url):
    """
    Holt die saubere Domain aus einer URL.
    """
    if not url or not isinstance(url, str):
        return ""
    try:
        # Falls http fehlt, einfach davorhängen damit urlparse nicht meckert
        if not url.startswith("http"):
            url = "http://" + url
        
        # www. wegwerfen, stört nur beim Vergleich
        return urlparse(url).netloc.replace("www.", "").strip().lower()
    except:
        return ""
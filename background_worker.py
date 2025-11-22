import time
import json
import os
from scrapers.service import ScraperService
from scrapers.registry import provider_registry
from dataclasses import asdict

CACHE_FILE = "cache/events.json"
service = ScraperService(provider_registry)

def run_scraping():
    """Ejecuta scraping de todos los providers y actualiza la caché."""
    print("Scraping iniciado...")
    try:
        events = service.build_events()
        data = [asdict(e) for e in events]
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Scraping completado ({len(events)} eventos)")
        
        # Log por provider
        from collections import Counter
        providers = Counter(e.provider for e in events)
        for prov, count in providers.items():
            print(f"  - {prov}: {count} eventos")
            
    except Exception as e:
        print(f"Error scraping: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Worker ejecutándose...")
    while True:
        run_scraping()
        time.sleep(120)  # 2 minutos
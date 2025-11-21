import time
import json
from scrapers.service import ScraperService
from scrapers.registry import provider_registry
from dataclasses import asdict

CACHE_FILE = "cache/events.json"

service = ScraperService(provider_registry)


def run_scraping():
    print("Scraping iniciado...")
    try:
        events = service.build_events()
        data = [asdict(e) for e in events]

        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Scraping completado ({len(events)} eventos)")
    except Exception as e:
        print(f"Error scraping: {e}")


if __name__ == "__main__":
    print("Worker ejecutándose...")
    while True:
        run_scraping()
        time.sleep(120)  # cada 2 minutos

import time
import json
import os
from scrapers.service import ScraperService
from scrapers.registry import provider_registry
from dataclasses import asdict

# Archivo de caché a escribir
CACHE_FILE = "cache/events.json"

# Instanciamos el servicio
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
    except Exception as e:
        print(f"Error scraping: {e}")


if __name__ == "__main__":
    print("Worker ejecutándose...")
    while True:
        run_scraping()
        # Esperamos 2 minutos entre ejecuciones (puedes ajustarlo)
        time.sleep(120)

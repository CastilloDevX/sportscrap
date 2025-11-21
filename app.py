from flask import Flask, jsonify, render_template, request, Response
import requests
import json
import os
from datetime import datetime

from scrapers.service import ScraperService
from scrapers.registry import provider_registry
from dataclasses import asdict

# Ubicación del archivo de caché
CACHE_FILE = "cache/events.json"

app = Flask(__name__)

# Instanciamos el servicio de scrapers para generar eventos si no hay caché
service = ScraperService(provider_registry)


def load_events():
    # 1. Intentar leer la caché
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data:
                    return data
        except Exception:
            pass

    # 2. Si no hay datos, ejecutar los scrapers y escribir cache
    try:
        events = service.build_events()
        data = [asdict(e) for e in events]
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return data
    except Exception as e:
        print(f"Error generando eventos: {e}")
        return []


# Filtro de plantilla para convertir timestamps a fechas legibles
@app.template_filter("datetime")
def datetime_filter(ts):
    try:
        ts = int(ts)
        return datetime.utcfromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M:%S") if ts > 0 else "-"
    except Exception:
        return "-"


# Proxy para esquivar bloqueos de referer
@app.route("/proxy")
def proxy():
    target = request.args.get("u")
    if not target:
        return "Missing URL", 400

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://kevinsport.digital/"
    }

    r = requests.get(target, headers=headers)
    return Response(r.content, content_type=r.headers.get("Content-Type"))


# Página principal
@app.route("/")
def index():
    events = load_events()
    return render_template("index.html", events=events, title="Sportstream")


# Endpoint opcional para consultar eventos vía AJAX
@app.route("/api/events")
def api_events():
    return jsonify(load_events())


# Página de stream individual
@app.route("/stream")
def stream():
    url = request.args.get("url")
    source = request.args.get("source")
    event_id = request.args.get("event")

    # Cargar eventos desde cache
    events = load_events()

    # Buscar el evento seleccionado
    event_obj = next((e for e in events if str(e.get("id")) == str(event_id)), None)

    if not event_obj:
        return "Evento no encontrado", 404

    # Los streams normalmente ya vienen en el evento cacheado
    event_streams = event_obj.get("streams", [])

    # Recargar streams para LiveTV, Kevinsport, etc. si el usuario lo pide
    if source and "livetv" in source.lower():
        from scrapers.providers.livetv import LiveTVProvider
        provider = LiveTVProvider()
        event_streams = provider._parse_event_streams(event_obj["url"])
    elif source and "kevinsport" in source.lower():
        from scrapers.providers.kevinsport import KevinsportProvider
        provider = KevinsportProvider()
        event_streams = provider._get_event_streams(event_obj["url"])
        if url:
            url = f"/proxy?u={url}"
    elif source and "kakarot" in source.lower():
        # Los streams de Kakarotfoot vienen listos en caché
        pass

    # Si no hay URL pero hay streams, elegimos el primero
    if not url and event_streams:
        url = event_streams[0]["url"]

    return render_template(
        "stream.html",
        url=url,
        source=source,
        event=event_obj,
        event_streams=event_streams,
        event_id=event_id,
        title="Reproducción en directo"
    )


if __name__ == "__main__":
    # Railway/Render necesitan bindear a 0.0.0.0 y usar el puerto de entorno
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)

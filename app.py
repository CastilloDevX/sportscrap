from flask import Flask, jsonify, render_template, request, Response
import requests
from datetime import datetime
from scrapers.service import ScraperService
from scrapers.registry import provider_registry
from dataclasses import asdict

app = Flask(__name__)

service = ScraperService(provider_registry)

# ---- FILTER datetime (necesario para Kakarotfoot) ----
@app.template_filter("datetime")
def datetime_filter(ts):
    try:
        ts = int(ts)
        return datetime.utcfromtimestamp(ts/1000).strftime("%Y-%m-%d %H:%M:%S") if ts > 0 else "-"
    except Exception:
        return "-"



# --------- PROXY PARA EVITAR REFERRER BLOCK ----------
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


# -------- INDEX --------
@app.route("/")
def index():
    events = service.build_events()
    return render_template("index.html", events=events, title="Sportstream")


# -------- STREAM PAGE --------
@app.route("/stream")
def stream():
    url = request.args.get("url")
    source = request.args.get("source")
    event_id = request.args.get("event")

    # Volver a obtener eventos (pero sin streams pesados)
    events = service.build_events()

    # Buscar el evento correspondiente
    event_obj = next((e for e in events if str(e.id) == str(event_id)), None)

    if not event_obj:
        return "Evento no encontrado", 404

    # -------------------------
    #  LAZY STREAMS POR PROVEEDOR
    # -------------------------
    event_streams = event_obj.streams  # En caso de Kakarotfoot o TiroAlPalo — ya vienen listos

    # LIVE TV
    if source and "livetv" in source.lower():
        from scrapers.providers.livetv import LiveTVProvider
        provider = LiveTVProvider()
        event_streams = provider._parse_event_streams(event_obj.url)

    # KEVINSPORT (necesita PROXY y streams extra)
    elif source and "kevinsport" in source.lower():
        from scrapers.providers.kevinsport import KevinsportProvider
        provider = KevinsportProvider()
        event_streams = provider._get_event_streams(event_obj.url)

        # Aplicar PROXY al stream principal
        if url:
            url = f"/proxy?u={url}"

    # KAKAROTFOOT – streams ya vienen listos
    elif source and "kakarot" in source.lower():
        pass  # Nada que hacer

    # Si por alguna razón el URL viene vacío
    if not url and event_streams:
        url = event_streams[0].url

    # -------------------------
    # Renderizar página
    # -------------------------
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
    app.run(debug=True)

from flask import Flask, jsonify, render_template, request, Response
import requests
import json
import os
from datetime import datetime

# --- CONFIG ---
CACHE_FILE = "cache/events.json"

app = Flask(__name__)


# ---------------------------- #
#   UTILIDAD: Cargar cache     #
# ---------------------------- #
def load_events():
    """Carga los eventos desde el archivo cacheado por el worker."""
    if not os.path.exists(CACHE_FILE):
        return []
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


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
    events = load_events()
    return render_template("index.html", events=events, title="Sportstream")


# -------- API (opcional para AJAX) --------
@app.route("/api/events")
def api_events():
    return jsonify(load_events())


# -------- STREAM PAGE --------
@app.route("/stream")
def stream():
    url = request.args.get("url")
    source = request.args.get("source")
    event_id = request.args.get("event")

    # Cargar eventos del cache
    events = load_events()

    # Buscar evento
    event_obj = next((e for e in events if str(e.get("id")) == str(event_id)), None)

    if not event_obj:
        return "Evento no encontrado", 404

    # STREAMS (los eventos cacheados ya traen streams en muchos casos)
    event_streams = event_obj.get("streams", [])

    # -------------------------
    #  LIVE TV
    # -------------------------
    if source and "livetv" in source.lower():
        from scrapers.providers.livetv import LiveTVProvider
        provider = LiveTVProvider()
        event_streams = provider._parse_event_streams(event_obj["url"])

    # -------------------------
    #  KEVINSPORT
    # -------------------------
    elif source and "kevinsport" in source.lower():
        from scrapers.providers.kevinsport import KevinsportProvider
        provider = KevinsportProvider()
        event_streams = provider._get_event_streams(event_obj["url"])

        if url:
            url = f"/proxy?u={url}"

    # -------------------------
    #  KAKAROTFOOT
    # -------------------------
    elif source and "kakarot" in source.lower():
        pass  # Streams ya estaban listos

    # Si no llega URL pero hay streams
    if not url and event_streams:
        url = event_streams[0]["url"]

    # Render
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
    # Railway requiere bindear a 0.0.0.0 y puerto ENV
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)

from flask import Flask, jsonify, render_template, request
from dataclasses import asdict
from scrapers.service import ScraperService
from scrapers.registry import provider_registry

app = Flask(__name__, static_url_path="/static")

# Instancia del servicio (inyecta el registro de proveedores)
scraper_service = ScraperService(provider_registry)

@app.template_filter('datetime')
def datetime_filter(ms_timestamp):
    # UTC -> YYYY-MM-DD HH:MM:SS
    from datetime import datetime
    try:
        return datetime.utcfromtimestamp(int(ms_timestamp) / 1000).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return ""

@app.route("/")
def index():
    # Carga inicial SSR (server-side render)
    events = scraper_service.build_events()
    return render_template("index.html", events=events, title="Sportstream")

@app.route("/api/events")
def api_events():
    events = scraper_service.build_events()
    return jsonify([asdict(e) for e in events])

@app.route("/stream")
def stream():
    url = request.args.get("url")
    source = request.args.get("source", "")
    return render_template("stream.html", url=url, source=source, title="Reproducción en directo")

if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, jsonify, render_template, request
from datetime import datetime
from scrapers.service import ScraperService
from scrapers.registry import provider_registry

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="public",
    static_url_path=""
)

service = ScraperService(provider_registry)

# Filtro de fecha para mostrar timestamps
@app.template_filter("datetime")
def datetime_filter(ts):
    try:
        return datetime.utcfromtimestamp(int(ts) / 1000).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "?"

@app.route("/")
def index():
    events = service.build_events()
    return render_template("index.html", events=events, title="Sportstream")

@app.route("/api")
def api_events():
    events = service.build_events()
    return jsonify([e.to_dict() for e in events])

@app.route("/stream")
def stream():
    url = request.args.get("url")
    source = request.args.get("source", "")
    return render_template("stream.html", url=url, source=source, title="Reproducción en directo")

if __name__ == "__main__":
    app.run(debug=True)
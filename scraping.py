import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import requests

@dataclass
class Stream:
    """
    Representa un flujo de vídeo para un evento.

    Se añade un campo opcional `source` que indica de qué sitio web proviene
    el enlace (p. ej. "Kakarotfoot", "Tiroalpalo", "KevinSport" o "LiveTV").
    """
    name: str
    url: str
    language: Optional[str] = None
    source: Optional[str] = None


@dataclass
class Event:
    """Representa un evento deportivo."""
    id: str
    name: str
    url: str
    league: str
    home: str
    away: str
    start_time: int
    streams: List[Stream]


def get_html(url: str) -> str:
    """Realiza una solicitud HTTP y obtiene el HTML de la página."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener la página {url}: {e}")
        return ""


def parse_kakarot_event_page(html: str) -> List[Stream]:
    """Extrae flujos en español de una página de evento de kakarotfoot.ru."""
    soup = BeautifulSoup(html, "html.parser")
    container = soup.find(id="kaurukavideo")
    streams: List[Stream] = []
    if not container:
        return streams
    for span in container.select("span.change-video"):
        text = (span.get_text() or "").strip()
        if " es" in text.lower():
            embed_url = span.get("data-embed") or ""
            # Marcamos la fuente "Kakarotfoot"
            streams.append(Stream(name=text, url=embed_url, language="es", source="Kakarotfoot"))
    return streams

def build_events() -> List[Event]:
    """
    Obtiene eventos en español a partir del feed JSON de Kakarotfoot.

    Lee el JSON, filtra los eventos con canales en español y crea objetos Event.
    Para cada canal en español, genera un Stream con su origen "Kakarotfoot".

    Si deseas ampliar a Tiroalpalo, KevinSport o LiveTV, puedes usar las
    funciones parse_* correspondientes, pero algunas páginas requieren JavaScript
    y podrían no funcionar sin un navegador de verdad.
    """
    events: List[Event] = []
    # Descargar datos de Kakarotfoot
    try:
        data = requests.get("https://kakarotfoot.ru/json.php").json()
    except Exception as e:
        print(f"No se pudo descargar el feed JSON: {e}")
        return events

    for obj in data:
        # Filtrar canales en español
        es_channels = [ch.get("ch") for ch in obj.get("streams", []) if ch.get("lang") == "es"]
        if not es_channels:
            continue
        event = Event(
            id=obj["id"],
            name=f"{obj['home']} vs {obj['away']}",
            url=f"https://kakarotfoot.ru/{obj['url']}",
            league=obj.get("league", ""),
            home=obj.get("home", ""),
            away=obj.get("away", ""),
            start_time=int(obj.get("time", 0)),
            streams=[]
        )
        for ch in es_channels:
            # Generamos un enlace de streaming con su canal
            stream_url = f"https://kakarotfoot.ru/yu/3/{ch}"
            event.streams.append(Stream(
                name=f"Canal {ch} (es)",
                url=stream_url,
                language="es",
                source="Kakarotfoot"
            ))
        events.append(event)

    return events

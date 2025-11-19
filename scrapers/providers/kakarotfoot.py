import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from ..models import Event, Stream
from ..base import BaseProvider

class KakarotfootProvider(BaseProvider):
    name = "Kakarotfoot"
    FEED = "https://kakarotfoot.ru/json.php"

    def fetch_events(self) -> List[Event]:
        events: List[Event] = []
        try:
            data = requests.get(self.FEED, timeout=15).json()
        except Exception:
            return events

        for obj in data:
            streams_data = obj.get("streams", []) or []
            if not streams_data:
                continue

            e = Event(
                id=str(obj.get("id", "")),
                name=f"{obj.get('home','')} vs {obj.get('away','')}",
                url=f"https://kakarotfoot.ru/{obj.get('url','')}",
                league=obj.get("league", ""),
                home=obj.get("home", ""),
                away=obj.get("away", ""),
                start_time=int(obj.get("time", 0)),
                streams=[]
            )

            # ✅ Trae TODOS los canales del feed y usa el NOMBRE REAL del canal si viene en el JSON
            for s in streams_data:
                ch: Optional[str] = s.get("ch") or s.get("channel") or s.get("id")
                if not ch:
                    continue

                # nombre visible del canal según el feed
                display_name = (
                    s.get("name")
                    or s.get("title")
                    or s.get("label")
                    or f"Canal {ch}"
                )

                lang = (s.get("lang") or "").lower() or None
                stream_url = f"https://kakarotfoot.ru/yu/3/{ch}"

                e.streams.append(Stream(
                    name=display_name,     # ← nombre real del canal
                    url=stream_url,
                    language=lang,         # ← lo mostraremos como badge en la UI
                    source=self.name
                ))

            # si por alguna razón no hay streams tras parsear, salta
            if not e.streams:
                continue

            events.append(e)

        return events

    @staticmethod
    def parse_event_page(html: str) -> List[Stream]:
        soup = BeautifulSoup(html, "html.parser")
        container = soup.find(id="kaurukavideo")
        if not container:
            return []
        streams: List[Stream] = []
        for span in container.select("span.change-video"):
            txt = (span.get_text() or "").strip()
            embed = span.get("data-embed") or ""
            # intenta extraer ‘ES’, ‘EN’, etc. del texto
            lang = None
            low = txt.lower()
            if " es" in low or "(es" in low:
                lang = "es"
            streams.append(Stream(name=txt, url=embed, language=lang, source="Kakarotfoot"))
        return streams

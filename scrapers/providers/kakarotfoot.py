import requests
from typing import List
from ..models import Event, Stream
from ..base import BaseProvider

class KakarotfootProvider(BaseProvider):
    name = "Kakarotfoot"
    FEED = "https://kakarotfoot.ru/json.php"

    def fetch_events(self) -> List[Event]:
        events = []
        try:
            data = requests.get(self.FEED, timeout=10).json()
        except:
            return events

        for obj in data:
            streams_info = obj.get("streams", [])
            if not streams_info:
                continue

            e = Event(
                id=str(obj.get("id", "")),
                name=f"{obj.get('home', '')} vs {obj.get('away', '')}",
                url=f"https://kakarotfoot.ru/{obj.get('url', '')}",
                league=obj.get("league", ""),
                home=obj.get("home", ""),
                away=obj.get("away", ""),
                start_time=int(obj.get("time", 0)),
                streams=[]
            )

            for s in streams_info:
                ch = s.get("ch")
                if not ch:
                    continue

                display_name = s.get("name") or f"Canal {ch}"
                lang = s.get("lang")

                e.streams.append(Stream(
                    name=display_name,
                    url=f"https://kakarotfoot.ru/yu/3/{ch}",
                    language=lang,
                    source=self.name
                ))

            events.append(e)

        return events

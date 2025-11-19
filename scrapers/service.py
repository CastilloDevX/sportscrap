from typing import List, Iterable
from .models import Event
from .base import BaseProvider

class ScraperService:
    def __init__(self, providers: Iterable[BaseProvider]):
        self.providers = list(providers)

    def build_events(self) -> List[Event]:
        # Agrega eventos de todos los proveedores registrados
        events: List[Event] = []
        for p in self.providers:
            try:
                events.extend(p.fetch_events())
            except Exception:
                # aislamos errores por proveedor
                continue

        # Ordena por hora de inicio y remueve duplicados (id+league como llave simple)
        seen = set()
        unique: List[Event] = []
        for e in sorted(events, key=lambda x: x.start_time):
            key = (e.id, e.league)
            if key in seen:
                continue
            seen.add(key)
            unique.append(e)
        return unique

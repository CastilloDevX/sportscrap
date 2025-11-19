from abc import ABC, abstractmethod
from typing import List
from .models import Event

class BaseProvider(ABC):
    # Contrato para proveedores (Kakarotfoot, etc.)."""
    name: str

    @abstractmethod
    def fetch_events(self) -> List[Event]:
        # Devuelve eventos (con streams) listos para consumir
        raise NotImplementedError

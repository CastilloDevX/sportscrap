from typing import List
from .base import BaseProvider
from .providers.kakarotfoot import KakarotfootProvider

# Aquí registras todos los proveedores disponibles
provider_registry: List[BaseProvider] = [
    KakarotfootProvider(),
    # Ejemplo futuro:
    # TiroAlPaloProvider(),
    # KevinSportProvider(),
]

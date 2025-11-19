from typing import List
from .base import BaseProvider
from .providers.kakarotfoot import KakarotfootProvider

provider_registry: List[BaseProvider] = [
    KakarotfootProvider()
]

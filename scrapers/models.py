from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Stream:
    name: str
    url: str
    language: Optional[str] = None
    source: Optional[str] = None

@dataclass
class Event:
    id: str
    name: str
    url: str
    league: str
    home: str
    away: str
    start_time: int  # epoch ms (UTC)
    streams: List[Stream] = field(default_factory=list)

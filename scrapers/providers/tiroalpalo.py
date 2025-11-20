from __future__ import annotations
import re
from datetime import datetime
from typing import List, Optional
import requests
from bs4 import BeautifulSoup
from ..base import BaseProvider
from ..models import Event, Stream

class TiroalpaloProvider(BaseProvider):
    name = "Tiroalpalo"
    LIST_URL = "https://tiroalpalome.com/directo"

    def fetch_events(self) -> List[Event]:
        events = []
        try:
            html = requests.get(self.LIST_URL, timeout=10).text
        except:
            return events

        soup = BeautifulSoup(html, "html.parser")

        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)
            if not href.startswith("https://tiroalpalome.com"):
                continue
            if "-" in text or " vs " in text.lower():
                links.append((href, text))

        seen = set()
        for href, text in links:
            if href in seen:
                continue
            seen.add(href)

            event = self._parse_event_page(href, text)
            if event:
                events.append(event)

        return events

    def _parse_event_page(self, url: str, fallback: str) -> Optional[Event]:
        try:
            html = requests.get(url, timeout=10).text
        except:
            return None

        soup = BeautifulSoup(html, "html.parser")

        # Título
        title_tag = soup.find(["h1", "h2", "h3"])
        title = title_tag.get_text(strip=True) if title_tag else fallback

        match_time = None
        home = ""
        away = ""

        m = re.match(r"(\d{1,2}:\d{2})\s*[|\-]?(.*)", title)
        if m:
            match_time = m.group(1)
            title_no_time = m.group(2).strip()
        else:
            title_no_time = title

        if " vs " in title_no_time.lower():
            parts = re.split(r"\s+vs\s+", title_no_time, flags=re.IGNORECASE)
            if len(parts) == 2:
                home, away = parts
        elif "-" in title_no_time:
            parts = title_no_time.split("-", 1)
            if len(parts) == 2:
                home, away = parts[0].strip(), parts[1].strip()
        else:
            home = title_no_time

        start_ms = 0
        if match_time:
            try:
                hh, mm = map(int, match_time.split(":"))
                now = datetime.utcnow()
                dt = now.replace(hour=hh, minute=mm, second=0)
                if dt < now:
                    dt = dt.replace(day=now.day + 1)
                start_ms = int(dt.timestamp() * 1000)
            except:
                pass

        streams = []
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True).lower()
            if text.startswith("link") or text.startswith("alternativo"):
                streams.append(Stream(
                    name=a.get_text(strip=True),
                    url=a["href"],
                    source="Tiroalpalo"
                ))

        if not streams:
            return None

        return Event(
            id=url,
            name=title_no_time,
            url=url,
            league="",
            home=home,
            away=away,
            start_time=start_ms,
            provider="Tiroalpalo",
            streams=streams
        )

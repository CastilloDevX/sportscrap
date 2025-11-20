"""
KevinSport Provider — Scraper completo y optimizado
"""

from __future__ import annotations
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import List

from ..base import BaseProvider
from ..models import Event, Stream


class KevinsportProvider(BaseProvider):
    name = "KevinSport"
    URL = "https://kevinsport.pro/live/football/"

    def fetch_events(self) -> List[Event]:
        return asyncio.run(self.fetch_events_async())

    async def fetch_events_async(self) -> List[Event]:
        events: List[Event] = []

        async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0"}) as session:
            try:
                async with session.get(self.URL, timeout=10) as resp:
                    html = await resp.text()
            except:
                return events

            soup = BeautifulSoup(html, "html.parser")
            rows = soup.select("table.table-hover tr")
            current_league = "(Desconocido)"
            tasks = []

            for row in rows:
                classes = row.get("class", [])

                # FILA DE LIGA
                if "table-info" in classes:
                    txt = row.get_text(strip=True)
                    if txt:
                        current_league = txt
                    continue

                # FILA DE PARTIDO
                if "table-dark" not in classes:
                    continue

                # Hora
                time_td = row.find("td", class_="matchtime")
                match_time = time_td.get_text(strip=True) if time_td else ""

                # Equipos
                title_td = row.find("td", class_="pnltblttl")
                title = title_td.get_text(strip=True) if title_td else "Unknown"

                if " Vs " in title:
                    home, away = title.split(" Vs ", 1)
                else:
                    home, away = title, ""

                # Nombre formateado
                name_final = (
                    f"{home} vs {away} ({match_time})"
                    if match_time else f"{home} vs {away}"
                )

                # Link de Watch
                watch = row.find("a", href=True)
                if not watch:
                    continue
                event_page = watch["href"]

                event = Event(
                    id=event_page,
                    name=name_final,
                    url=event_page,
                    league=current_league,
                    home=home,
                    away=away,
                    start_time=0,
                    provider="KevinSport",
                    match_time=match_time,
                    streams=[]
                )

                events.append(event)
                tasks.append(self._load_streams_async(session, event))

            await asyncio.gather(*tasks)
            return events

    async def _load_streams_async(self, session, event: Event):
        # Página principal del evento
        try:
            async with session.get(event.url, timeout=10) as r:
                html = await r.text()
        except:
            return

        soup = BeautifulSoup(html, "html.parser")

        # Iframe principal
        iframe = soup.find("iframe")
        if iframe:
            src = iframe.get("src")
            if src:
                event.streams.append(Stream(
                    name="Stream 1",
                    url=src,
                    source="KevinSport"
                ))

        # Streams secundarios
        stream_buttons = soup.find_all("a", string=lambda t: t and "Stream" in t)

        for btn in stream_buttons:
            href = btn.get("href")
            if not href:
                continue

            try:
                async with session.get(href, timeout=10) as r2:
                    sub_html = await r2.text()
            except:
                continue

            sub_soup = BeautifulSoup(sub_html, "html.parser")
            sub_iframe = sub_soup.find("iframe")

            if not sub_iframe:
                continue

            src = sub_iframe.get("src")
            if src:
                event.streams.append(Stream(
                    name=btn.get_text(strip=True),
                    url=src,
                    source="KevinSport"
                ))

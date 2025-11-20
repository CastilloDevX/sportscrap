"""
LiveTV Provider - Lazy Streams

• Lee la página de próximos partidos de LiveTV (fútbol).
• Crea eventos SIN streams (Lazy Streams).
• La liga se extrae desde el texto entre paréntesis: (Brazil. Serie A).
• La fecha/hora de LiveTV NO se convierte a timestamp (se ignora para evitar 1970-01-01).
• Los streams se obtienen solo cuando entras a /stream (load_streams).

Este provider está pensado para trabajar con la ruta /stream
que llama a load_streams(event.url) cuando source == "LiveTV".
"""

from __future__ import annotations

from typing import List, Tuple
import re

import requests
from bs4 import BeautifulSoup
import urllib3

from ..base import BaseProvider
from ..models import Event, Stream

# Desactivar warnings de certificados raros de LiveTV
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# User-Agent para que LiveTV no nos bloquee tan fácil
UA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0"
}


class LiveTVProvider(BaseProvider):
    name = "LiveTV"

    # Página de próximos partidos (football)
    LIST_URL = "https://livetv.sx/enx/allupcomingsports/1/"

    # ==============================
    #   PUBLIC: fetch_events (index)
    # ==============================
    def fetch_events(self) -> List[Event]:
        """
        Descarga la lista de partidos de LiveTV y crea objetos Event
        SIN rellenar streams (Lazy Streams).
        """
        events: List[Event] = []

        try:
            resp = requests.get(
                self.LIST_URL,
                headers=UA_HEADERS,
                timeout=20,
                verify=False,
            )
            resp.raise_for_status()
        except Exception as e:
            print("[LiveTV] Error al descargar LIST_URL:", e)
            return events

        soup = BeautifulSoup(resp.text, "html.parser")

        # Cada partido está en un <td> con un <a class="bottomgray"> que apunta a /eventinfo/
        for a in soup.find_all("a", href=True, class_="bottomgray"):
            href = a["href"]
            if "eventinfo" not in href:
                continue

            event_url = href if href.startswith("http") else f"https://livetv.sx{href}"

            title = " ".join(a.stripped_strings)  # Ej: "Fluminense – Flamengo-RJ"
            home, away = self._split_teams(title)

            # Span con hora + liga:  <span class="evdesc">23:30 (Brazil. Serie A)</span>
            evdesc = a.find_next("span", class_="evdesc")
            raw_desc = evdesc.get_text(" ", strip=True) if evdesc else ""

            # Liga = texto entre paréntesis
            league = ""
            m = re.search(r"\((.*?)\)", raw_desc)
            if m:
                league = m.group(1).strip()

            # NO convertimos la hora a timestamp para evitar 1970-01-01
            # Devolvemos start_time=0 para que el filtro datetime muestre "-"
            start_time = 0

            event = Event(
                id=event_url,
                name=f"{home} vs {away}",
                url=event_url,
                league=league or "LiveTV",
                home=home,
                away=away,
                start_time=start_time,
                provider=self.name,
                streams=[],  # Lazy Streams: se llenan en load_streams()
            )
            events.append(event)

        # Eliminar duplicados por URL
        unique: List[Event] = []
        seen = set()
        for ev in events:
            if ev.url in seen:
                continue
            seen.add(ev.url)
            unique.append(ev)

        return unique

    # ==============================
    #   PUBLIC: cargar streams
    # ==============================
    def load_streams(self, event_url: str) -> List[Stream]:
        """
        Se llama desde /stream para obtener los streams de un evento LiveTV.
        Hace scraping de la página de eventinfo y, si es necesario, de webplayer.php.
        """
        return self._parse_event_streams(event_url)

    # ==============================
    #   PRIVATE: utils
    # ==============================
    def _split_teams(self, title: str) -> Tuple[str, str]:
        """Divide 'Home – Away' en (home, away)."""
        for sep in [" – ", " - ", " vs ", " Vs ", " v "]:
            if sep in title:
                h, a = title.split(sep, 1)
                return h.strip(), a.strip()
        return title.strip(), ""

    def _absolute_from(self, base: str, url: str) -> str:
        """Convierte urls relativas o //cdn a urls absolutas."""
        if url.startswith("http://") or url.startswith("https://"):
            return url
        if url.startswith("//"):
            return "https:" + url

        m = re.match(r"(https?://[^/]+)", base)
        root = m.group(1) if m else "https://livetv.sx"

        if url.startswith("/"):
            return root + url
        return root + "/" + url.lstrip("/")

    # ==============================
    #   PRIVATE: scraping de streams
    # ==============================
    def _parse_event_streams(self, event_url: str) -> List[Stream]:
        """
        1. Descarga la página de eventinfo.
        2. Busca urls de webplayer.php.
        3. De cada webplayer.php extrae el <iframe src="..."> real del stream.
        4. Si no encuentra webplayer, intenta directamente iframes en eventinfo.
        """
        streams: List[Stream] = []

        # ---- Paso 1: eventinfo ----
        try:
            resp = requests.get(
                event_url,
                headers=UA_HEADERS,
                timeout=20,
                verify=False,
            )
            resp.raise_for_status()
        except Exception as e:
            print("[LiveTV] Error al descargar eventinfo:", e)
            return streams

        soup = BeautifulSoup(resp.text, "html.parser")

        webplayer_urls = set()

        # a) enlaces directos a webplayer.php
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "webplayer.php" in href:
                webplayer_urls.add(self._absolute_from(event_url, href))

        # b) urls dentro de scripts
        for script in soup.find_all("script"):
            txt = script.string or ""
            for m in re.findall(r"(https?://[^'\" ]*webplayer\.php[^'\" ]*)", txt):
                webplayer_urls.add(m)

        # ---- Caso especial: sin webplayer, pero con iframe directo ----
        if not webplayer_urls:
            for iframe in soup.find_all("iframe", src=True):
                src = iframe["src"]
                full = self._absolute_from(event_url, src)
                streams.append(Stream(
                    name="Stream 1",
                    url=full,
                    source=self.name,
                    language=None,
                ))
            return streams

        # ---- Paso 2: visitar cada webplayer y extraer iframe ----
        for idx, wp_url in enumerate(sorted(webplayer_urls), start=1):
            try:
                wp_resp = requests.get(
                    wp_url,
                    headers=UA_HEADERS,
                    timeout=20,
                    verify=False,
                )
                wp_resp.raise_for_status()
            except Exception as e:
                print("[LiveTV] Error al descargar webplayer:", e)
                continue

            wp_soup = BeautifulSoup(wp_resp.text, "html.parser")
            iframe = wp_soup.find("iframe", src=True)
            if not iframe:
                continue

            src = iframe["src"]
            full = self._absolute_from(wp_url, src)

            streams.append(Stream(
                name=f"Stream {idx}",
                url=full,
                source=self.name,
                language=None,
            ))

        return streams

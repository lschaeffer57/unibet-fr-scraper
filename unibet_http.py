"""En-têtes + warm-up session Unibet (réduit les 403 datacenter ; proxy via env)."""

from __future__ import annotations

import aiohttp

# Même “empreinte” navigateur que des requêtes XHR depuis unibet.fr
UNIBET_REQUEST_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.unibet.fr/",
    "Origin": "https://www.unibet.fr",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "DNT": "1",
}


async def warm_unibet_session(session: aiohttp.ClientSession) -> None:
    """Page d’accueil pour cookies / jetons souvent exigés avant l’API zones/."""
    h = {
        **UNIBET_REQUEST_HEADERS,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Upgrade-Insecure-Requests": "1",
    }
    try:
        async with session.get(
            "https://www.unibet.fr/",
            headers=h,
            allow_redirects=True,
            timeout=aiohttp.ClientTimeout(total=25),
        ) as resp:
            await resp.read()
    except Exception:
        pass


def unibet_connector() -> aiohttp.TCPConnector:
    return aiohttp.TCPConnector(limit=64, limit_per_host=24, ttl_dns_cache=600)

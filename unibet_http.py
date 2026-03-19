"""En-têtes + warm-up session Unibet (réduit les 403 datacenter ; proxy HTTP, SOCKS ou Tor via env)."""

from __future__ import annotations

import asyncio
import os
from urllib.parse import quote

import aiohttp
from aiohttp.connector import BaseConnector

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
            proxy=aiohttp_per_request_proxy(),
            timeout=aiohttp.ClientTimeout(total=25),
        ) as resp:
            await resp.read()
    except Exception:
        pass


def use_tor() -> bool:
    v = os.environ.get("UNIBET_USE_TOR", "").strip().lower()
    return v in ("1", "true", "yes", "on")


def tor_socks_url() -> str:
    """SOCKS5 distant (résolution DNS côté proxy) — défaut port Tor."""
    return os.environ.get("TOR_SOCKS_PROXY", "socks5h://127.0.0.1:9050").strip()


def _nordvpn_socks_url_from_env() -> str | None:
    """Construit socks5h:// depuis les identifiants SOCKS NordVPN (évite une URL avec caractères spéciaux)."""
    host = os.environ.get("NORDVPN_SOCKS_HOST", "").strip()
    user = os.environ.get("NORDVPN_SOCKS_USER", "").strip()
    password = os.environ.get("NORDVPN_SOCKS_PASS", "").strip()
    if not (host and user and password):
        return None
    port = os.environ.get("NORDVPN_SOCKS_PORT", "1080").strip()
    u = quote(user, safe="")
    p = quote(password, safe="")
    return f"socks5h://{u}:{p}@{host}:{port}"


def effective_socks_proxy_url() -> str | None:
    """URL SOCKS si le connecteur doit passer par Tor, UNIBET_SOCKS_PROXY ou variables NordVPN."""
    if use_tor():
        return tor_socks_url()
    direct = os.environ.get("UNIBET_SOCKS_PROXY", "").strip()
    if direct:
        return direct
    return _nordvpn_socks_url_from_env()


def aiohttp_per_request_proxy() -> str | None:
    """Proxy HTTP(S) explicite (CONNECT) pour chaque GET — à utiliser sur VPS avec offre résidentielle."""
    if effective_socks_proxy_url() is not None:
        return None
    p = os.environ.get("UNIBET_PROXY", "").strip() or os.environ.get("UNIBET_HTTPS_PROXY", "").strip()
    return p or None


def unibet_trust_env() -> bool:
    """Désactivé avec SOCKS ou proxy explicite (évite de doubler HTTPS_PROXY / variables d’env)."""
    if effective_socks_proxy_url() is not None:
        return False
    if aiohttp_per_request_proxy() is not None:
        return False
    return True


async def unibet_aiohttp_get(session: aiohttp.ClientSession, url: str) -> str | None:
    """GET Unibet avec gestion d’erreurs homogène (utilisé par les scrapers async)."""
    try:
        async with session.get(
            url,
            proxy=aiohttp_per_request_proxy(),
            timeout=aiohttp.ClientTimeout(total=30),
        ) as response:
            response.raise_for_status()
            return await response.text()
    except aiohttp.ClientResponseError as e:
        print(f"Erreur HTTP {e.status} lors de la récupération de {url}: {e.message}")
        return None
    except asyncio.TimeoutError:
        print(f"Timeout lors de la récupération de {url}")
        return None
    except Exception as e:
        print(f"Erreur lors de la récupération de {url}: {e}")
        return None


def unibet_connector() -> BaseConnector:
    socks_url = effective_socks_proxy_url()
    if socks_url:
        try:
            from aiohttp_socks import ProxyConnector
        except ImportError as e:
            raise ImportError(
                "Proxy SOCKS requis : installe aiohttp-socks (déjà dans requirements.txt)."
            ) from e
        return ProxyConnector.from_url(
            socks_url,
            limit=64,
            limit_per_host=24,
            ttl_dns_cache=600,
        )
    return aiohttp.TCPConnector(limit=64, limit_per_host=24, ttl_dns_cache=600)

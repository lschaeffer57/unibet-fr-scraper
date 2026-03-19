"""Chromium + Playwright — stratégie alignée sur Unibet.PDF (V120) : une page, /sport, puis fetch().then(r => r.json())."""

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

import aiohttp

from unibet_http import (
    UNIBET_REQUEST_HEADERS,
    unibet_connector,
    unibet_trust_env,
    warm_unibet_session,
)

# Même UA que le PDF (chaîne complète type Chrome Windows 123).
DEFAULT_PDF_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
)


def use_playwright() -> bool:
    v = os.environ.get("UNIBET_USE_PLAYWRIGHT", "").strip().lower()
    return v in ("1", "true", "yes", "on")


class PlaywrightFetcher:
    """Une seule page (comme le PDF), réchauffée sur /sport ; tous les API passent par evaluate sur cette page."""

    def __init__(self) -> None:
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._eval_lock = asyncio.Lock()

    async def __aenter__(self) -> PlaywrightFetcher:
        from playwright.async_api import async_playwright

        headless = os.environ.get("UNIBET_PLAYWRIGHT_HEADLESS", "1").strip().lower() not in (
            "0",
            "false",
            "no",
        )
        ua = os.environ.get("UNIBET_PLAYWRIGHT_UA", DEFAULT_PDF_USER_AGENT).strip() or DEFAULT_PDF_USER_AGENT
        proxy_url = os.environ.get("UNIBET_PLAYWRIGHT_PROXY", "").strip()
        # PDF : chromium.launch(headless=True) sans args Chromium.
        launch_kwargs: dict = {"headless": headless}
        extra = os.environ.get("UNIBET_PLAYWRIGHT_CHROMIUM_ARGS", "").strip()
        if extra:
            launch_kwargs["args"] = [a.strip() for a in extra.split(",") if a.strip()]
        if proxy_url:
            launch_kwargs["proxy"] = {"server": proxy_url}

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(**launch_kwargs)
        # PDF : new_context(user_agent=…) uniquement (pas locale / fuseau).
        if os.environ.get("UNIBET_PLAYWRIGHT_LOCALE_FR", "").strip().lower() in ("1", "true", "yes"):
            self._context = await self._browser.new_context(
                user_agent=ua,
                locale="fr-FR",
                timezone_id="Europe/Paris",
            )
        else:
            self._context = await self._browser.new_context(user_agent=ua)

        timeout_ms = int(os.environ.get("UNIBET_PLAYWRIGHT_TIMEOUT_MS", "90000").strip() or "90000")
        self._context.set_default_timeout(timeout_ms)

        self._page = await self._context.new_page()
        # PDF : goto /sport, mouse.move(100,100), sleep(2) ; try/except pass
        try:
            await self._page.goto(
                "https://www.unibet.fr/sport",
                wait_until="domcontentloaded",
                timeout=60000,
            )
            await self._page.mouse.move(100, 100)
            await asyncio.sleep(
                float(os.environ.get("UNIBET_PLAYWRIGHT_WARMUP_SLEEP", "2").strip() or "2")
            )
        except Exception:
            pass
        return self

    async def __aexit__(self, *args: object) -> None:
        if self._page is not None:
            await self._page.close()
            self._page = None
        if self._context is not None:
            await self._context.close()
        if self._browser is not None:
            await self._browser.close()
        if self._playwright is not None:
            await self._playwright.stop()

    async def get_text(self, url: str) -> str | None:
        """Comme le PDF : fetch(url).then(r=>r.json()) avec catch → {} ; renvoie le JSON sérialisé en texte."""
        if self._page is None:
            return None
        try:
            async with self._eval_lock:
                result = await self._page.evaluate(
                    """async (url) => {
                        try {
                            const r = await fetch(url);
                            const data = await r.json().catch(() => ({}));
                            return { ok: r.ok, status: r.status, text: JSON.stringify(data) };
                        } catch (e) {
                            return { ok: false, status: 0, text: "{}" };
                        }
                    }""",
                    url,
                )
            if not result.get("ok"):
                st = result.get("status")
                print(
                    f"Erreur HTTP {st} lors de la récupération de {url}: Forbidden"
                    if st == 403
                    else f"Erreur HTTP {st} lors de la récupération de {url}"
                )
                return None
            return result.get("text")
        except Exception as e:
            print(f"Erreur lors de la récupération de {url}: {e}")
            return None


@asynccontextmanager
async def unibet_client_session() -> AsyncIterator[aiohttp.ClientSession | PlaywrightFetcher]:
    """Session aiohttp (défaut) ou fetcher Playwright si UNIBET_USE_PLAYWRIGHT=1."""
    if use_playwright():
        async with PlaywrightFetcher() as pw:
            yield pw
        return
    connector = unibet_connector()
    async with aiohttp.ClientSession(
        headers=UNIBET_REQUEST_HEADERS,
        connector=connector,
        timeout=aiohttp.ClientTimeout(total=30),
        trust_env=unibet_trust_env(),
    ) as session:
        await warm_unibet_session(session)
        yield session

"""Automação opcional de navegador local por Playwright, com perfil isolado."""

from __future__ import annotations

from pathlib import Path


class BrowserTool:
    """Controla um Chromium local somente quando a ferramenta é solicitada pelo agente."""

    def __init__(self, profile_dir: str | Path, headless: bool = False):
        self.profile_dir = Path(profile_dir).expanduser()
        self.headless = headless
        self._playwright = None
        self._context = None
        self._page = None

    def _ensure_page(self):
        if self._page:
            return self._page
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError(
                "O controle de navegador requer Playwright. Instale as dependências e execute "
                "`python3 -m playwright install chromium` uma vez."
            ) from exc
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self._playwright = sync_playwright().start()
        self._context = self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.profile_dir),
            headless=self.headless,
            accept_downloads=False,
        )
        self._page = self._context.pages[0] if self._context.pages else self._context.new_page()
        self._page.set_default_timeout(15_000)
        return self._page

    @staticmethod
    def _summary(page) -> str:
        title = page.title()
        body = page.locator("body").inner_text(timeout=10_000).strip()
        clipped = body[:8_000] + ("..." if len(body) > 8_000 else "")
        return f"URL: {page.url}\nTítulo: {title}\n\n{clipped or '(página sem texto visível)'}"

    def navigate(self, url: str) -> str:
        if not url.startswith(("https://", "http://")):
            raise ValueError("Use uma URL http:// ou https:// explícita.")
        page = self._ensure_page()
        page.goto(url, wait_until="domcontentloaded")
        return self._summary(page)

    def read(self) -> str:
        return self._summary(self._ensure_page())

    def click(self, selector: str) -> str:
        page = self._ensure_page()
        page.locator(selector).first.click()
        page.wait_for_timeout(250)
        return self._summary(page)

    def type(self, selector: str, text: str) -> str:
        page = self._ensure_page()
        page.locator(selector).first.fill(text)
        return f"Campo preenchido para o seletor: {selector}"

    def close(self) -> str:
        if self._context:
            self._context.close()
        if self._playwright:
            self._playwright.stop()
        self._context = None
        self._playwright = None
        self._page = None
        return "Sessão local do navegador encerrada."

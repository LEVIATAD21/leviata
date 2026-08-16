"""Auditoria web passiva e defensiva para alvos autorizados."""
from __future__ import annotations

import json
import socket
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests


class SecurityError(RuntimeError):
    """Erro controlado de escopo ou auditoria de segurança."""


class SecurityToolkit:
    """Executa apenas verificações GET passivas em loopback ou hosts aprovados."""

    loopback_hosts = {"localhost", "127.0.0.1", "::1"}

    def __init__(self, workspace: str | Path, allowed_hosts: set[str] | None = None, session=None):
        self.workspace = Path(workspace).expanduser().resolve()
        self.allowed_hosts = {host.lower().strip() for host in (allowed_hosts or set()) if host.strip()}
        self.session = session or requests.Session()

    def _validate_url(self, url: str) -> tuple[str, str]:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise SecurityError("Use uma URL http(s) completa para um alvo autorizado.")
        host = parsed.hostname.lower()
        if host not in self.loopback_hosts and host not in self.allowed_hosts:
            raise SecurityError("Por segurança, o alvo precisa ser loopback ou estar em allowed_hosts explícitos.")
        return parsed.geturl(), host

    @staticmethod
    def _headers_report(headers) -> dict[str, object]:
        expected = {
            "content-security-policy": "CSP ausente",
            "x-content-type-options": "X-Content-Type-Options ausente",
            "x-frame-options": "X-Frame-Options ausente",
            "referrer-policy": "Referrer-Policy ausente",
        }
        lower = {key.lower(): value for key, value in headers.items()}
        findings = [{"header": key, "message": message} for key, message in expected.items() if key not in lower]
        return {"present": {key: lower[key] for key in expected if key in lower}, "findings": findings}

    def audit(self, url: str) -> str:
        target, host = self._validate_url(url)
        try:
            response = self.session.get(target, timeout=15, allow_redirects=True, headers={"User-Agent": "KAWA-AI-defensive-audit/1.0"})
        except requests.RequestException as exc:
            raise SecurityError(f"Não foi possível acessar o alvo autorizado: {exc}") from exc
        report = {
            "target": target,
            "resolved_url": response.url,
            "host": host,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status_code": response.status_code,
            "redirects": len(response.history),
            "headers": self._headers_report(response.headers),
            "tls": response.url.startswith("https://"),
            "cookies": [],
            "forms": 0,
            "notes": [
                "Auditoria passiva: não executa payloads, não envia formulários e não tenta autenticação.",
                "Ausência de cabeçalho é um sinal para revisão, não prova isolada de vulnerabilidade.",
            ],
        }
        for cookie in response.cookies:
            report["cookies"].append({
                "name": cookie.name,
                "secure": bool(cookie.secure),
                "has_expires": cookie.expires is not None,
                "domain": cookie.domain,
                "path": cookie.path,
            })
        content_type = response.headers.get("content-type", "")
        if "html" in content_type:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text[:2_000_000], "html.parser")
            report["forms"] = len(soup.find_all("form"))
            report["mixed_content_candidates"] = [
                tag.get("src") or tag.get("href")
                for tag in soup.find_all(src=True) + soup.find_all(href=True)
                if str(tag.get("src") or tag.get("href")).startswith("http://")
            ][:50]
        output_dir = self.workspace / "kawa-quality"
        output_dir.mkdir(parents=True, exist_ok=True)
        output = output_dir / f"web-audit-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return json.dumps({"report": str(output), "summary": report}, ensure_ascii=False, indent=2)

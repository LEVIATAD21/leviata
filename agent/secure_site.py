"""Ciclo local de desenvolvimento seguro para sites criados pelo Leviatã.

O módulo cria somente um projeto de referência dentro do workspace, aplica
controles básicos de hardening e registra evidências de verificações estáticas.
Ele não publica, não abre portas públicas e não executa ataques de rede.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class SecureSiteError(RuntimeError):
    """Erro do ciclo local de site seguro."""


class SecureSiteCycle:
    """Cria, verifica e retesta um site local com critérios explícitos."""

    _blocked_patterns = (
        ("unsafe_dynamic_execution", re.compile(r"\b(?:eval|exec)\s*\(")),
        ("unsafe_html_injection", re.compile(r"\binnerHTML\s*=")),
        ("unsafe_shell_execution", re.compile(r"shell\s*=\s*True")),
        ("public_bind", re.compile(r"(?:0\.0\.0\.0|::)")),
        ("embedded_secret", re.compile(r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['\"][^'\"]{8,}")),
    )
    _adversarial_patterns = (
        ("client_sensitive_storage", re.compile(r"(?i)(?:localStorage|sessionStorage)\.(?:setItem|getItem)\([^\n]{0,160}(?:token|password|secret|session)"), "Simula abuso de sessão no navegador; não armazene dados sensíveis em localStorage/sessionStorage."),
        ("insecure_external_resource", re.compile(r"(?i)(?:src|href|action)\s*=\s*['\"]http://"), "Simula interceptação de tráfego; use apenas recursos HTTPS e transporte seguro."),
        ("permissive_cors", re.compile(r"(?i)access-control-allow-origin[^\n]{0,80}\*"), "Simula abuso entre origens; restrinja CORS aos domínios necessários."),
        ("missing_rate_limit_contract", re.compile(r"(?i)(?:login|signin|password-reset|redefinir-senha)[^\n]{0,160}"), "Fluxo sensível identificado: confirme limitação de tentativas e mensagens de erro não enumeráveis no backend real."),
    )
    _adversarial_scenarios = (
        ("input_and_template_abuse", "Procura execução dinâmica e injeção HTML que poderiam transformar entrada em código."),
        ("session_and_secret_exposure", "Procura segredos embutidos e armazenamento inseguro de credenciais ou sessão."),
        ("transport_and_origin_abuse", "Procura recursos HTTP e configuração permissiva de origem cruzada."),
        ("public_service_exposure", "Confirma que o servidor de referência não escuta em interfaces públicas."),
    )

    def __init__(self, workspace: str | Path):
        self.workspace = Path(workspace).expanduser().resolve()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _target(self, site_name: str) -> Path:
        slug = re.sub(r"[^a-z0-9-]+", "-", site_name.casefold()).strip("-") or "site-seguro"
        target = (self.workspace / "leviata-secure-sites" / slug).resolve()
        try:
            target.relative_to(self.workspace)
        except ValueError as exc:
            raise SecureSiteError("O site precisa permanecer dentro do workspace autorizado.") from exc
        return target

    def _write_reference_site(self, target: Path, title: str) -> None:
        target.mkdir(parents=True, exist_ok=True)
        (target / "index.html").write_text(
            f"""<!doctype html>
<html lang=\"pt-BR\">
  <head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
    <meta name=\"referrer\" content=\"no-referrer\">
    <title>{title}</title>
    <link rel=\"stylesheet\" href=\"/styles.css\">
  </head>
  <body>
    <main>
      <p class=\"eyebrow\">Projeto local verificado</p>
      <h1>{title}</h1>
      <p>Referência estática criada localmente pelo ciclo seguro do Leviatã.</p>
    </main>
  </body>
</html>
""",
            encoding="utf-8",
        )
        (target / "styles.css").write_text(
            """* { box-sizing: border-box; }
body { margin: 0; min-height: 100vh; display: grid; place-items: center; background: #09111f; color: #edf4ff; font: 16px/1.5 system-ui, sans-serif; }
main { width: min(92vw, 720px); padding: 48px; border: 1px solid #27415f; border-radius: 20px; background: #0f1d30; }
.eyebrow { color: #76d4b1; font-weight: 700; text-transform: uppercase; letter-spacing: .12em; }
""",
            encoding="utf-8",
        )
        (target / "server.py").write_text(
            """from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent.resolve()

class LocalOnlyHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("Content-Security-Policy", "default-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        super().end_headers()

if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 0), LocalOnlyHandler).serve_forever()
""",
            encoding="utf-8",
        )
        (target / "SECURITY.md").write_text(
            """# Controles locais

Este site não é publicado pelo ciclo. O servidor de referência escuta somente em `127.0.0.1` e usa porta efêmera. Antes de qualquer distribuição, execute novamente o ciclo de verificação e revise dependências, autenticação e variáveis de ambiente do projeto real.
""",
            encoding="utf-8",
        )

    def _evidence_dir(self, target: Path) -> Path:
        path = target / "leviata-secure-cycle"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def verify(self, target_path: str | Path) -> dict[str, Any]:
        target = Path(target_path).expanduser().resolve()
        try:
            target.relative_to(self.workspace)
        except ValueError as exc:
            raise SecureSiteError("A verificação só pode analisar site dentro do workspace.") from exc
        required = {"index.html", "styles.css", "server.py", "SECURITY.md"}
        findings: list[dict[str, str]] = []
        for filename in sorted(required):
            if not (target / filename).is_file():
                findings.append({"kind": "missing_required_file", "file": filename, "detail": "Arquivo obrigatório ausente."})
        for item in target.rglob("*"):
            if "leviata-secure-cycle" in item.parts or not item.is_file() or item.is_symlink():
                continue
            try:
                text = item.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for kind, pattern in self._blocked_patterns:
                if pattern.search(text):
                    findings.append({"kind": kind, "file": str(item.relative_to(target)), "detail": "Padrão bloqueado pelo ciclo local."})
            for kind, pattern, remediation in self._adversarial_patterns:
                if pattern.search(text):
                    findings.append({"kind": kind, "file": str(item.relative_to(target)), "detail": remediation})
        server = (target / "server.py")
        if server.exists():
            server_text = server.read_text(encoding="utf-8", errors="ignore")
            for header in ("Content-Security-Policy", "X-Content-Type-Options", "X-Frame-Options", "Referrer-Policy", "Permissions-Policy"):
                if header not in server_text:
                    findings.append({"kind": "missing_security_header", "file": "server.py", "detail": f"Cabeçalho ausente: {header}"})
            if '"127.0.0.1"' not in server_text:
                findings.append({"kind": "local_only_bind_missing", "file": "server.py", "detail": "Servidor deve escutar somente em 127.0.0.1."})
        evidence = {
            "created_at": self._now(),
            "target": str(target),
            "method": "local_static_secure_site_gate",
            "status": "passed" if not findings else "blocked",
            "finding_count": len(findings),
            "findings": findings,
            "adversarial_simulations": [
                {
                    "scenario": name,
                    "purpose": purpose,
                    "status": "blocked" if findings else "passed",
                }
                for name, purpose in self._adversarial_scenarios
            ],
            "publication": "not_requested_and_not_performed",
        }
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        evidence_file = self._evidence_dir(target) / f"verification-{stamp}.json"
        evidence_file.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        evidence["evidence_file"] = str(evidence_file)
        return evidence

    def run(self, site_name: str = "site-seguro", title: str | None = None, maximum_cycles: int = 3) -> str:
        target = self._target(site_name)
        self._write_reference_site(target, title or "Site seguro local")
        attempts: list[dict[str, Any]] = []
        for cycle in range(1, max(1, min(maximum_cycles, 5)) + 1):
            evidence = self.verify(target)
            attempts.append({"cycle": cycle, "status": evidence["status"], "evidence_file": evidence["evidence_file"]})
            if evidence["status"] == "passed":
                return json.dumps({"status": "passed", "target": str(target), "cycles": attempts, "publication": "not_performed"}, ensure_ascii=False)
            break
        return json.dumps({"status": "blocked", "target": str(target), "cycles": attempts, "publication": "not_performed"}, ensure_ascii=False)

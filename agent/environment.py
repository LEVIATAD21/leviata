"""Diagnóstico de ambiente (Linux Mint vs Termux sem root) e transporte opt-in para tarefas de pesquisa."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


class EnvironmentInspector:
    """Verifica restrições de ambiente e se adapta a sistemas sem privilégios de root."""

    @staticmethod
    def inspect() -> dict[str, str | bool]:
        is_termux = "TERMUX_VERSION" in os.environ or os.path.exists("/data/data/com.termux")
        has_sudo = shutil.which("sudo") is not None
        can_root = False
        if has_sudo and not is_termux:
            try:
                res = subprocess.run(["sudo", "-n", "true"], capture_output=True, timeout=2)
                can_root = (res.returncode == 0)
            except Exception:
                can_root = False

        home = Path.home()
        return {
            "platform": "termux" if is_termux else "linux_mint_or_standard",
            "home": str(home),
            "root_privileges": can_root,
            "termux_environment": is_termux,
            "storage_writable": os.access(str(home), os.W_OK),
        }

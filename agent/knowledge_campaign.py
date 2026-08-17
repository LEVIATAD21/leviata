"""Campanha local, progressiva e auditável de testes de conhecimento.

O módulo não inventa conhecimento em massa nem faz chamadas de rede. Ele organiza
domínios, limita lotes, valida itens fornecidos por fontes rastreáveis e registra
somente itens únicos e avaliáveis como progresso válido.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class KnowledgeCampaignError(RuntimeError):
    """Erro de validação da campanha de conhecimento."""


class KnowledgeCampaign:
    """Mantém uma campanha local com meta por domínio e evidências por lote."""

    TARGET_PER_DOMAIN = 2_000_000
    MAX_BATCH_SIZE = 1_000
    DOMAINS = {
        "GEN": "Conhecimento geral e interdisciplinar",
        "FOR": "Sistemas formais e quantitativos",
        "NAT": "Ciências naturais",
        "ENG": "Engenharia e tecnologia",
        "CMP": "Computação e informação",
        "MED": "Medicina e saúde",
        "AGR": "Agricultura, veterinária e alimentos",
        "SOC": "Ciências sociais",
        "ECO": "Economia, negócios e trabalho",
        "LAW": "Direito, cidadania e políticas públicas",
        "HIS": "História, patrimônio e arqueologia",
        "GEO": "Geografia, território e urbanismo",
        "HUM": "Filosofia, psicologia, religião e ética",
        "LAN": "Linguagens, literatura e comunicação",
        "EDU": "Educação e aprendizagem",
        "ART": "Artes, design e criação",
        "COM": "Comunicação, jornalismo e informação",
        "SPO": "Esporte, lazer e bem-estar",
        "PRA": "Conhecimentos práticos e profissões",
        "THE": "Teorias e campos emergentes",
    }
    REQUIRED_FIELDS = ("domain", "subdomain", "modality", "prompt", "expected", "source_url")
    _VALID_URL = re.compile(r"^https://[^\s]+$", re.IGNORECASE)

    def __init__(self, root: str | Path | None = None):
        self.root = Path(root or Path.home() / ".leviata-ai" / "knowledge-campaign").expanduser().resolve()
        self.manifest_path = self.root / "campaign.json"
        self.items_path = self.root / "validated-items.jsonl"
        self.batches_dir = self.root / "batches"

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def initialize(self, target_per_domain: int | None = None) -> dict[str, Any]:
        if self.manifest_path.exists():
            return self.status()
        target = int(target_per_domain or self.TARGET_PER_DOMAIN)
        if target < 1:
            raise KnowledgeCampaignError("A meta por domínio deve ser maior que zero.")
        self.root.mkdir(parents=True, exist_ok=True)
        self.batches_dir.mkdir(parents=True, exist_ok=True)
        manifest = {
            "version": 1,
            "created_at": self._now(),
            "target_per_domain": target,
            "domains": {code: {"label": label, "validated": 0} for code, label in self.DOMAINS.items()},
            "batches": [],
        }
        self._write_manifest(manifest)
        return self.status()

    def _manifest(self) -> dict[str, Any]:
        if not self.manifest_path.exists():
            self.initialize()
        try:
            return json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise KnowledgeCampaignError("O manifesto local da campanha está inválido.") from exc

    def _write_manifest(self, manifest: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        temporary = self.manifest_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.manifest_path)

    def status(self) -> dict[str, Any]:
        manifest = self._manifest()
        target = manifest["target_per_domain"]
        domains = [
            {
                "code": code,
                "label": item["label"],
                "validated": item["validated"],
                "remaining": max(0, target - item["validated"]),
                "target": target,
            }
            for code, item in manifest["domains"].items()
        ]
        return {
            "status": "ready",
            "root": str(self.root),
            "target_per_domain": target,
            "domain_count": len(domains),
            "validated_total": sum(item["validated"] for item in domains),
            "batches_recorded": len(manifest["batches"]),
            "domains": domains,
        }

    def preview_batch(self, domain: str = "ALL", requested: int = 250) -> dict[str, Any]:
        manifest = self._manifest()
        requested = int(requested)
        if not 1 <= requested <= self.MAX_BATCH_SIZE:
            raise KnowledgeCampaignError(f"O lote precisa ter entre 1 e {self.MAX_BATCH_SIZE} itens.")
        selected = list(manifest["domains"]) if domain.upper() == "ALL" else [domain.upper()]
        unknown = [code for code in selected if code not in manifest["domains"]]
        if unknown:
            raise KnowledgeCampaignError(f"Domínio desconhecido: {', '.join(unknown)}.")
        target = manifest["target_per_domain"]
        plan = []
        for code in selected:
            validated = manifest["domains"][code]["validated"]
            plan.append({
                "domain": code,
                "label": manifest["domains"][code]["label"],
                "requested": requested,
                "planned": min(requested, max(0, target - validated)),
                "remaining_before": max(0, target - validated),
            })
        return {
            "status": "preview",
            "network": "not_used",
            "generation": "not_performed",
            "evaluation": "not_performed",
            "plans": plan,
            "acceptance_contract": list(self.REQUIRED_FIELDS),
        }

    @staticmethod
    def _signature(item: dict[str, Any]) -> str:
        canonical = "\x1f".join(
            " ".join(str(item[field]).casefold().split())
            for field in ("domain", "subdomain", "modality", "prompt", "expected")
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _known_signatures(self) -> set[str]:
        if not self.items_path.exists():
            return set()
        signatures: set[str] = set()
        for line in self.items_path.read_text(encoding="utf-8").splitlines():
            try:
                signatures.add(json.loads(line)["signature"])
            except (KeyError, json.JSONDecodeError):
                continue
        return signatures

    def record_batch(self, domain: str, candidates: list[dict[str, Any]], evaluator: str = "external_or_deterministic") -> dict[str, Any]:
        manifest = self._manifest()
        code = domain.upper()
        if code not in manifest["domains"]:
            raise KnowledgeCampaignError(f"Domínio desconhecido: {domain}.")
        if not candidates:
            raise KnowledgeCampaignError("O lote não possui candidatos para avaliação.")
        if len(candidates) > self.MAX_BATCH_SIZE:
            raise KnowledgeCampaignError(f"O lote excede o máximo de {self.MAX_BATCH_SIZE} candidatos.")

        known = self._known_signatures()
        accepted: list[dict[str, Any]] = []
        rejected: list[dict[str, str]] = []
        target = manifest["target_per_domain"]
        remaining = max(0, target - manifest["domains"][code]["validated"])
        for position, raw in enumerate(candidates, start=1):
            if not isinstance(raw, dict):
                rejected.append({"position": str(position), "reason": "candidate_not_object"})
                continue
            missing = [field for field in self.REQUIRED_FIELDS if not str(raw.get(field, "")).strip()]
            if missing:
                rejected.append({"position": str(position), "reason": f"missing:{','.join(missing)}"})
                continue
            item = {field: " ".join(str(raw[field]).split()) for field in self.REQUIRED_FIELDS}
            if item["domain"].upper() != code:
                rejected.append({"position": str(position), "reason": "domain_mismatch"})
                continue
            if not self._VALID_URL.fullmatch(item["source_url"]):
                rejected.append({"position": str(position), "reason": "source_requires_https"})
                continue
            signature = self._signature(item)
            if signature in known:
                rejected.append({"position": str(position), "reason": "duplicate"})
                continue
            if len(accepted) >= remaining:
                rejected.append({"position": str(position), "reason": "target_already_reached"})
                continue
            known.add(signature)
            accepted.append({**item, "signature": signature, "evaluated_by": evaluator, "validated_at": self._now()})

        self.root.mkdir(parents=True, exist_ok=True)
        if accepted:
            with self.items_path.open("a", encoding="utf-8") as handle:
                for item in accepted:
                    handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
            manifest["domains"][code]["validated"] += len(accepted)
        batch_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + f"-{code.lower()}"
        evidence = {
            "batch_id": batch_id,
            "created_at": self._now(),
            "domain": code,
            "evaluator": evaluator,
            "received": len(candidates),
            "accepted": len(accepted),
            "rejected": rejected,
            "network": "not_used",
            "generation": "provided_candidates_only",
        }
        self.batches_dir.mkdir(parents=True, exist_ok=True)
        evidence_path = self.batches_dir / f"{batch_id}.json"
        evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        manifest["batches"].append({"batch_id": batch_id, "domain": code, "evidence_file": str(evidence_path), "accepted": len(accepted)})
        self._write_manifest(manifest)
        return {**evidence, "evidence_file": str(evidence_path), "status": self.status()}

    def render_status(self) -> str:
        status = self.status()
        lines = [
            "=== Campanha de conhecimento Leviatã ===",
            f"Domínios: {status['domain_count']} | Meta por domínio: {status['target_per_domain']:,}",
            f"Itens validados: {status['validated_total']:,} | Lotes registrados: {status['batches_recorded']}",
        ]
        lines.extend(f"- {item['code']}: {item['validated']:,}/{item['target']:,} — {item['label']}" for item in status["domains"])
        return "\n".join(lines)

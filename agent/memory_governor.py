"""Orçamento adaptativo de memória para o Leviatã.

O módulo não particiona fisicamente a RAM e não altera a swap do dispositivo.
Ele calcula um limite operacional conservador para reduzir pressão de memória e
recomenda quantos trabalhadores locais podem iniciar simultaneamente.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path


MiB = 1024 * 1024


@dataclass(frozen=True)
class MemoryPlan:
    profile: str
    total_mib: int
    available_mib: int
    swap_total_mib: int
    swap_free_mib: int
    agent_budget_mib: int
    system_reserve_mib: int
    runtime_budget_mib: int
    active_workers: int
    per_worker_mib: int
    recommended_batch_size: int
    recommended_context_chars: int
    status: str
    note: str

    def as_dict(self) -> dict[str, int | str]:
        return asdict(self)


class MemoryGovernor:
    """Calcula um orçamento de trabalho local sem modificar o kernel ou a swap."""

    LOW_RAM_THRESHOLD_MIB = 12 * 1024
    SERVER_DETECTION_THRESHOLD_MIB = 16 * 1024
    HIGH_RAM_AGENT_CAP_MIB = 6 * 1024
    MIN_FREE_SYSTEM_MIB = 512
    MIN_WORKER_MIB = 512
    PREFERRED_WORKER_MIB = 1024
    DEFAULT_BATCH_SIZE = 250
    REDUCED_BATCH_SIZE = 50
    DEFAULT_CONTEXT_CHARS = 6_000
    REDUCED_CONTEXT_CHARS = 4_000
    THROTTLED_CONTEXT_CHARS = 2_000

    @staticmethod
    def resolve_profile(profile: str = "auto", total_mib: int = 0) -> str:
        """Classifica automaticamente servidor acima de 16 GiB, salvo perfil explícito."""
        requested = (profile or "auto").strip().casefold()
        if requested == "auto":
            requested = os.environ.get("KAWA_RESOURCE_PROFILE", "auto").strip().casefold()
        if requested == "auto":
            return "server" if total_mib > MemoryGovernor.SERVER_DETECTION_THRESHOLD_MIB else "desktop"
        aliases = {"pc": "desktop", "pessoal": "desktop", "notebook": "desktop", "server": "server", "servidor": "server"}
        resolved = aliases.get(requested, requested)
        if resolved not in {"desktop", "server"}:
            raise ValueError("Perfil inválido: use auto, desktop ou server.")
        return resolved

    @staticmethod
    def _meminfo() -> dict[str, int]:
        values: dict[str, int] = {}
        path = Path("/proc/meminfo")
        if not path.exists():
            return values
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            key, _, raw = line.partition(":")
            tokens = raw.split()
            if tokens and tokens[0].isdigit():
                values[key] = int(tokens[0]) * 1024
        return values

    @classmethod
    def inspect(cls) -> dict[str, int]:
        info = cls._meminfo()
        total = info.get("MemTotal", 0)
        available = info.get("MemAvailable", info.get("MemFree", 0))
        return {
            "total_mib": total // MiB,
            "available_mib": available // MiB,
            "swap_total_mib": info.get("SwapTotal", 0) // MiB,
            "swap_free_mib": info.get("SwapFree", 0) // MiB,
        }

    @classmethod
    def plan_from_metrics(
        cls,
        total_mib: int,
        available_mib: int,
        workers_requested: int = 4,
        swap_total_mib: int = 0,
        swap_free_mib: int = 0,
        profile: str = "auto",
    ) -> MemoryPlan:
        resolved_profile = cls.resolve_profile(profile, total_mib)
        if total_mib <= 0:
            return MemoryPlan(resolved_profile, 0, max(0, available_mib), max(0, swap_total_mib), max(0, swap_free_mib), 0, 0, 0, 0, 0, 0, cls.THROTTLED_CONTEXT_CHARS, "unavailable", "Não foi possível identificar a memória do dispositivo.")
        requested = max(1, int(workers_requested))
        if resolved_profile == "server":
            # Em servidor declarado, privilegia throughput sem consumir os últimos 10% do host.
            agent_budget = total_mib - max(1024, total_mib // 10)
        else:
            agent_budget = total_mib // 2 if total_mib <= cls.LOW_RAM_THRESHOLD_MIB else cls.HIGH_RAM_AGENT_CAP_MIB
        agent_budget = min(agent_budget, total_mib)
        system_reserve = max(0, total_mib - agent_budget)
        runtime_budget = min(agent_budget, max(0, available_mib - cls.MIN_FREE_SYSTEM_MIB))
        if runtime_budget < cls.MIN_WORKER_MIB:
            return MemoryPlan(resolved_profile, total_mib, max(0, available_mib), max(0, swap_total_mib), max(0, swap_free_mib), agent_budget, system_reserve, runtime_budget, 0, 0, 0, cls.THROTTLED_CONTEXT_CHARS, "throttled", "Memória disponível insuficiente; mantenha a tarefa registrada e não inicie novos trabalhadores até liberar recursos.")
        worker_cap = max(1, runtime_budget // cls.PREFERRED_WORKER_MIB)
        active_workers = min(requested, worker_cap)
        under_pressure = available_mib * 4 < total_mib
        if under_pressure:
            active_workers = max(1, active_workers // 2)
        per_worker = runtime_budget // active_workers
        batch_size = cls.REDUCED_BATCH_SIZE if under_pressure else cls.DEFAULT_BATCH_SIZE
        context_chars = cls.REDUCED_CONTEXT_CHARS if under_pressure else cls.DEFAULT_CONTEXT_CHARS
        return MemoryPlan(
            resolved_profile,
            total_mib,
            max(0, available_mib),
            max(0, swap_total_mib),
            max(0, swap_free_mib),
            agent_budget,
            system_reserve,
            runtime_budget,
            active_workers,
            per_worker,
            batch_size,
            context_chars,
            "reduced" if under_pressure else "ready",
            "Carga do Leviatã reduzida gradualmente por pressão de memória; RAM e swap não foram particionadas nem alteradas." if under_pressure else "Orçamento consultivo: a RAM e a swap não foram particionadas nem alteradas.",
        )

    @classmethod
    def plan(cls, workers_requested: int = 4, profile: str = "auto") -> MemoryPlan:
        metrics = cls.inspect()
        return cls.plan_from_metrics(workers_requested=workers_requested, profile=profile, **metrics)

    @classmethod
    def render(cls, workers_requested: int = 4, profile: str = "auto") -> str:
        plan = cls.plan(workers_requested, profile)
        return (
            "=== Orçamento de memória Leviatã ===\n"
            f"Perfil: {plan.profile}\n"
            f"RAM total: {plan.total_mib} MiB | disponível agora: {plan.available_mib} MiB\n"
            f"Orçamento da IA: {plan.agent_budget_mib} MiB | reserva do sistema: {plan.system_reserve_mib} MiB\n"
            f"Orçamento seguro agora: {plan.runtime_budget_mib} MiB | trabalhadores: {plan.active_workers} | por trabalhador: {plan.per_worker_mib} MiB\n"
            f"Lote recomendado: {plan.recommended_batch_size} | contexto recuperado: {plan.recommended_context_chars} caracteres\n"
            f"Swap: {plan.swap_free_mib}/{plan.swap_total_mib} MiB livre | estado: {plan.status}\n"
            f"Nota: {plan.note}"
        )

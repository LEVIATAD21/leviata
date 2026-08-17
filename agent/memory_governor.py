"""Orçamento adaptativo de memória para o KAWA-AI.

O módulo não particiona fisicamente a RAM e não altera a swap do dispositivo.
Ele calcula um limite operacional conservador para reduzir pressão de memória e
recomenda quantos trabalhadores locais podem iniciar simultaneamente.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path


MiB = 1024 * 1024


@dataclass(frozen=True)
class MemoryPlan:
    total_mib: int
    available_mib: int
    swap_total_mib: int
    swap_free_mib: int
    agent_budget_mib: int
    system_reserve_mib: int
    runtime_budget_mib: int
    active_workers: int
    per_worker_mib: int
    status: str
    note: str

    def as_dict(self) -> dict[str, int | str]:
        return asdict(self)


class MemoryGovernor:
    """Calcula um orçamento de trabalho local sem modificar o kernel ou a swap."""

    LOW_RAM_THRESHOLD_MIB = 12 * 1024
    HIGH_RAM_AGENT_CAP_MIB = 6 * 1024
    MIN_FREE_SYSTEM_MIB = 512
    MIN_WORKER_MIB = 512
    PREFERRED_WORKER_MIB = 1024

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
    ) -> MemoryPlan:
        if total_mib <= 0:
            return MemoryPlan(0, max(0, available_mib), max(0, swap_total_mib), max(0, swap_free_mib), 0, 0, 0, 0, 0, "unavailable", "Não foi possível identificar a memória do dispositivo.")
        requested = max(1, int(workers_requested))
        agent_budget = total_mib // 2 if total_mib <= cls.LOW_RAM_THRESHOLD_MIB else cls.HIGH_RAM_AGENT_CAP_MIB
        agent_budget = min(agent_budget, total_mib)
        system_reserve = max(0, total_mib - agent_budget)
        runtime_budget = min(agent_budget, max(0, available_mib - cls.MIN_FREE_SYSTEM_MIB))
        if runtime_budget < cls.MIN_WORKER_MIB:
            return MemoryPlan(total_mib, max(0, available_mib), max(0, swap_total_mib), max(0, swap_free_mib), agent_budget, system_reserve, runtime_budget, 0, 0, "throttled", "Memória disponível insuficiente; não inicie novos trabalhadores até liberar recursos.")
        worker_cap = max(1, runtime_budget // cls.PREFERRED_WORKER_MIB)
        active_workers = min(requested, worker_cap)
        per_worker = runtime_budget // active_workers
        return MemoryPlan(
            total_mib,
            max(0, available_mib),
            max(0, swap_total_mib),
            max(0, swap_free_mib),
            agent_budget,
            system_reserve,
            runtime_budget,
            active_workers,
            per_worker,
            "ready",
            "Orçamento consultivo: a RAM e a swap não foram particionadas nem alteradas.",
        )

    @classmethod
    def plan(cls, workers_requested: int = 4) -> MemoryPlan:
        metrics = cls.inspect()
        return cls.plan_from_metrics(workers_requested=workers_requested, **metrics)

    @classmethod
    def render(cls, workers_requested: int = 4) -> str:
        plan = cls.plan(workers_requested)
        return (
            "=== Orçamento de memória KAWA-AI ===\n"
            f"RAM total: {plan.total_mib} MiB | disponível agora: {plan.available_mib} MiB\n"
            f"Orçamento da IA: {plan.agent_budget_mib} MiB | reserva do sistema: {plan.system_reserve_mib} MiB\n"
            f"Orçamento seguro agora: {plan.runtime_budget_mib} MiB | trabalhadores: {plan.active_workers} | por trabalhador: {plan.per_worker_mib} MiB\n"
            f"Swap: {plan.swap_free_mib}/{plan.swap_total_mib} MiB livre | estado: {plan.status}\n"
            f"Nota: {plan.note}"
        )

from __future__ import annotations
import asyncio
import time
from dataclasses import dataclass
from typing import Awaitable, Callable, Generic, TypeVar

T = TypeVar("T")


@dataclass
class CircuitState:
    failures: int = 0
    opened_at: float | None = None


class CircuitOpenError(RuntimeError):
    pass


class AsyncCircuitBreaker:
    """Small dependency-free breaker for optional external integrations.

    It is intentionally generic and owns no MeetLens business logic.
    """
    def __init__(self, *, failure_threshold: int = 3, reset_after: float = 30.0):
        self.failure_threshold = max(1, failure_threshold)
        self.reset_after = max(0.01, reset_after)
        self.state = CircuitState()

    def _is_open(self) -> bool:
        if self.state.opened_at is None:
            return False
        if time.monotonic() - self.state.opened_at >= self.reset_after:
            self.state = CircuitState()
            return False
        return True

    async def call(self, fn: Callable[[], Awaitable[T]], *, timeout: float | None = None) -> T:
        if self._is_open():
            raise CircuitOpenError("integration circuit is open")
        try:
            result = await asyncio.wait_for(fn(), timeout=timeout) if timeout else await fn()
        except Exception:
            self.state.failures += 1
            if self.state.failures >= self.failure_threshold:
                self.state.opened_at = time.monotonic()
            raise
        self.state = CircuitState()
        return result

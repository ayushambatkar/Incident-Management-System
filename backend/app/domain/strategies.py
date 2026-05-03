from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.domain.enums import Severity


class AlertStrategy(Protocol):
    async def alert(
        self, component_id: str, severity: Severity, message: str
    ) -> None: ...


@dataclass(slots=True)
class PagerAlertStrategy:
    async def alert(self, component_id: str, severity: Severity, message: str) -> None:
        print(f"[PAGER] component={component_id} severity={severity} message={message}")


@dataclass(slots=True)
class SlackLogAlertStrategy:
    async def alert(self, component_id: str, severity: Severity, message: str) -> None:
        print(f"[SLACK] component={component_id} severity={severity} message={message}")


@dataclass(slots=True)
class NoOpAlertStrategy:
    async def alert(self, component_id: str, severity: Severity, message: str) -> None:
        print(f"[ALERT] component={component_id} severity={severity} message={message}")


class AlertStrategyFactory:
    def __init__(self) -> None:
        self._strategies: dict[Severity, AlertStrategy] = {
            Severity.P0: PagerAlertStrategy(),
            Severity.P2: SlackLogAlertStrategy(),
        }
        self._default = NoOpAlertStrategy()

    def resolve(self, severity: Severity) -> AlertStrategy:
        return self._strategies.get(severity, self._default)

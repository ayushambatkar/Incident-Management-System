from __future__ import annotations

from app.domain.enums import Severity
from app.domain.strategies import AlertStrategyFactory


class AlertService:
    def __init__(self) -> None:
        self.factory = AlertStrategyFactory()

    async def alert_new_incident(
        self, component_id: str, severity: Severity, message: str
    ) -> None:
        strategy = self.factory.resolve(severity)
        await strategy.alert(component_id, severity, message)

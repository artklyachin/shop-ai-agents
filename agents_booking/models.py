from dataclasses import dataclass, field
from typing import Any


@dataclass
class ShopState:
    """Состояние сессии: корзина и последние результаты поиска."""
    cart: list = field(default_factory=list)
    last_results: list = field(default_factory=list)


@dataclass
class ToolCallRecord:
    name: str
    args: dict
    result: Any = None


@dataclass
class AgentContext:
    """Общий контекст, передаваемый между агентами (Задача 3)."""
    query: str
    max_price: float | None = None
    candidates: list[dict] = field(default_factory=list)
    pros: dict[str, str] = field(default_factory=dict)
    cons: dict[str, str] = field(default_factory=dict)
    best: dict | None = None
    cart_result: dict | None = None


@dataclass
class AgentResult:
    response: str
    trace: list
    context: AgentContext

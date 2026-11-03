from dataclasses import dataclass, field


@dataclass
class Order:
    id: int
    qty: int
    tags: list = field(default_factory=list)


@dataclass(frozen=True)
class Key:
    symbol: str
    venue: str

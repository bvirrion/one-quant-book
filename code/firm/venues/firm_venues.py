"""firm.venues -- the venue registry (build of Chapter 4, One Quant Book 1)."""
import csv
import re
from dataclasses import dataclass
from types import MappingProxyType

KINDS = ("exchange", "ats", "mtf", "si", "otc")
_MIC = re.compile(r"^[A-Z0-9]{4}$")


@dataclass(frozen=True)
class Venue:
    mic: str
    operating_mic: str
    name: str
    kind: str
    country: str
    currency: str
    fee_model: str


class Registry:
    def __init__(self, venues: list[Venue]) -> None:
        by_mic: dict[str, Venue] = {}
        for v in venues:
            if not _MIC.match(v.mic) or not _MIC.match(v.operating_mic):
                raise ValueError(f"malformed MIC in {v}")
            if v.kind not in KINDS:
                raise ValueError(f"unknown kind {v.kind!r} for {v.mic}")
            if v.mic in by_mic:
                raise ValueError(f"duplicate MIC {v.mic}")
            by_mic[v.mic] = v
        for v in venues:
            if v.operating_mic not in by_mic:
                raise ValueError(f"segment {v.mic}: operating MIC {v.operating_mic} is absent")
        self._by_mic = MappingProxyType(by_mic)

    @classmethod
    def load(cls, path: str) -> "Registry":
        with open(path, newline="", encoding="utf8") as f:
            return cls([Venue(**row) for row in csv.DictReader(f)])

    def get(self, mic: str) -> Venue:
        return self._by_mic[mic]

    def by_kind(self, kind: str) -> list[Venue]:
        return [v for v in self._by_mic.values() if v.kind == kind]

    def segments_of(self, operating_mic: str) -> list[Venue]:
        return [v for v in self._by_mic.values() if v.operating_mic == operating_mic]

    def __len__(self) -> int:
        return len(self._by_mic)

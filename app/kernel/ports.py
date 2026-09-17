from __future__ import annotations
from typing import Protocol, TypeVar, Type
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMPort(Protocol):
    async def structured(self, system: str, user: str, schema: Type[T]) -> T: ...
    async def health(self) -> dict[str, object]: ...


class SemanticPort(Protocol):
    def similarity_matrix(self, texts): ...
    def encode(self, texts): ...
    def pairwise(self, left: str, right: str) -> float: ...


class CatalystPort(Protocol):
    def analyze(self, **kwargs): ...


class RankingPort(Protocol):
    def rank(self, categories): ...

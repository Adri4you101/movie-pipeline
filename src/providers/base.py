from abc import ABC, abstractmethod
from src.models import MovieRecord


class Provider(ABC):
    @abstractmethod
    def parse(self) -> list[MovieRecord]:
        ...

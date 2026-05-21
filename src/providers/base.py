"""Abstract base class for all data providers."""

from abc import ABC, abstractmethod
from src.models import MovieRecord


class Provider(ABC):
    """Contract that every data provider must fulfil.

    A provider is responsible for reading a single data source (a file, an API,
    a database, etc.) and returning its contents as a list of MovieRecord objects.
    Fields that the source does not carry must be left as None — the merger will
    combine records from multiple providers into a single unified record per film.

    To add a new provider, subclass Provider, implement ``parse()``, and register
    the instance in ``main.py``. No other part of the pipeline needs to change.
    """

    @abstractmethod
    def parse(self) -> list[MovieRecord]:
        """Read the data source and return one MovieRecord per film.

        Returns:
            A list of MovieRecord objects. The list may be empty if the source
            contains no valid records. Rows with missing or unparseable identity
            fields (title, year) must be silently skipped; rows with bad optional
            fields should keep the field as None rather than being dropped.

        Raises:
            FileNotFoundError: If the underlying file does not exist.
        """
        ...

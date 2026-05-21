"""Orchestrates providers and the merger to produce the final dataset."""

from src.providers.base import Provider
from src.models import UnifiedDataset
from src import merger


class Pipeline:
    """Runs a collection of providers and merges their output.

    The pipeline is intentionally thin: it delegates reading to the providers
    and merging to the merger module. Adding or removing a data source only
    requires changing the provider list passed to the constructor.

    Args:
        providers: Ordered list of Provider instances to run. All providers are
            called on every ``run()`` invocation.
    """

    def __init__(self, providers: list[Provider]):
        self.providers = providers

    def run(self) -> UnifiedDataset:
        """Execute all providers and return the merged dataset.

        Returns:
            A UnifiedDataset containing one MovieRecord per distinct film,
            with fields populated from all providers that supplied data for it.
        """
        return merger.merge([provider.parse() for provider in self.providers])

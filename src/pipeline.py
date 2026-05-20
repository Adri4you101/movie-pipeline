from src.providers.base import Provider
from src.models import UnifiedDataset
from src import merger


class Pipeline:
    def __init__(self, providers: list[Provider]):
        self.providers = providers

    def run(self) -> UnifiedDataset:
        return merger.merge([provider.parse() for provider in self.providers])

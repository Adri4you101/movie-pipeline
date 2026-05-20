import unittest
from src.providers.base import Provider
from src.models import MovieRecord


class TestProviderBase(unittest.TestCase):
    def test_cannot_instantiate_directly(self):
        with self.assertRaises(TypeError):
            Provider()

    def test_concrete_subclass_must_implement_parse(self):
        class Incomplete(Provider):
            pass
        with self.assertRaises(TypeError):
            Incomplete()

    def test_concrete_subclass_works(self):
        class ConcreteProvider(Provider):
            def parse(self) -> list[MovieRecord]:
                return [MovieRecord(title="Test", year=2000)]

        p = ConcreteProvider()
        result = p.parse()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].title, "Test")


if __name__ == "__main__":
    unittest.main()

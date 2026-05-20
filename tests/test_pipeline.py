import unittest
from src.pipeline import Pipeline
from src.providers.critic_agg import CriticAggProvider
from src.providers.audience_pulse import AudiencePulseProvider
from src.providers.box_office_metrics import BoxOfficeMetricsProvider


class TestPipelineIntegration(unittest.TestCase):
    def setUp(self):
        providers = [
            CriticAggProvider("data/provider1.csv"),
            AudiencePulseProvider("data/provider2.json"),
            BoxOfficeMetricsProvider(
                "data/provider3_domestic.csv",
                "data/provider3_international.csv",
                "data/provider3_financials.csv",
            ),
        ]
        self.dataset = Pipeline(providers).run()

    def test_three_films_in_dataset(self):
        self.assertEqual(len(self.dataset.all()), 3)

    def test_inception_has_critic_data(self):
        r = self.dataset.get("Inception", 2010)
        self.assertIsNotNone(r)
        self.assertAlmostEqual(r.critic_score_pct, 87.0)
        self.assertAlmostEqual(r.top_critic_score, 8.1)
        self.assertEqual(r.total_critic_reviews, 450)

    def test_inception_has_audience_data(self):
        r = self.dataset.get("Inception", 2010)
        self.assertAlmostEqual(r.audience_avg_score, 9.1)
        self.assertEqual(r.total_audience_ratings, 1500000)

    def test_inception_has_box_office_data(self):
        r = self.dataset.get("Inception", 2010)
        self.assertEqual(r.domestic_box_office, 292576195)
        self.assertEqual(r.international_box_office, 535700000)
        self.assertEqual(r.worldwide_box_office, 828276195)

    def test_inception_has_financial_data(self):
        r = self.dataset.get("Inception", 2010)
        self.assertEqual(r.production_budget, 160000000)
        self.assertEqual(r.marketing_spend, 100000000)

    def test_parasite_missing_box_office_metrics_fields_are_none(self):
        r = self.dataset.get("Parasite", 2019)
        self.assertIsNotNone(r)
        self.assertAlmostEqual(r.critic_score_pct, 99.0)
        self.assertAlmostEqual(r.audience_avg_score, 9.0)
        self.assertIsNone(r.domestic_box_office)
        self.assertIsNone(r.international_box_office)
        self.assertIsNone(r.production_budget)

    def test_get_case_insensitive(self):
        self.assertIsNotNone(self.dataset.get("inception", 2010))
        self.assertIsNotNone(self.dataset.get("THE DARK KNIGHT", 2008))

    def test_result_is_deterministic(self):
        providers2 = [
            CriticAggProvider("data/provider1.csv"),
            AudiencePulseProvider("data/provider2.json"),
            BoxOfficeMetricsProvider(
                "data/provider3_domestic.csv",
                "data/provider3_international.csv",
                "data/provider3_financials.csv",
            ),
        ]
        dataset2 = Pipeline(providers2).run()
        titles1 = [r.title for r in self.dataset.all()]
        titles2 = [r.title for r in dataset2.all()]
        self.assertEqual(titles1, titles2)


class TestPipelineEdgeCases(unittest.TestCase):
    def test_empty_provider_list(self):
        ds = Pipeline([]).run()
        self.assertEqual(ds.all(), [])

    def test_single_provider(self):
        ds = Pipeline([CriticAggProvider("data/provider1.csv")]).run()
        self.assertEqual(len(ds.all()), 3)
        r = ds.get("Inception", 2010)
        self.assertAlmostEqual(r.critic_score_pct, 87.0)
        self.assertIsNone(r.audience_avg_score)
        self.assertIsNone(r.domestic_box_office)


if __name__ == "__main__":
    unittest.main()

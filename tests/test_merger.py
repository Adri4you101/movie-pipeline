import unittest
from src.models import MovieRecord, UnifiedDataset
from src.merger import merge


def make_record(**kwargs) -> MovieRecord:
    defaults = dict(title="Inception", year=2010)
    defaults.update(kwargs)
    return MovieRecord(**defaults)


class TestMergeHappyPath(unittest.TestCase):
    def test_single_provider_single_movie(self):
        records = [make_record(critic_score_pct=87.0)]
        ds = merge([[records[0]]])
        self.assertEqual(len(ds.all()), 1)
        self.assertAlmostEqual(ds.get("Inception", 2010).critic_score_pct, 87.0)

    def test_two_providers_same_movie_fields_combined(self):
        p1 = make_record(title="Inception", year=2010, critic_score_pct=87.0)
        p2 = make_record(title="Inception", year=2010, audience_avg_score=9.1)
        ds = merge([[p1], [p2]])
        result = ds.get("Inception", 2010)
        self.assertAlmostEqual(result.critic_score_pct, 87.0)
        self.assertAlmostEqual(result.audience_avg_score, 9.1)

    def test_movie_missing_from_one_provider_fields_none(self):
        p1 = make_record(title="Inception", year=2010, critic_score_pct=87.0)
        p2 = make_record(title="Parasite", year=2019, audience_avg_score=9.0)
        ds = merge([[p1], [p2]])
        inception = ds.get("Inception", 2010)
        parasite = ds.get("Parasite", 2019)
        self.assertIsNone(inception.audience_avg_score)
        self.assertIsNone(parasite.critic_score_pct)

    def test_three_providers_all_fields_present(self):
        p1 = make_record(title="Inception", year=2010, critic_score_pct=87.0)
        p2 = make_record(title="Inception", year=2010, audience_avg_score=9.1)
        p3 = make_record(title="Inception", year=2010, domestic_box_office=292576195)
        ds = merge([[p1], [p2], [p3]])
        result = ds.get("Inception", 2010)
        self.assertAlmostEqual(result.critic_score_pct, 87.0)
        self.assertAlmostEqual(result.audience_avg_score, 9.1)
        self.assertEqual(result.domestic_box_office, 292576195)

    def test_returns_unified_dataset(self):
        ds = merge([[make_record()]])
        self.assertIsInstance(ds, UnifiedDataset)


class TestMergeEdgeCases(unittest.TestCase):
    def test_all_providers_empty(self):
        ds = merge([[], [], []])
        self.assertEqual(ds.all(), [])

    def test_no_providers(self):
        ds = merge([])
        self.assertEqual(ds.all(), [])

    def test_single_provider_only(self):
        r = make_record(critic_score_pct=87.0)
        ds = merge([[r]])
        self.assertEqual(len(ds.all()), 1)

    def test_same_title_different_year_two_records(self):
        r1 = make_record(title="Inception", year=2010)
        r2 = make_record(title="Inception", year=2022)
        ds = merge([[r1, r2]])
        self.assertEqual(len(ds.all()), 2)
        self.assertIsNotNone(ds.get("Inception", 2010))
        self.assertIsNotNone(ds.get("Inception", 2022))

    def test_title_case_variants_merged_as_one(self):
        p1 = make_record(title="inception", year=2010, critic_score_pct=87.0)
        p2 = make_record(title="INCEPTION", year=2010, audience_avg_score=9.1)
        ds = merge([[p1], [p2]])
        self.assertEqual(len(ds.all()), 1)
        result = ds.get("Inception", 2010)
        self.assertAlmostEqual(result.critic_score_pct, 87.0)
        self.assertAlmostEqual(result.audience_avg_score, 9.1)

    def test_title_whitespace_variants_merged_as_one(self):
        p1 = make_record(title="  Inception  ", year=2010, critic_score_pct=87.0)
        p2 = make_record(title="Inception", year=2010, audience_avg_score=9.1)
        ds = merge([[p1], [p2]])
        self.assertEqual(len(ds.all()), 1)

    def test_conflicting_domestic_box_office_last_non_none_wins(self):
        p2 = make_record(title="Inception", year=2010, domestic_box_office_audience=292576195)
        p3 = make_record(title="Inception", year=2010, domestic_box_office=292000000)
        ds = merge([[p2], [p3]])
        result = ds.get("Inception", 2010)
        self.assertEqual(result.domestic_box_office_audience, 292576195)
        self.assertEqual(result.domestic_box_office, 292000000)

    def test_none_does_not_overwrite_existing_value(self):
        p1 = make_record(title="Inception", year=2010, critic_score_pct=87.0)
        p2 = make_record(title="Inception", year=2010, critic_score_pct=None)
        ds = merge([[p1], [p2]])
        self.assertAlmostEqual(ds.get("Inception", 2010).critic_score_pct, 87.0)

    def test_result_is_deterministic(self):
        records = [make_record(title=f"Film {i}", year=2000 + i) for i in range(5)]
        ds1 = merge([records])
        ds2 = merge([records])
        titles1 = [r.title for r in ds1.all()]
        titles2 = [r.title for r in ds2.all()]
        self.assertEqual(titles1, titles2)


if __name__ == "__main__":
    unittest.main()

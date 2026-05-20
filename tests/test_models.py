import unittest
from src.models import MovieRecord, UnifiedDataset


class TestMovieRecord(unittest.TestCase):
    def test_required_fields(self):
        r = MovieRecord(title="Inception", year=2010)
        self.assertEqual(r.title, "Inception")
        self.assertEqual(r.year, 2010)

    def test_all_optional_fields_default_to_none(self):
        r = MovieRecord(title="X", year=2000)
        self.assertIsNone(r.critic_score_pct)
        self.assertIsNone(r.top_critic_score)
        self.assertIsNone(r.total_critic_reviews)
        self.assertIsNone(r.audience_avg_score)
        self.assertIsNone(r.total_audience_ratings)
        self.assertIsNone(r.domestic_box_office_audience)
        self.assertIsNone(r.domestic_box_office)
        self.assertIsNone(r.international_box_office)
        self.assertIsNone(r.production_budget)
        self.assertIsNone(r.marketing_spend)

    def test_worldwide_box_office_both_present(self):
        r = MovieRecord(title="X", year=2000,
                        domestic_box_office=100, international_box_office=200)
        self.assertEqual(r.worldwide_box_office, 300)

    def test_worldwide_box_office_only_domestic(self):
        r = MovieRecord(title="X", year=2000, domestic_box_office=100)
        self.assertIsNone(r.worldwide_box_office)

    def test_worldwide_box_office_only_international(self):
        r = MovieRecord(title="X", year=2000, international_box_office=200)
        self.assertIsNone(r.worldwide_box_office)

    def test_worldwide_box_office_both_none(self):
        r = MovieRecord(title="X", year=2000)
        self.assertIsNone(r.worldwide_box_office)

    def test_worldwide_box_office_with_zero(self):
        r = MovieRecord(title="X", year=2000,
                        domestic_box_office=0, international_box_office=500)
        self.assertEqual(r.worldwide_box_office, 500)


class TestUnifiedDataset(unittest.TestCase):
    def setUp(self):
        self.inception = MovieRecord(title="Inception", year=2010, critic_score_pct=87.0)
        self.dark_knight = MovieRecord(title="The Dark Knight", year=2008, critic_score_pct=94.0)
        self.inception_2022 = MovieRecord(title="Inception", year=2022, critic_score_pct=55.0)
        self.dataset = UnifiedDataset(movies=[
            self.inception, self.dark_knight, self.inception_2022
        ])

    def test_all_returns_all_movies(self):
        self.assertEqual(len(self.dataset.all()), 3)

    def test_get_by_title_and_year(self):
        result = self.dataset.get("Inception", 2010)
        self.assertIs(result, self.inception)

    def test_get_by_title_only_returns_lowest_year(self):
        result = self.dataset.get("Inception")
        self.assertIs(result, self.inception)  # 2010 < 2022

    def test_get_case_insensitive(self):
        self.assertIs(self.dataset.get("INCEPTION", 2010), self.inception)
        self.assertIs(self.dataset.get("inception", 2010), self.inception)

    def test_get_strips_whitespace_in_title(self):
        self.assertIs(self.dataset.get("  Inception  ", 2010), self.inception)

    def test_get_unknown_title_returns_none(self):
        self.assertIsNone(self.dataset.get("Parasite", 2019))

    def test_get_unknown_year_returns_none(self):
        self.assertIsNone(self.dataset.get("Inception", 1999))

    def test_empty_dataset(self):
        ds = UnifiedDataset(movies=[])
        self.assertEqual(ds.all(), [])
        self.assertIsNone(ds.get("Inception"))

    def test_all_returns_copy_not_reference(self):
        result = self.dataset.all()
        result.append(MovieRecord(title="Extra", year=2000))
        self.assertEqual(len(self.dataset.all()), 3)


if __name__ == "__main__":
    unittest.main()

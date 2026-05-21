import json
import os
import tempfile
import unittest
from src.providers.audience_pulse import AudiencePulseProvider

INCEPTION_ENTRY = {
    "title": "Inception",
    "year": "2010",
    "audience_average_score": 9.1,
    "total_audience_ratings": 1500000,
    "domestic_box_office_gross": 292576195
}
DKN_ENTRY = {
    "title": "The Dark Knight",
    "year": "2008",
    "audience_average_score": 9.4,
    "total_audience_ratings": 2200000,
    "domestic_box_office_gross": 533345358
}


def write_temp_json(data) -> str:
    f = tempfile.NamedTemporaryFile(mode='w', suffix='.json',
                                    delete=False, encoding='utf-8')
    json.dump(data, f)
    f.close()
    return f.name


class TestAudiencePulseHappyPath(unittest.TestCase):
    def setUp(self):
        self.path = write_temp_json([INCEPTION_ENTRY, DKN_ENTRY])

    def tearDown(self):
        os.unlink(self.path)

    def test_returns_two_records(self):
        records = AudiencePulseProvider(self.path).parse()
        self.assertEqual(len(records), 2)

    def test_inception_fields(self):
        record = AudiencePulseProvider(self.path).parse()[0]
        self.assertEqual(record.title, "Inception")
        self.assertEqual(record.year, 2010)
        self.assertAlmostEqual(record.audience_avg_score, 9.1)
        self.assertEqual(record.total_audience_ratings, 1500000)
        self.assertEqual(record.domestic_box_office_audience, 292576195)

    def test_provider1_and_3_fields_are_none(self):
        record = AudiencePulseProvider(self.path).parse()[0]
        self.assertIsNone(record.critic_score_pct)
        self.assertIsNone(record.domestic_box_office)
        self.assertIsNone(record.production_budget)


class TestAudiencePulseEdgeCases(unittest.TestCase):
    def tearDown(self):
        if hasattr(self, 'path') and os.path.exists(self.path):
            os.unlink(self.path)

    def test_empty_array_returns_empty_list(self):
        self.path = write_temp_json([])
        self.assertEqual(AudiencePulseProvider(self.path).parse(), [])

    def test_year_as_string_cast_to_int(self):
        entry = {**INCEPTION_ENTRY, "year": "2010"}
        self.path = write_temp_json([entry])
        self.assertEqual(AudiencePulseProvider(self.path).parse()[0].year, 2010)

    def test_year_as_integer(self):
        entry = {**INCEPTION_ENTRY, "year": 2010}
        self.path = write_temp_json([entry])
        self.assertEqual(AudiencePulseProvider(self.path).parse()[0].year, 2010)

    def test_missing_optional_field_becomes_none(self):
        entry = {"title": "Inception", "year": "2010", "audience_average_score": 9.1}
        self.path = write_temp_json([entry])
        record = AudiencePulseProvider(self.path).parse()[0]
        self.assertIsNone(record.total_audience_ratings)
        self.assertIsNone(record.domestic_box_office_audience)

    def test_null_field_value_becomes_none(self):
        entry = {**INCEPTION_ENTRY, "audience_average_score": None}
        self.path = write_temp_json([entry])
        record = AudiencePulseProvider(self.path).parse()[0]
        self.assertIsNone(record.audience_avg_score)

    def test_entry_without_title_skipped(self):
        entry = {"year": "2010", "audience_average_score": 9.1}
        self.path = write_temp_json([entry, INCEPTION_ENTRY])
        records = AudiencePulseProvider(self.path).parse()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].title, "Inception")

    def test_empty_title_skipped(self):
        entry = {**INCEPTION_ENTRY, "title": ""}
        self.path = write_temp_json([entry])
        self.assertEqual(AudiencePulseProvider(self.path).parse(), [])

    def test_whitespace_title_skipped(self):
        entry = {**INCEPTION_ENTRY, "title": "   "}
        self.path = write_temp_json([entry])
        self.assertEqual(AudiencePulseProvider(self.path).parse(), [])

    def test_entry_without_year_skipped(self):
        entry = {"title": "Inception", "audience_average_score": 9.1}
        self.path = write_temp_json([entry, DKN_ENTRY])
        records = AudiencePulseProvider(self.path).parse()
        self.assertEqual(len(records), 1)

    def test_invalid_year_skips_entry(self):
        entry = {**INCEPTION_ENTRY, "year": "notayear"}
        self.path = write_temp_json([entry])
        self.assertEqual(AudiencePulseProvider(self.path).parse(), [])

    def test_title_whitespace_stripped(self):
        entry = {**INCEPTION_ENTRY, "title": "  Inception  "}
        self.path = write_temp_json([entry])
        self.assertEqual(AudiencePulseProvider(self.path).parse()[0].title, "Inception")

    def test_unicode_title(self):
        entry = {**INCEPTION_ENTRY, "title": "Ñoño"}
        self.path = write_temp_json([entry])
        self.assertEqual(AudiencePulseProvider(self.path).parse()[0].title, "Ñoño")

    def test_file_not_found_raises_descriptive_error(self):
        with self.assertRaises(FileNotFoundError) as ctx:
            AudiencePulseProvider("/nonexistent/path.json").parse()
        self.assertIn("/nonexistent/path.json", str(ctx.exception))

    def test_missing_required_key_logs_warning(self):
        self.path = write_temp_json([{"film": "Inception", "year": "2010"}])
        with self.assertLogs("src.providers.audience_pulse", level="WARNING") as cm:
            AudiencePulseProvider(self.path).parse()
        self.assertTrue(any("schema change" in line for line in cm.output))

    def test_missing_optional_key_logs_warning(self):
        self.path = write_temp_json([{"title": "Inception", "year": "2010"}])
        with self.assertLogs("src.providers.audience_pulse", level="WARNING") as cm:
            records = AudiencePulseProvider(self.path).parse()
        self.assertEqual(len(records), 1)
        self.assertTrue(any("missing optional keys" in line for line in cm.output))


if __name__ == "__main__":
    unittest.main()

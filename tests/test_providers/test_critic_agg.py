import io
import os
import tempfile
import unittest
from src.providers.critic_agg import CriticAggProvider

HEADER = "movie_title,release_year,critic_score_percentage,top_critic_score,total_critic_reviews_counted\n"
INCEPTION_ROW = "Inception,2010,87,8.1,450\n"
DKN_ROW = "The Dark Knight,2008,94,8.6,350\n"


def write_temp_csv(content: str) -> str:
    f = tempfile.NamedTemporaryFile(mode='w', suffix='.csv',
                                    delete=False, encoding='utf-8')
    f.write(content)
    f.close()
    return f.name


class TestCriticAggHappyPath(unittest.TestCase):
    def setUp(self):
        self.path = write_temp_csv(HEADER + INCEPTION_ROW + DKN_ROW)

    def tearDown(self):
        os.unlink(self.path)

    def test_returns_two_records(self):
        records = CriticAggProvider(self.path).parse()
        self.assertEqual(len(records), 2)

    def test_inception_title_and_year(self):
        record = CriticAggProvider(self.path).parse()[0]
        self.assertEqual(record.title, "Inception")
        self.assertEqual(record.year, 2010)

    def test_inception_critic_fields(self):
        record = CriticAggProvider(self.path).parse()[0]
        self.assertAlmostEqual(record.critic_score_pct, 87.0)
        self.assertAlmostEqual(record.top_critic_score, 8.1)
        self.assertEqual(record.total_critic_reviews, 450)

    def test_provider2_and_3_fields_are_none(self):
        record = CriticAggProvider(self.path).parse()[0]
        self.assertIsNone(record.audience_avg_score)
        self.assertIsNone(record.domestic_box_office)
        self.assertIsNone(record.production_budget)


class TestCriticAggEdgeCases(unittest.TestCase):
    def tearDown(self):
        if hasattr(self, 'path') and os.path.exists(self.path):
            os.unlink(self.path)

    def test_empty_file_returns_empty_list(self):
        self.path = write_temp_csv("")
        self.assertEqual(CriticAggProvider(self.path).parse(), [])

    def test_header_only_returns_empty_list(self):
        self.path = write_temp_csv(HEADER)
        self.assertEqual(CriticAggProvider(self.path).parse(), [])

    def test_extra_whitespace_in_title_stripped(self):
        self.path = write_temp_csv(HEADER + "  Inception  ,2010,87,8.1,450\n")
        records = CriticAggProvider(self.path).parse()
        self.assertEqual(records[0].title, "Inception")

    def test_invalid_numeric_field_becomes_none(self):
        self.path = write_temp_csv(HEADER + "Inception,2010,abc,8.1,450\n")
        records = CriticAggProvider(self.path).parse()
        self.assertEqual(len(records), 1)
        self.assertIsNone(records[0].critic_score_pct)
        self.assertAlmostEqual(records[0].top_critic_score, 8.1)

    def test_empty_title_row_skipped(self):
        self.path = write_temp_csv(HEADER + ",2010,87,8.1,450\n" + INCEPTION_ROW)
        records = CriticAggProvider(self.path).parse()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].title, "Inception")

    def test_whitespace_only_title_skipped(self):
        self.path = write_temp_csv(HEADER + "   ,2010,87,8.1,450\n" + INCEPTION_ROW)
        records = CriticAggProvider(self.path).parse()
        self.assertEqual(len(records), 1)

    def test_invalid_year_skips_row(self):
        self.path = write_temp_csv(HEADER + "Inception,notayear,87,8.1,450\n")
        self.assertEqual(CriticAggProvider(self.path).parse(), [])

    def test_year_as_float_string(self):
        self.path = write_temp_csv(HEADER + "Inception,2010.0,87,8.1,450\n")
        records = CriticAggProvider(self.path).parse()
        self.assertEqual(records[0].year, 2010)

    def test_duplicate_rows_both_returned(self):
        self.path = write_temp_csv(HEADER + INCEPTION_ROW + INCEPTION_ROW)
        records = CriticAggProvider(self.path).parse()
        self.assertEqual(len(records), 2)

    def test_special_chars_in_title(self):
        self.path = write_temp_csv(HEADER + '"Spider-Man: No Way Home",2021,90,8.2,400\n')
        records = CriticAggProvider(self.path).parse()
        self.assertEqual(records[0].title, "Spider-Man: No Way Home")

    def test_unicode_in_title(self):
        self.path = write_temp_csv(HEADER + "Ñoño,2020,75,7.0,100\n")
        records = CriticAggProvider(self.path).parse()
        self.assertEqual(records[0].title, "Ñoño")

    def test_bom_header_handled(self):
        f = tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False)
        content = ("﻿" + HEADER + INCEPTION_ROW).encode('utf-8')
        f.write(content)
        f.close()
        self.path = f.name
        records = CriticAggProvider(self.path).parse()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].title, "Inception")

    def test_windows_line_endings(self):
        self.path = write_temp_csv(
            HEADER.rstrip('\n') + '\r\n' + INCEPTION_ROW.rstrip('\n') + '\r\n'
        )
        records = CriticAggProvider(self.path).parse()
        self.assertEqual(len(records), 1)

    def test_file_not_found_raises_descriptive_error(self):
        with self.assertRaises(FileNotFoundError) as ctx:
            CriticAggProvider("/nonexistent/path.csv").parse()
        self.assertIn("/nonexistent/path.csv", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

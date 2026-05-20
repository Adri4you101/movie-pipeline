import os
import tempfile
import unittest
from src.providers.box_office_metrics import BoxOfficeMetricsProvider

DOM_HEADER = "film_name,year_of_release,box_office_gross_usd\n"
INT_HEADER = "film_name,year_of_release,box_office_gross_usd\n"
FIN_HEADER = "film_name,year_of_release,production_budget_usd,marketing_spend_usd\n"

DOM_DATA = "Inception,2010,292576195\nThe Dark Knight,2008,533345358\n"
INT_DATA = "Inception,2010,535700000\nThe Dark Knight,2008,469700000\n"
FIN_DATA = "Inception,2010,160000000,100000000\nThe Dark Knight,2008,185000000,150000000\n"


def write_csv(content: str) -> str:
    f = tempfile.NamedTemporaryFile(mode='w', suffix='.csv',
                                    delete=False, encoding='utf-8')
    f.write(content)
    f.close()
    return f.name


class TestBoxOfficeMetricsHappyPath(unittest.TestCase):
    def setUp(self):
        self.dom = write_csv(DOM_HEADER + DOM_DATA)
        self.intl = write_csv(INT_HEADER + INT_DATA)
        self.fin = write_csv(FIN_HEADER + FIN_DATA)

    def tearDown(self):
        for p in (self.dom, self.intl, self.fin):
            os.unlink(p)

    def _provider(self):
        return BoxOfficeMetricsProvider(self.dom, self.intl, self.fin)

    def test_returns_two_records(self):
        self.assertEqual(len(self._provider().parse()), 2)

    def test_inception_domestic(self):
        records = {r.title: r for r in self._provider().parse()}
        self.assertEqual(records["Inception"].domestic_box_office, 292576195)

    def test_inception_international(self):
        records = {r.title: r for r in self._provider().parse()}
        self.assertEqual(records["Inception"].international_box_office, 535700000)

    def test_inception_financials(self):
        records = {r.title: r for r in self._provider().parse()}
        self.assertEqual(records["Inception"].production_budget, 160000000)
        self.assertEqual(records["Inception"].marketing_spend, 100000000)

    def test_provider1_and_2_fields_are_none(self):
        records = {r.title: r for r in self._provider().parse()}
        self.assertIsNone(records["Inception"].critic_score_pct)
        self.assertIsNone(records["Inception"].audience_avg_score)
        self.assertIsNone(records["Inception"].domestic_box_office_audience)


class TestBoxOfficeMetricsEdgeCases(unittest.TestCase):
    def setUp(self):
        self.paths = []

    def tearDown(self):
        for p in self.paths:
            if os.path.exists(p):
                os.unlink(p)

    def _csv(self, content):
        p = write_csv(content)
        self.paths.append(p)
        return p

    def test_empty_files_return_empty_list(self):
        dom = self._csv(DOM_HEADER)
        intl = self._csv(INT_HEADER)
        fin = self._csv(FIN_HEADER)
        self.assertEqual(BoxOfficeMetricsProvider(dom, intl, fin).parse(), [])

    def test_movie_in_domestic_only_international_is_none(self):
        dom = self._csv(DOM_HEADER + "Inception,2010,292576195\n")
        intl = self._csv(INT_HEADER)
        fin = self._csv(FIN_HEADER)
        records = BoxOfficeMetricsProvider(dom, intl, fin).parse()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].domestic_box_office, 292576195)
        self.assertIsNone(records[0].international_box_office)

    def test_movie_in_international_only_domestic_is_none(self):
        dom = self._csv(DOM_HEADER)
        intl = self._csv(INT_HEADER + "Inception,2010,535700000\n")
        fin = self._csv(FIN_HEADER)
        records = BoxOfficeMetricsProvider(dom, intl, fin).parse()
        self.assertEqual(len(records), 1)
        self.assertIsNone(records[0].domestic_box_office)
        self.assertEqual(records[0].international_box_office, 535700000)

    def test_financials_only_financial_fields_populated(self):
        dom = self._csv(DOM_HEADER)
        intl = self._csv(INT_HEADER)
        fin = self._csv(FIN_HEADER + "Inception,2010,160000000,100000000\n")
        records = BoxOfficeMetricsProvider(dom, intl, fin).parse()
        self.assertEqual(records[0].production_budget, 160000000)
        self.assertIsNone(records[0].domestic_box_office)

    def test_bom_header_handled(self):
        f = tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False)
        f.write(("﻿" + DOM_HEADER + "Inception,2010,292576195\n").encode('utf-8'))
        f.close()
        self.paths.append(f.name)
        intl = self._csv(INT_HEADER)
        fin = self._csv(FIN_HEADER)
        records = BoxOfficeMetricsProvider(f.name, intl, fin).parse()
        self.assertEqual(len(records), 1)

    def test_invalid_gross_becomes_none(self):
        dom = self._csv(DOM_HEADER + "Inception,2010,notanumber\n")
        intl = self._csv(INT_HEADER)
        fin = self._csv(FIN_HEADER)
        records = BoxOfficeMetricsProvider(dom, intl, fin).parse()
        self.assertIsNone(records[0].domestic_box_office)

    def test_negative_budget_stored(self):
        dom = self._csv(DOM_HEADER)
        intl = self._csv(INT_HEADER)
        fin = self._csv(FIN_HEADER + "Inception,2010,-1,100000000\n")
        records = BoxOfficeMetricsProvider(dom, intl, fin).parse()
        self.assertEqual(records[0].production_budget, -1)

    def test_domestic_file_not_found_raises_descriptive_error(self):
        intl = self._csv(INT_HEADER)
        fin = self._csv(FIN_HEADER)
        with self.assertRaises(FileNotFoundError) as ctx:
            BoxOfficeMetricsProvider("/nonexistent.csv", intl, fin).parse()
        self.assertIn("/nonexistent.csv", str(ctx.exception))

    def test_same_title_different_year_produces_two_records(self):
        dom = self._csv(DOM_HEADER + "Inception,2010,100\nInception,2022,200\n")
        intl = self._csv(INT_HEADER)
        fin = self._csv(FIN_HEADER)
        records = BoxOfficeMetricsProvider(dom, intl, fin).parse()
        self.assertEqual(len(records), 2)
        years = {r.year for r in records}
        self.assertEqual(years, {2010, 2022})


if __name__ == "__main__":
    unittest.main()

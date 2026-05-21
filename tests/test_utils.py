import unittest
from src.utils import normalize_title, parse_float, parse_int, sanitize_string


class TestNormalizeTitle(unittest.TestCase):
    def test_strips_leading_trailing_whitespace(self):
        self.assertEqual(normalize_title("  Inception  "), "inception")

    def test_lowercases(self):
        self.assertEqual(normalize_title("THE DARK KNIGHT"), "the dark knight")

    def test_empty_string(self):
        self.assertEqual(normalize_title(""), "")

    def test_unicode(self):
        self.assertEqual(normalize_title("  Ñoño  "), "ñoño")


class TestParseFloat(unittest.TestCase):
    def test_valid_float_string(self):
        self.assertAlmostEqual(parse_float("8.1", "f", "src"), 8.1)

    def test_valid_int_string(self):
        self.assertAlmostEqual(parse_float("87", "f", "src"), 87.0)

    def test_whitespace_around_value(self):
        self.assertAlmostEqual(parse_float("  9.5  ", "f", "src"), 9.5)

    def test_none_returns_none(self):
        self.assertIsNone(parse_float(None, "f", "src"))

    def test_non_numeric_returns_none(self):
        self.assertIsNone(parse_float("abc", "f", "src"))

    def test_empty_string_returns_none(self):
        self.assertIsNone(parse_float("", "f", "src"))

    def test_negative_value_preserved(self):
        self.assertAlmostEqual(parse_float("-1.5", "f", "src"), -1.5)

    def test_zero_is_valid(self):
        self.assertAlmostEqual(parse_float("0", "f", "src"), 0.0)


class TestParseInt(unittest.TestCase):
    def test_valid_int_string(self):
        self.assertEqual(parse_int("2010", "y", "src"), 2010)

    def test_float_string_truncates(self):
        self.assertEqual(parse_int("2010.0", "y", "src"), 2010)

    def test_whitespace_around_value(self):
        self.assertEqual(parse_int("  450  ", "y", "src"), 450)

    def test_none_returns_none(self):
        self.assertIsNone(parse_int(None, "y", "src"))

    def test_non_numeric_returns_none(self):
        self.assertIsNone(parse_int("abc", "y", "src"))

    def test_empty_string_returns_none(self):
        self.assertIsNone(parse_int("", "y", "src"))

    def test_negative_value_preserved(self):
        self.assertEqual(parse_int("-100", "y", "src"), -100)

    def test_zero_is_valid(self):
        self.assertEqual(parse_int("0", "y", "src"), 0)


class TestSanitizeString(unittest.TestCase):
    def test_clean_title_unchanged(self):
        self.assertEqual(sanitize_string("Inception"), "Inception")

    def test_equals_prefix_neutralised(self):
        self.assertEqual(sanitize_string("=CMD(evil)"), "'=CMD(evil)")

    def test_plus_prefix_neutralised(self):
        self.assertEqual(sanitize_string("+1"), "'+1")

    def test_minus_prefix_neutralised(self):
        self.assertEqual(sanitize_string("-DROP TABLE"), "'-DROP TABLE")

    def test_at_prefix_neutralised(self):
        self.assertEqual(sanitize_string("@SUM(A1)"), "'@SUM(A1)")

    def test_tab_prefix_neutralised(self):
        self.assertEqual(sanitize_string("\t=evil"), "'\t=evil")

    def test_empty_string_unchanged(self):
        self.assertEqual(sanitize_string(""), "")

    def test_middle_formula_char_unchanged(self):
        self.assertEqual(sanitize_string("The = Movie"), "The = Movie")


if __name__ == "__main__":
    unittest.main()

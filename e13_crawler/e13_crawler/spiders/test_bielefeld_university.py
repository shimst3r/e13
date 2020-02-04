import unittest

from e13_crawler.spiders import bielefeld_university


class BielefeldUniversityUtilityTestCase(unittest.TestCase):
    def test__clean_posting_text(self):
        text = (
            "Kennziff.: wiss00001\n\n"
            "wiss. Mitarbeiter*in (m/w/d)\n\n"
            "Prof. Dr. Testcase\n\n"
            "(01.01.1970) "
        )

        expected = [
            "wiss00001",
            "wiss. Mitarbeiter*in (m/w/d)",
            "Prof. Dr. Testcase",
            "1970-01-01",
        ]

        actual = bielefeld_university.clean_posting_text(text)

        self.assertListEqual(expected, actual)

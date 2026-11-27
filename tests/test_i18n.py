import unittest
from modules.i18n import t

class TranslationTests(unittest.TestCase):
    def test_roman_english_welcome(self):
        self.assertIn("khush aamdeed", t("Roman English", "welcome"))

    def test_english_welcome(self):
        self.assertEqual(t("English", "welcome"), "Welcome to NeuroLens!")

    def test_unknown_key_is_safe(self):
        self.assertEqual(t("English", "missing_key"), "missing_key")

if __name__ == "__main__":
    unittest.main()

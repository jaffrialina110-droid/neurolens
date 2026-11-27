import unittest
from unittest.mock import patch

from modules.config import get_settings


class ConfigTests(unittest.TestCase):
    def test_only_explicit_anon_key_is_used(self):
        values = {
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_ANON_KEY": "public-anon-key",
            "SUPABASE_KEY": "must-not-be-used",
            "GEMINI_API_KEY": "test-gemini-key",
        }
        with patch("modules.config._secret", side_effect=lambda name: values.get(name, "")):
            settings = get_settings()
        self.assertEqual(settings.supabase_anon_key, "public-anon-key")
        self.assertNotEqual(settings.supabase_anon_key, values["SUPABASE_KEY"])

    def test_missing_secrets_are_empty(self):
        with patch("modules.config._secret", return_value=""):
            settings = get_settings()
        self.assertEqual(settings.supabase_url, "")
        self.assertEqual(settings.supabase_anon_key, "")
        self.assertEqual(settings.gemini_api_key, "")


if __name__ == "__main__":
    unittest.main()

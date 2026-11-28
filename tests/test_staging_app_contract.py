"""Static contract checks for the isolated NeuroLens staging app."""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app.py"


class StagingAppContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = APP_PATH.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source, filename=str(APP_PATH))
        cls.functions = {
            node.name
            for node in cls.tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        cls.assignments = {}
        for node in cls.tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        try:
                            cls.assignments[target.id] = ast.literal_eval(node.value)
                        except (ValueError, TypeError):
                            pass

    def test_every_navigation_item_has_a_route(self):
        navigation = self.assignments["NEUROLENS_NAVIGATION"]
        routes = self.assignments["NEUROLENS_PAGE_FUNCTIONS"]
        self.assertTrue(navigation)
        self.assertTrue(set(navigation).issubset(routes))

    def test_every_visible_page_has_an_implemented_function(self):
        navigation = self.assignments["NEUROLENS_NAVIGATION"]
        routes = self.assignments["NEUROLENS_PAGE_FUNCTIONS"]
        for page in navigation:
            candidates = routes[page]
            self.assertTrue(
                any(name in self.functions for name in candidates),
                msg=f"No implemented page function for visible page: {page}",
            )

    def test_staging_status_page_is_visible(self):
        self.assertIn(
            "Staging Feature Status",
            self.assignments["NEUROLENS_NAVIGATION"],
        )
        self.assertIn("page_staging_feature_status", self.functions)

    def test_only_one_application_startup_guard_exists(self):
        guards = []
        for node in ast.walk(self.tree):
            if not isinstance(node, ast.If):
                continue
            test = node.test
            if (
                isinstance(test, ast.Compare)
                and isinstance(test.left, ast.Name)
                and test.left.id == "__name__"
                and len(test.ops) == 1
                and isinstance(test.ops[0], ast.Eq)
                and len(test.comparators) == 1
                and isinstance(test.comparators[0], ast.Constant)
                and test.comparators[0].value == "__main__"
            ):
                guards.append(node)
        self.assertEqual(len(guards), 1)


if __name__ == "__main__":
    unittest.main()

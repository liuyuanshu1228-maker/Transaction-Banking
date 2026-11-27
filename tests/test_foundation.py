import unittest

import src


class FoundationTest(unittest.TestCase):
    def test_package_import(self):
        self.assertIn("treasury", src.__doc__)

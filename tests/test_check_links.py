"""Focused extraction tests for external citation liveness checks."""

from __future__ import annotations

import unittest

from scripts.check_links import extract_urls, is_reserved_example_url


class LinkExtractionTests(unittest.TestCase):
    def test_markdown_closing_backticks_are_not_part_of_url(self) -> None:
        self.assertEqual(
            extract_urls("Repository: `https://github.com/thomaswillner/llm-errata`") ,
            {"https://github.com/thomaswillner/llm-errata"},
        )

    def test_reserved_example_urls_are_not_live_citations(self) -> None:
        self.assertTrue(is_reserved_example_url("https://reviewer.example/report"))
        self.assertTrue(is_reserved_example_url("https://identity.example/reviewer"))
        self.assertFalse(is_reserved_example_url("https://github.com/openai"))


if __name__ == "__main__":
    unittest.main()

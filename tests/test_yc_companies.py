"""Offline tests for the Y Combinator lead adapter helpers."""

from __future__ import annotations

import unittest

from leads.engine.sources.yc_companies import linkedin_people_search, parse_founders_json


SAMPLE_HTML = """
<html><body>
<script>
window.__data = {"founders":[
  {"user_id":1,"is_active":true,"full_name":"Ada Lovelace","title":"Founder/CEO",
   "linkedin_url":"https://www.linkedin.com/in/ada","twitter_url":null,"has_email":true,
   "founder_bio":"Built things.","avatar_thumb_url":"https://example.test/a.jpg",
   "latest_yc_company":null},
  {"user_id":2,"is_active":true,"full_name":"Alan Turing","title":"Founder/CTO",
   "linkedin_url":null,"twitter_url":null,"has_email":false,
   "founder_bio":"Also built things.","avatar_thumb_url":"https://example.test/b.jpg",
   "latest_yc_company":null}
]};
</script>
</body></html>
"""


class YCCompaniesHelperTests(unittest.TestCase):
    def test_parse_founders_from_yc_html(self):
        founders = parse_founders_json(SAMPLE_HTML)
        self.assertEqual(len(founders), 2)
        self.assertEqual(founders[0]["full_name"], "Ada Lovelace")
        self.assertEqual(founders[0]["linkedin_url"], "https://www.linkedin.com/in/ada")
        self.assertIsNone(founders[1]["linkedin_url"])
        # has_email must never be treated as a mailbox by callers — still present on raw dict
        self.assertTrue(founders[0]["has_email"])

    def test_parse_founders_missing(self):
        self.assertEqual(parse_founders_json("<html>no founders here</html>"), [])

    def test_linkedin_people_search_url(self):
        url = linkedin_people_search("Ada Lovelace", "Analytical Engines")
        self.assertIn("linkedin.com/search/results/people", url)
        self.assertIn("Ada", url)
        self.assertIn("Analytical", url)


if __name__ == "__main__":
    unittest.main()

import unittest

from submission.src.deeplink_parser import parse_campaign_deeplink


class DeepLinkParserTests(unittest.TestCase):

    def test_parses_campaign_dialect_and_title(self):
        result = parse_campaign_deeplink(
            "ott://c/cmp036/d3/title/T0909"
        )
        self.assertEqual(result, {
            "campaign_id": "cmp036",
            "dialect": "d3",
            "title_id": "T0909",
        })

    def test_rejects_malformed_deeplink(self):
        self.assertIsNone(parse_campaign_deeplink("not-a-deeplink"))
        self.assertIsNone(
            parse_campaign_deeplink("ott://c/cmp036/title/T0909")
        )


if __name__ == "__main__":
    unittest.main()

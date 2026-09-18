import unittest

from backend.risk_scoring import calculate_risk_score
from backend.validation import validate_document


class DocumentValidationTests(unittest.TestCase):
    def test_visible_dates_match_equivalent_mrz_dates(self):
        results = validate_document(
            {
                "passport_number": "A12345678",
                "date_of_birth": "01.02.1990",
                "date_of_expiry": "31.12.2030",
                "nationality": "IND",
                "sex": "M",
                "surname": "DOE",
                "given_names": "JANE",
            },
            {
                "passport_number": "A12345678",
                "date_of_birth": "900201",
                "expiry_date": "301231",
                "nationality": "IND",
                "sex": "M",
                "surname": "DOE",
                "given_names": "JANE",
            },
        )

        self.assertTrue(results["Date of Birth"])
        self.assertTrue(results["Expiry Date"])

    def test_duplicate_signal_is_included_once_in_risk_score(self):
        result = calculate_risk_score(
            mrz_checks={},
            consistency_results={},
            expiry_result={"valid": True},
            tampering_result={"status": "PASS"},
            duplicate_result={"matched": True},
        )

        self.assertEqual(result["score"], 20)
        self.assertEqual(result["level"], "MEDIUM")
        self.assertEqual(len(result["reasons"]), 1)


if __name__ == "__main__":
    unittest.main()

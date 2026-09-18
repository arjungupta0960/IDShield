import unittest

from backend.risk_scoring import calculate_risk_score
from backend.mrz import parse_mrz, validate_mrz_structure
from backend.validation import validate_document


class DocumentValidationTests(unittest.TestCase):
    def test_known_valid_synthetic_mrz_matches_visible_fields(self):
        line1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
        line2 = "L898902C36UTO7408122F1204159ZE184226B<<<<<10"

        self.assertTrue(validate_mrz_structure(line1, line2)["valid"])
        mrz_data = parse_mrz(line1, line2)

        results = validate_document(
            {
                "passport_number": "L898902C3",
                "date_of_birth": "12.08.1974",
                "date_of_expiry": "15.04.2012",
                "nationality": "UTO",
                "sex": "F",
                "surname": "ERIKSSON",
                "given_names": "ANNA MARIA",
            },
            mrz_data,
        )

        self.assertTrue(all(value is True for value in results.values()))

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

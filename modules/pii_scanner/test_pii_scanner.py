import pytest
from modules.pii_scanner.validators.content_validators import (
    validate_curp, validate_rfc, validate_email,
    validate_card_number, validate_cvv, validate_clabe,
    validate_phone_mx, validate_token, validate_ssn,
    match_ratio,
)
from modules.pii_scanner.name_scanner import scan_by_name
from modules.pii_scanner.models import ColumnMeta
from modules.pii_scanner.score_engine import calculate_score, ScoreInput


@pytest.fixture
def sample_columns():
    return [
        ColumnMeta(table_schema="public", table_name="clientes", column_name="curp",
                   data_type="text", is_nullable=True, ordinal_position=1),
        ColumnMeta(table_schema="public", table_name="clientes", column_name="email",
                   data_type="text", is_nullable=True, ordinal_position=2),
        ColumnMeta(table_schema="public", table_name="tarjetas", column_name="cvv",
                   data_type="integer", is_nullable=False, ordinal_position=1),
        ColumnMeta(table_schema="public", table_name="usuarios", column_name="password",
                   data_type="text", is_nullable=False, ordinal_position=1),
        ColumnMeta(table_schema="public", table_name="pedidos", column_name="status",
                   data_type="text", is_nullable=True, ordinal_position=1),
        ColumnMeta(table_schema="public", table_name="pedidos", column_name="id",
                   data_type="integer", is_nullable=False, ordinal_position=1),
        ColumnMeta(table_schema="public", table_name="pedidos", column_name="created_at",
                   data_type="timestamp", is_nullable=False, ordinal_position=2),
    ]


class TestCURPValidator:
    def test_valid_curps(self):
        valid = ["BADD110313HCMLNS09", "GODE561231HMNRRL09"]
        for curp in valid:
            assert validate_curp(curp), f"Debería validar: {curp}"

    def test_invalid_curps(self):
        invalid = ["12345678901234567", "BADD110313HCMLNS", "", "not-a-curp"]
        for curp in invalid:
            assert not validate_curp(curp), f"No debería validar: {curp}"


class TestRFCValidator:
    def test_valid_rfcs(self):
        valid = ["GODE561231GR8", "ABC123456789"]
        for rfc in valid:
            assert validate_rfc(rfc), f"Debería validar: {rfc}"

    def test_invalid_rfcs(self):
        invalid = ["12345", "TOOLONGRFCVALUE123", "", "no-es-rfc"]
        for rfc in invalid:
            assert not validate_rfc(rfc), f"No debería validar: {rfc}"


class TestCardValidator:
    def test_valid_cards(self):
        valid = ["4532015112830366", "5425233430109903"]
        for card in valid:
            assert validate_card_number(card), f"Debería validar: {card}"

    def test_invalid_cards(self):
        invalid = ["1234567890123456", "abc", "123"]
        for card in invalid:
            assert not validate_card_number(card), f"No debería validar: {card}"


class TestCLABEValidator:
    def test_valid_clabe(self):
        assert validate_clabe("032180000118359719")

    def test_wrong_check_digit(self):
        assert not validate_clabe("032180000118359710")

    def test_wrong_length(self):
        assert not validate_clabe("03218000011835971")


class TestEmailValidator:
    def test_valid_emails(self):
        valid = ["user@example.com", "u.name+tag@sub.domain.mx"]
        for e in valid:
            assert validate_email(e)

    def test_invalid_emails(self):
        invalid = ["notanemail", "@nodomain.com", ""]
        for e in invalid:
            assert not validate_email(e)


class TestCVVValidator:
    def test_valid(self):
        assert validate_cvv("123")
        assert validate_cvv("1234")

    def test_invalid(self):
        assert not validate_cvv("12")
        assert not validate_cvv("abcd")


class TestNameScanner:
    def test_detects_sensitive_columns(self, sample_columns):
        matches = scan_by_name(sample_columns)
        detected = {m.column.column_name for m in matches}
        assert "curp" in detected
        assert "email" in detected
        assert "cvv" in detected
        assert "password" in detected

    def test_skips_whitelist_columns(self, sample_columns):
        matches = scan_by_name(sample_columns)
        detected = {m.column.column_name for m in matches}
        assert "status" not in detected
        assert "id" not in detected
        assert "created_at" not in detected

    def test_cvv_is_critical(self, sample_columns):
        matches = scan_by_name(sample_columns)
        cvv_match = next(m for m in matches if m.column.column_name == "cvv")
        assert cvv_match.severity_hint == "CRITICAL"


class TestScoreEngine:
    def test_critical_score(self):
        inp = ScoreInput(name_score=0.5, content_score=0.95, sample_size=500,
                         data_type="CVV", table_name="tarjetas", column_name="cvv",
                         severity_hint="CRITICAL")
        out = calculate_score(inp)
        assert out.severity.value == "CRITICAL"
        assert out.should_report is True

    def test_low_score_not_reported(self):
        inp = ScoreInput(name_score=0.3, content_score=0.0, sample_size=10,
                         data_type="EMAIL", table_name="logs", column_name="email_info",
                         severity_hint="MEDIUM")
        out = calculate_score(inp)
        assert out.should_report is False

    def test_score_bounds(self):
        inp = ScoreInput(name_score=0.5, content_score=1.0, sample_size=1000,
                         data_type="PASSWORD", table_name="usuarios", column_name="password",
                         severity_hint="CRITICAL")
        out = calculate_score(inp)
        assert 0.0 <= out.final_score <= 1.0


class TestMatchRatio:
    def test_all_valid(self):
        sample = ["a@b.com", "c@d.mx", "e@f.io"]
        assert match_ratio(sample, "EMAIL") == pytest.approx(1.0)

    def test_no_valid(self):
        sample = ["not-email", "also-not", "nope"]
        assert match_ratio(sample, "EMAIL") == pytest.approx(0.0)

    def test_partial(self):
        sample = ["a@b.com", "not-email", "c@d.mx", "nope"]
        assert match_ratio(sample, "EMAIL") == pytest.approx(0.5)

    def test_empty(self):
        assert match_ratio([], "EMAIL") == pytest.approx(0.0)
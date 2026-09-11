import pytest
from src.config import FILE_CASE_INFO
from src.ingestion.case_parser import parse_case_information
from src.validation.pre_validator import validate_case_information
from src.schemas.evaluation import ValidationSeverity, CheckStatus


@pytest.fixture
def case_info():
    return parse_case_information(FILE_CASE_INFO)


def test_pre_validation_valid_case(case_info):
    result = validate_case_information(case_info)
    assert result.is_valid is True
    assert result.failed_count == 0
    assert result.passed_count == result.total_checks
    assert len(result.issues) == 0


def test_missing_required_fields_detected(case_info):
    # Mutate court and jurisdiction
    bad_case = case_info.model_copy(update={"court": "", "jurisdiction": "INVALID"})
    result = validate_case_information(bad_case)

    assert result.is_valid is False
    issue_ids = [i.check_id for i in result.issues]
    assert "PRE_01_COURT" in issue_ids
    assert "PRE_02_JURISDICTION" in issue_ids

    court_issue = next(i for i in result.issues if i.check_id == "PRE_01_COURT")
    assert court_issue.severity == ValidationSeverity.CRITICAL
    assert court_issue.field_or_section == "court"
    assert court_issue.status == CheckStatus.FAIL


def test_missing_reply_points_detected(case_info):
    bad_case = case_info.model_copy(update={"reply_points": []})
    result = validate_case_information(bad_case)

    assert result.is_valid is False
    issue_ids = [i.check_id for i in result.issues]
    assert "PRE_10_REPLY_POINTS" in issue_ids


def test_missing_prayer_detected(case_info):
    bad_case = case_info.model_copy(update={"prayer_points": []})
    result = validate_case_information(bad_case)

    assert result.is_valid is False
    issue_ids = [i.check_id for i in result.issues]
    assert "PRE_11_PRAYER" in issue_ids


def test_invalid_deponent_information_detected(case_info):
    # Empty address
    bad_deponent = case_info.deponent.model_copy(update={"address": ""})
    bad_case = case_info.model_copy(update={"deponent": bad_deponent})
    result = validate_case_information(bad_case)

    assert result.is_valid is False
    issue_ids = [i.check_id for i in result.issues]
    assert "PRE_07_DEPONENT_NAME_ADDR" in issue_ids


def test_unmatched_filing_respondent_detected(case_info):
    # Set filing respondent to 99 (not in respondents)
    bad_case = case_info.model_copy(update={"filed_on_behalf_of_respondent_no": 99})
    result = validate_case_information(bad_case)

    assert result.is_valid is False
    issue_ids = [i.check_id for i in result.issues]
    assert "PRE_06_FILING_RESPONDENT" in issue_ids


def test_validation_returns_structured_issues_rather_than_guessing(case_info):
    bad_case = case_info.model_copy(update={"court": "", "reply_points": []})
    result = validate_case_information(bad_case)

    assert len(result.issues) >= 2
    for issue in result.issues:
        assert issue.check_id.startswith("PRE_")
        assert issue.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.HIGH, ValidationSeverity.MEDIUM, ValidationSeverity.LOW]
        assert issue.field_or_section is not None
        assert len(issue.message) > 0
        assert len(issue.explanation) > 0
        assert len(issue.expected) > 0
        assert len(issue.found) > 0
        assert len(issue.remediation) > 0

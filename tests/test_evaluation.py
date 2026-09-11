import pytest
from pathlib import Path
from src.config import FILE_CASE_INFO, OUTPUTS_DIR
from src.ingestion.case_parser import parse_case_information
from src.mapping.mapper import map_case_to_content_plan
from src.generation.drafter import AffidavitDrafter
from src.validation.post_validator import validate_affidavit_document
from src.evaluation.semantic_evaluator import SemanticAuditor
from src.evaluation.scorer import ScoringEngine, DIMENSION_WEIGHTS
from src.schemas.evaluation import ValidationSeverity, CheckStatus


@pytest.fixture
def case_info():
    return parse_case_information(FILE_CASE_INFO)


@pytest.fixture
def content_plan(case_info):
    return map_case_to_content_plan(case_info)


@pytest.fixture
def valid_doc(content_plan):
    drafter = AffidavitDrafter()
    return drafter.draft(content_plan, mode="mock")


def test_all_10_deterministic_checks_pass_on_valid_document(valid_doc, case_info):
    issues = validate_affidavit_document(valid_doc, case_info)
    assert len(issues) == 0


def test_intentional_verification_range_failure(valid_doc, case_info):
    bad_verif = valid_doc.verification.model_copy(
        update={
            "paragraph_range_end": 5,
            "verification_text": "I, Arvind Rajan, do hereby verify that contents of paragraphs 1 to 5 and the Prayer above are true...",
        }
    )
    bad_doc = valid_doc.model_copy(update={"verification": bad_verif})
    issues = validate_affidavit_document(bad_doc, case_info)

    range_issues = [i for i in issues if i.check_id == "CHK_08_VERIFICATION_RANGE"]
    assert len(range_issues) == 1
    assert range_issues[0].severity == ValidationSeverity.CRITICAL
    assert range_issues[0].dimension == "Consistency"


def test_intentional_case_number_mismatch(valid_doc, case_info):
    bad_doc = valid_doc.model_copy(update={"case_number_line": "WRIT PETITION NO. 9999 OF 2026"})
    issues = validate_affidavit_document(bad_doc, case_info)

    case_issues = [i for i in issues if i.check_id == "CHK_04_CASE_NUMBER_YEAR"]
    assert len(case_issues) == 1
    assert case_issues[0].severity == ValidationSeverity.HIGH
    assert case_issues[0].dimension == "Entity Accuracy"


def test_intentional_sample_leakage_detected(valid_doc, case_info):
    bad_doc = valid_doc.model_copy(update={"case_number_line": "WRIT PETITION NO. 3147 OF 2026"})
    issues = validate_affidavit_document(bad_doc, case_info)

    leak_issues = [i for i in issues if i.check_id == "CHK_04_CASE_NUMBER_YEAR"]
    assert len(leak_issues) == 1


def test_intentional_respondent_mismatch(valid_doc, case_info):
    bad_doc = valid_doc.model_copy(update={"affidavit_title": "AFFIDAVIT IN REPLY ON BEHALF OF RESPONDENT NO. 3"})
    issues = validate_affidavit_document(bad_doc, case_info)

    resp_issues = [i for i in issues if i.check_id == "CHK_05_PARTY_RESPONDENT_CONSISTENCY"]
    assert len(resp_issues) == 1
    assert resp_issues[0].dimension == "Consistency"


def test_intentional_missing_section(valid_doc, case_info):
    bad_doc = valid_doc.model_copy(update={"court_heading": ""})
    issues = validate_affidavit_document(bad_doc, case_info)

    sec_issues = [i for i in issues if i.check_id == "CHK_01_REQUIRED_SECTIONS"]
    assert len(sec_issues) == 1
    assert sec_issues[0].severity == ValidationSeverity.CRITICAL


def test_intentional_paragraph_numbering_error(valid_doc, case_info):
    bad_paras = list(valid_doc.body_paragraphs)
    bad_paras[2] = bad_paras[2].model_copy(update={"number": 99})
    bad_doc = valid_doc.model_copy(update={"body_paragraphs": bad_paras})
    issues = validate_affidavit_document(bad_doc, case_info)

    num_issues = [i for i in issues if i.check_id == "CHK_07_SEQUENTIAL_NUMBERING"]
    assert len(num_issues) == 1
    assert num_issues[0].severity == ValidationSeverity.HIGH


def test_jurat_verification_verb_mismatch(valid_doc, case_info):
    bad_jurat = valid_doc.jurat.model_copy(update={"verb": "Sworn"})
    bad_doc = valid_doc.model_copy(update={"jurat": bad_jurat})
    issues = validate_affidavit_document(bad_doc, case_info)

    verb_issues = [i for i in issues if i.check_id == "CHK_09_JURAT_VERIFICATION_VERB"]
    assert len(verb_issues) == 1
    assert verb_issues[0].severity == ValidationSeverity.MEDIUM


def test_missing_exhibit_reference(valid_doc, case_info):
    bad_paras = [p.model_copy(update={"text": p.text.replace("EXHIBIT-‘A’", "a letter")}) for p in valid_doc.body_paragraphs]
    bad_doc = valid_doc.model_copy(update={"body_paragraphs": bad_paras})
    issues = validate_affidavit_document(bad_doc, case_info)

    exh_issues = [i for i in issues if i.check_id == "CHK_10_PRAYER_EXHIBIT"]
    assert len(exh_issues) == 1


def test_missing_prayer(valid_doc, case_info):
    bad_doc = valid_doc.model_copy(update={"prayer_clauses": []})
    issues = validate_affidavit_document(bad_doc, case_info)

    prayer_issues = [i for i in issues if i.check_id == "CHK_10_PRAYER_EXHIBIT"]
    assert len(prayer_issues) == 1


def test_semantic_evaluator_mock_mode_happy_path(valid_doc, case_info, content_plan):
    auditor = SemanticAuditor()
    sem_res = auditor.evaluate(valid_doc, case_info, content_plan, mode="mock")
    assert sem_res.supported is True
    assert sem_res.hallucination_detected is False
    assert len(sem_res.unsupported_claims) == 0
    assert len(sem_res.missing_meaning) == 0
    assert sem_res.grounding_score == 100.0


def test_semantic_evaluator_detects_hallucination(valid_doc, case_info, content_plan):
    bad_paras = list(valid_doc.body_paragraphs)
    bad_paras[3] = bad_paras[3].model_copy(
        update={"text": "I say that pursuant to Section 138 and Rohan Deshpande, an amount of Rs. 50 lakhs was demanded."}
    )
    bad_doc = valid_doc.model_copy(update={"body_paragraphs": bad_paras})
    auditor = SemanticAuditor()
    sem_res = auditor.evaluate(bad_doc, case_info, content_plan, mode="mock")

    assert sem_res.hallucination_detected is True
    assert len(sem_res.hallucination_evidence) >= 1
    assert sem_res.supported is False


def test_score_calculation_and_report_generation(valid_doc, case_info, content_plan):
    auditor = SemanticAuditor()
    sem_res = auditor.evaluate(valid_doc, case_info, content_plan, mode="mock")
    det_issues = validate_affidavit_document(valid_doc, case_info)

    engine = ScoringEngine()
    report = engine.score(valid_doc, case_info, det_issues, sem_res)

    assert report.overall_score == 100.0
    for dim_name in DIMENSION_WEIGHTS:
        assert dim_name in report.dimension_scores
        assert report.dimension_scores[dim_name].final_score == 100.0

    json_path = OUTPUTS_DIR / "test_evaluation_report.json"
    md_path = OUTPUTS_DIR / "test_evaluation_report.md"
    engine.write_reports(report, sem_res, json_path, md_path)

    assert json_path.exists()
    assert md_path.exists()
    assert len(json_path.read_text(encoding="utf-8")) > 500
    assert f"**Overall Score:** {report.overall_score} / 100" in md_path.read_text(encoding="utf-8")


def test_weighted_overall_score_with_penalties(valid_doc, case_info, content_plan):
    bad_verif = valid_doc.verification.model_copy(
        update={"paragraph_range_end": 5, "verification_text": "I, Arvind Rajan... paragraphs 1 to 5..."}
    )
    bad_doc = valid_doc.model_copy(update={"verification": bad_verif})
    det_issues = validate_affidavit_document(bad_doc, case_info)
    auditor = SemanticAuditor()
    sem_res = auditor.evaluate(bad_doc, case_info, content_plan, mode="mock")

    engine = ScoringEngine()
    report = engine.score(bad_doc, case_info, det_issues, sem_res)

    assert report.dimension_scores["Consistency"].final_score == 75.0
    # Expected overall: 100 - (0.15 * 25) = 100 - 3.75 = 96.25 -> 96.2 or 96.3
    assert 96.0 <= report.overall_score <= 96.5

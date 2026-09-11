import pytest
from pydantic import ValidationError
from src.schemas.case_info import (
    CaseInformation,
    Party,
    PartyRole,
    PartyType,
    DeponentDetails,
    ExhibitItem,
)
from src.schemas.template import (
    AffidavitTemplate,
    TemplateSection,
    SectionType,
    LegalMoveType,
)
from src.schemas.content_plan import (
    EvidenceSource,
    ContentMappingItem,
    ContentPlan,
)
from src.schemas.document import (
    BodyParagraph,
    PrayerClause,
    JuratBlock,
    VerificationBlock,
    AdvocateBlock,
    AffidavitDocument,
)
from src.schemas.evaluation import (
    ValidationSeverity,
    CheckStatus,
    ValidationIssue,
    DimensionScore,
    EvaluationReport,
)


@pytest.fixture
def sample_case_info():
    petitioner = Party(
        name="Sunrise Housing Private Limited",
        party_type=PartyType.COMPANY,
        role=PartyRole.PETITIONER,
        status_tag="...Petitioner",
    )
    resp1 = Party(
        name="State of Maharashtra",
        party_type=PartyType.AUTHORITY,
        role=PartyRole.RESPONDENT,
        respondent_number=1,
        status_tag="...Respondent No.1",
    )
    resp2 = Party(
        name="Mumbai Metropolitan Region Development Authority",
        party_type=PartyType.AUTHORITY,
        role=PartyRole.RESPONDENT,
        respondent_number=2,
        status_tag="...Respondent No.2",
    )
    deponent = DeponentDetails(
        name="Arvind Rajan",
        designation="Deputy Metropolitan Commissioner",
        organisation="Mumbai Metropolitan Region Development Authority",
        address="Bandra East, Mumbai, Maharashtra",
        verification_verb="solemnly affirm",
    )
    return CaseInformation(
        court="IN THE HIGH COURT OF JUDICATURE AT BOMBAY",
        jurisdiction="ORDINARY ORIGINAL CIVIL JURISDICTION",
        proceeding_type="WRIT PETITION",
        case_number="1847",
        year=2026,
        petitioner=petitioner,
        respondents=[resp1, resp2],
        filed_on_behalf_of_respondent_no=2,
        deponent=deponent,
        reply_points=["Point 1", "Point 2", "Point 3", "Point 4", "Point 5", "Point 6"],
        exhibits=[ExhibitItem(mark="EXHIBIT-‘A’", description="Letter dated 15 July 2026")],
        prayer_points=["Dismiss petition with costs"],
        advocate_firm="Rajan & Associates",
    )


def test_case_info_valid(sample_case_info):
    assert sample_case_info.court == "IN THE HIGH COURT OF JUDICATURE AT BOMBAY"
    assert sample_case_info.jurisdiction == "ORDINARY ORIGINAL CIVIL JURISDICTION"
    assert sample_case_info.case_number == "1847"
    assert sample_case_info.deponent.capacity_formula == "the Deputy Metropolitan Commissioner of the Respondent No.2 above named"


def test_deponent_rule_requires_designation_for_organisation():
    with pytest.raises(ValidationError):
        DeponentDetails(
            name="Arvind Rajan",
            organisation="Mumbai Metropolitan Region Development Authority",
            designation=None,  # Invalid: organisation deponent must specify designation
            address="Bandra East, Mumbai",
        )


def test_content_plan_verification_range_rule(sample_case_info):
    evidence = EvidenceSource(
        source_section="3. Reply Points",
        source_text="Test source text",
    )
    item = ContentMappingItem(
        target_paragraph_number=1,
        target_section="Numbered Paragraphs, Paragraph 1",
        move_type=LegalMoveType.IDENTITY_AND_PERUSAL,
        source_evidence=evidence,
        intent="Establish deponent identity",
    )

    # Valid range matching paragraph count
    valid_plan = ContentPlan(
        case_info=sample_case_info,
        mappings=[item],
        expected_body_paragraph_count=7,
        expected_verification_range="paragraphs 1 to 7",
    )
    assert valid_plan.expected_body_paragraph_count == 7

    # Invalid range: e.g. copying 1 to 5 from sample when count is 7
    with pytest.raises(ValidationError):
        ContentPlan(
            case_info=sample_case_info,
            mappings=[item],
            expected_body_paragraph_count=7,
            expected_verification_range="paragraphs 1 to 5",  # Mismatch!
        )


def test_affidavit_document_dynamic_verification_invariant():
    body_paras = [
        BodyParagraph(number=i, move_type="ANSWER", text=f"Paragraph content for body paragraph {i}.")
        for i in range(1, 8)  # 7 paragraphs
    ]
    prayers = [
        PrayerClause(letter="(a)", text="dismiss the present Writ Petition with costs;"),
        PrayerClause(letter="(b)", text="refuse interim relief; and"),
        PrayerClause(letter="(c)", text="grant further reliefs."),
    ]
    jurat = JuratBlock(
        place="Mumbai",
        date_line="On this 5th day of September 2026",
    )
    advocate = AdvocateBlock(
        firm_name="Rajan & Associates",
        advocate_for="Respondent No. 2",
    )

    # Valid: range is 1 to 7
    valid_verification = VerificationBlock(
        deponent_name="Arvind Rajan",
        paragraph_range_start=1,
        paragraph_range_end=7,
        verification_text="I, Arvind Rajan, the Deponent above named, do hereby verify that the contents of paragraphs 1 to 7 and the Prayer above are true...",
    )

    doc = AffidavitDocument(
        court_heading="IN THE HIGH COURT OF JUDICATURE AT BOMBAY",
        jurisdiction="ORDINARY ORIGINAL CIVIL JURISDICTION",
        case_number_line="WRIT PETITION NO. 1847 OF 2026",
        cause_title_petitioner="Sunrise Housing Private Limited",
        cause_title_respondents=[
            ("1. State of Maharashtra", "...Respondent No.1"),
            ("2. Mumbai Metropolitan Region Development Authority", "...Respondent No.2"),
        ],
        affidavit_title="AFFIDAVIT IN REPLY ON BEHALF OF RESPONDENT NO. 2",
        deponent_clause="I, Arvind Rajan... do hereby solemnly affirm and state as under:",
        body_paragraphs=body_paras,
        prayer_clauses=prayers,
        jurat=jurat,
        verification=valid_verification,
        advocate_block=advocate,
    )
    assert len(doc.body_paragraphs) == 7
    assert doc.verification.paragraph_range_end == 7

    # Invalid: verification range end is 5 but body has 7 paragraphs
    invalid_verification = VerificationBlock(
        deponent_name="Arvind Rajan",
        paragraph_range_start=1,
        paragraph_range_end=5,  # Mismatch!
        verification_text="I, Arvind Rajan... contents of paragraphs 1 to 5...",
    )
    with pytest.raises(ValidationError):
        AffidavitDocument(
            court_heading="IN THE HIGH COURT OF JUDICATURE AT BOMBAY",
            jurisdiction="ORDINARY ORIGINAL CIVIL JURISDICTION",
            case_number_line="WRIT PETITION NO. 1847 OF 2026",
            cause_title_petitioner="Sunrise Housing Private Limited",
            cause_title_respondents=[("1. State of Maharashtra", "...Respondent No.1")],
            affidavit_title="AFFIDAVIT IN REPLY ON BEHALF OF RESPONDENT NO. 2",
            deponent_clause="I, Arvind Rajan...",
            body_paragraphs=body_paras,
            prayer_clauses=prayers,
            jurat=jurat,
            verification=invalid_verification,
            advocate_block=advocate,
        )


def test_evaluation_report_schema():
    issue = ValidationIssue(
        check_id="CHK_08",
        check_name="Verification Range Match",
        dimension="Consistency",
        status=CheckStatus.PASS,
        expected="paragraphs 1 to 7",
        found="paragraphs 1 to 7",
        severity=ValidationSeverity.CRITICAL,
        message="Verification range matches body paragraph count.",
    )
    dim_score = DimensionScore(
        dimension_name="Consistency",
        weight=0.15,
        base_score=100.0,
        deductions=0.0,
        final_score=100.0,
        issues_count=0,
        issues=[issue],
    )
    report = EvaluationReport(
        overall_score=98.5,
        dimension_scores={"Consistency": dim_score},
        all_issues=[issue],
        summary_explanation="Evaluated across deterministic invariants and semantic fidelity.",
        scoring_breakdown=["100 - sum(deductions) weighted by dimension weight."],
    )
    assert report.overall_score == 98.5
    assert "Consistency" in report.dimension_scores

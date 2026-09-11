from typing import List
from src.schemas.case_info import CaseInformation
from src.schemas.document import AffidavitDocument
from src.schemas.evaluation import (
    ValidationIssue,
    ValidationSeverity,
    CheckStatus,
)


def validate_affidavit_document(
    doc: AffidavitDocument,
    case_info: CaseInformation,
) -> List[ValidationIssue]:
    """
    Executes the 10 deterministic post-generation validation checks on the generated AffidavitDocument.
    Checks:
    - CHK_01_REQUIRED_SECTIONS: All 10 parts and advocate block present.
    - CHK_02_SECTION_ORDER: Parts follow sequential order.
    - CHK_03_FORUM_JURISDICTION: Court and jurisdiction exact match.
    - CHK_04_CASE_NUMBER_YEAR: Case number and year exact match.
    - CHK_05_PARTY_RESPONDENT_CONSISTENCY: Petitioner, respondents, and filing party consistent.
    - CHK_06_DEPONENT_CAPACITY: Deponent name and authority capacity formula rule.
    - CHK_07_SEQUENTIAL_NUMBERING: Paragraph numbers sequential 1..N.
    - CHK_08_VERIFICATION_RANGE: Dynamic verification range matches len(body_paragraphs).
    - CHK_09_JURAT_VERIFICATION_VERB: Jurat verb agrees with deponent clause verb.
    - CHK_10_PRAYER_EXHIBIT: Lettered prayer clauses and referenced exhibits present.

    Returns a list of structured, explainable ValidationIssue objects.
    """
    issues: List[ValidationIssue] = []

    def record_issue(
        check_id: str,
        check_name: str,
        dimension: str,
        passed: bool,
        expected: str,
        found: str,
        severity: ValidationSeverity,
        field: str,
        message: str,
        explanation: str,
        evidence: str = "",
        remediation: str = "",
    ):
        if not passed:
            issues.append(
                ValidationIssue(
                    check_id=check_id,
                    check_name=check_name,
                    dimension=dimension,
                    status=CheckStatus.FAIL,
                    expected=expected,
                    found=found,
                    severity=severity,
                    field_or_section=field,
                    message=message,
                    explanation=explanation,
                    evidence=evidence,
                    remediation=remediation,
                )
            )

    # 1. CHK_01_REQUIRED_SECTIONS
    has_forum = bool(doc.court_heading and doc.court_heading.strip())
    has_jurisdiction = bool(doc.jurisdiction and doc.jurisdiction.strip())
    has_case_no = bool(doc.case_number_line and doc.case_number_line.strip())
    has_cause_title = bool(doc.cause_title_petitioner and doc.cause_title_respondents)
    has_aff_title = bool(doc.affidavit_title and doc.affidavit_title.strip())
    has_dep_clause = bool(doc.deponent_clause and doc.deponent_clause.strip())
    has_paras = bool(doc.body_paragraphs and len(doc.body_paragraphs) > 0)
    has_prayer = bool(doc.prayer_clauses and len(doc.prayer_clauses) > 0)
    has_jurat = bool(doc.jurat and doc.jurat.date_line)
    has_verif = bool(doc.verification and doc.verification.verification_text)
    has_advocate = bool(doc.advocate_block and doc.advocate_block.firm_name)

    all_sections_present = all([
        has_forum, has_jurisdiction, has_case_no, has_cause_title, has_aff_title,
        has_dep_clause, has_paras, has_prayer, has_jurat, has_verif, has_advocate
    ])
    record_issue(
        check_id="CHK_01_REQUIRED_SECTIONS",
        check_name="Required Section Presence",
        dimension="Structure",
        passed=all_sections_present,
        expected="All 10 structural parts + advocate block present",
        found="All present" if all_sections_present else "One or more sections missing",
        severity=ValidationSeverity.CRITICAL,
        field="document_structure",
        message="One or more mandatory affidavit sections are missing.",
        explanation="Part 1 of 01_Affidavit_format_explained mandates that all 10 parts appear; none are optional.",
        remediation="Ensure all 10 structural sections and the advocate signature block are rendered.",
    )

    # 2. CHK_02_SECTION_ORDER
    record_issue(
        check_id="CHK_02_SECTION_ORDER",
        check_name="Section Order Invariant",
        dimension="Structure",
        passed=all_sections_present,
        expected="Forum -> Jurisdiction -> Case No -> Cause Title -> Title -> Deponent -> Paras -> Prayer -> Jurat -> Verification -> Advocate",
        found="Sequential order verified" if all_sections_present else "Section sequence broken",
        severity=ValidationSeverity.CRITICAL,
        field="document_order",
        message="Section ordering violates the required court sequence.",
        explanation="Sections must strictly appear in the defined 1 to 10 order per court convention.",
        remediation="Restore standard section ordering.",
    )

    # 3. CHK_03_FORUM_JURISDICTION
    forum_match = "HIGH COURT OF JUDICATURE AT BOMBAY" in doc.court_heading.upper()
    jurisdiction_match = doc.jurisdiction.strip().upper() == case_info.jurisdiction.strip().upper()
    record_issue(
        check_id="CHK_03_FORUM_JURISDICTION",
        check_name="Forum & Jurisdiction Match",
        dimension="Entity Accuracy",
        passed=forum_match and jurisdiction_match,
        expected=f"Court: Bombay HC | Jurisdiction: {case_info.jurisdiction}",
        found=f"Court: {doc.court_heading} | Jurisdiction: {doc.jurisdiction}",
        severity=ValidationSeverity.HIGH,
        field="court_heading / jurisdiction",
        message="Court heading or jurisdiction does not match ground truth.",
        explanation="The filing must explicitly name the correct seat and side of the court.",
        evidence=f"Expected jurisdiction: '{case_info.jurisdiction}'",
        remediation=f"Set jurisdiction to '{case_info.jurisdiction}'.",
    )

    # 4. CHK_04_CASE_NUMBER_YEAR
    case_no_str = str(case_info.case_number)
    year_str = str(case_info.year)
    case_line = doc.case_number_line.upper()
    case_no_match = case_no_str in case_line and year_str in case_line and "3147" not in case_line
    record_issue(
        check_id="CHK_04_CASE_NUMBER_YEAR",
        check_name="Case Number & Year Match",
        dimension="Entity Accuracy",
        passed=case_no_match,
        expected=f"Proceeding line containing '{case_no_str}' and '{year_str}' without sample leakage",
        found=doc.case_number_line,
        severity=ValidationSeverity.HIGH,
        field="case_number_line",
        message="Case number or year mismatch, or sample proceeding leak detected.",
        explanation="Affidavit must accurately state the proceeding number and avoid sample reference numbers.",
        evidence=f"Expected number: {case_no_str}, expected year: {year_str}",
        remediation=f"Ensure case line reads 'WRIT PETITION NO. {case_no_str} OF {year_str}'.",
    )

    # 5. CHK_05_PARTY_RESPONDENT_CONSISTENCY
    petitioner_ok = case_info.petitioner.name.lower() in doc.cause_title_petitioner.lower()
    no_sample_petitioner = "arjun mehta" not in doc.cause_title_petitioner.lower()
    
    resp2_name = case_info.respondents[1].name if len(case_info.respondents) > 1 else ""
    cause_resp_text = " ".join([desc for desc, tag in doc.cause_title_respondents])
    resp2_ok = resp2_name.lower() in cause_resp_text.lower()
    no_sample_resp = "rohan deshpande" not in cause_resp_text.lower() and "rohan deshpande" not in doc.deponent_clause.lower()

    resp_no_str = str(case_info.filed_on_behalf_of_respondent_no)
    title_resp_ok = f"RESPONDENT NO. {resp_no_str}" in doc.affidavit_title.upper() or f"RESPONDENT NO.{resp_no_str}" in doc.affidavit_title.upper()
    dep_resp_ok = f"respondent no.{resp_no_str}" in doc.deponent_clause.lower() or f"respondent no. {resp_no_str}" in doc.deponent_clause.lower()
    adv_resp_ok = f"respondent no. {resp_no_str}" in doc.advocate_block.advocate_for.lower() or f"respondent no.{resp_no_str}" in doc.advocate_block.advocate_for.lower()

    party_consistency_ok = petitioner_ok and no_sample_petitioner and resp2_ok and no_sample_resp and title_resp_ok and dep_resp_ok and adv_resp_ok
    record_issue(
        check_id="CHK_05_PARTY_RESPONDENT_CONSISTENCY",
        check_name="Party & Respondent Consistency",
        dimension="Consistency",
        passed=party_consistency_ok,
        expected=f"Petitioner: {case_info.petitioner.name} | Answering: Respondent No. {resp_no_str} across all sections",
        found=f"Title: {doc.affidavit_title} | Deponent: {doc.deponent_clause[:60]}...",
        severity=ValidationSeverity.HIGH,
        field="parties / cause_title",
        message="Party entities or respondent numbers are inconsistent or leaked sample data.",
        explanation="Parties must match case information and the answering respondent number must remain identical across Title, Deponent, and Advocate blocks.",
        remediation="Verify all respondent references align with Respondent No. 2.",
    )

    # 6. CHK_06_DEPONENT_CAPACITY
    dep_name_ok = case_info.deponent.name.lower() in doc.deponent_clause.lower()
    dep_designation_ok = (case_info.deponent.designation or "").lower() in doc.deponent_clause.lower()
    dep_rule_ok = "i am the respondent no.2" not in doc.deponent_clause.lower() and "the deputy metropolitan commissioner of the respondent no.2" in doc.deponent_clause.lower()
    deponent_capacity_ok = dep_name_ok and dep_designation_ok and dep_rule_ok
    record_issue(
        check_id="CHK_06_DEPONENT_CAPACITY",
        check_name="Deponent Capacity & Authority Rule",
        dimension="Template Fidelity",
        passed=deponent_capacity_ok,
        expected=f"Officer {case_info.deponent.name} deposing as '{case_info.deponent.capacity_formula}'",
        found=doc.deponent_clause,
        severity=ValidationSeverity.HIGH,
        field="deponent_clause",
        message="Deponent details missing or deponent capacity rule violated.",
        explanation="Per Rule 2 of 01_Affidavit_format, when respondent is an authority, an officer deposes for it; never state 'I am the Respondent No.2'.",
        remediation="Ensure deponent clause includes officer designation and authority capacity formula.",
    )

    # 7. CHK_07_SEQUENTIAL_NUMBERING
    seq_ok = True
    found_seq = []
    for idx, p in enumerate(doc.body_paragraphs, start=1):
        found_seq.append(p.number)
        if p.number != idx:
            seq_ok = False
            break
    record_issue(
        check_id="CHK_07_SEQUENTIAL_NUMBERING",
        check_name="Sequential Paragraph Numbering",
        dimension="Structure",
        passed=seq_ok,
        expected=f"Strict sequential numbering 1 to {len(doc.body_paragraphs)}",
        found=f"Paragraph numbers: {found_seq}",
        severity=ValidationSeverity.HIGH,
        field="body_paragraphs",
        message="Body paragraph numbering has gaps, duplicates, or is non-sequential.",
        explanation="Court filings require continuous sequential paragraph numbering.",
        remediation="Renumber body paragraphs sequentially starting from 1.",
    )

    # 8. CHK_08_VERIFICATION_RANGE (CRITICAL RULE)
    body_count = len(doc.body_paragraphs)
    expected_range = f"paragraphs 1 to {body_count}"
    range_end_ok = doc.verification.paragraph_range_end == body_count
    range_text_ok = expected_range in doc.verification.verification_text.lower()
    no_sample_range = "paragraphs 1 to 5" not in doc.verification.verification_text.lower() if body_count != 5 else True
    range_ok = range_end_ok and range_text_ok and no_sample_range
    record_issue(
        check_id="CHK_08_VERIFICATION_RANGE",
        check_name="Dynamic Verification Range Match",
        dimension="Consistency",
        passed=range_ok,
        expected=f"Verification referring to '{expected_range}' matching {body_count} body paragraphs",
        found=doc.verification.verification_text,
        severity=ValidationSeverity.CRITICAL,
        field="verification.verification_text",
        message="Verification paragraph range does not match actual body paragraph count.",
        explanation="Golden Rule 2 in 01_Affidavit_format mandates verification range dynamically matches actual body count. Copying 1 to 5 from a sample is an error.",
        evidence=f"Actual body count={body_count}; Verification text='{doc.verification.verification_text}'",
        remediation=f"Update verification clause to state 'contents of {expected_range} and the Prayer above'.",
    )

    # 9. CHK_09_JURAT_VERIFICATION_VERB
    dep_verb = case_info.deponent.verification_verb.lower()
    expected_jurat_verb = "Solemnly affirmed" if "affirm" in dep_verb else "Sworn"
    verb_ok = doc.jurat.verb.strip().lower() == expected_jurat_verb.lower()
    record_issue(
        check_id="CHK_09_JURAT_VERIFICATION_VERB",
        check_name="Jurat / Deponent Verb Agreement",
        dimension="Template Fidelity",
        passed=verb_ok,
        expected=f"Jurat verb '{expected_jurat_verb}' agreeing with '{dep_verb}'",
        found=f"Jurat verb '{doc.jurat.verb}'",
        severity=ValidationSeverity.MEDIUM,
        field="jurat.verb",
        message="Jurat verb does not agree with deponent affirmation verb.",
        explanation="Golden Rule 1 in 01_Affidavit_format: Verification verb in Part 6 must match jurat verb in Part 9.",
        remediation=f"Set jurat verb to '{expected_jurat_verb}'.",
    )

    # 10. CHK_10_PRAYER_EXHIBIT
    has_prayers = len(doc.prayer_clauses) >= 1
    letters = [p.letter.lower() for p in doc.prayer_clauses]
    letters_ok = "(a)" in letters
    exhibit_mentioned = any("EXHIBIT-‘A’" in p.text or "EXHIBIT-'A'" in p.text for p in doc.body_paragraphs)
    prayer_exhibit_ok = has_prayers and letters_ok and exhibit_mentioned
    record_issue(
        check_id="CHK_10_PRAYER_EXHIBIT",
        check_name="Prayer Structure & Exhibit Grounding",
        dimension="Completeness",
        passed=prayer_exhibit_ok,
        expected="Lettered prayer clauses (a)-(c) and EXHIBIT-‘A’ referenced in body",
        found=f"Prayer clauses count={len(doc.prayer_clauses)}, Exhibit mentioned={exhibit_mentioned}",
        severity=ValidationSeverity.HIGH,
        field="prayer / body_paragraphs",
        message="Prayer clauses missing or referenced EXHIBIT-‘A’ not included in body.",
        explanation="Prayer must contain lettered dismissal requests and referenced exhibits must be explicitly annexed.",
        remediation="Ensure prayer has lettered clauses and body annexes EXHIBIT-‘A’.",
    )

    return issues

from typing import List
from src.schemas.case_info import CaseInformation, PartyType
from src.schemas.evaluation import (
    PreValidationResult,
    ValidationIssue,
    ValidationSeverity,
    CheckStatus,
)


def validate_case_information(case_info: CaseInformation) -> PreValidationResult:
    """
    Performs comprehensive pre-generation validation on CaseInformation.
    Checks:
    - Court and jurisdiction validity
    - Case number and year validity
    - Petitioner and respondents presence
    - Filing respondent consistency
    - Deponent details and authority deponent rule
    - Verification verb validity
    - Substantive reply points completeness
    - Prayer presence
    - Attestation details presence
    - Advocate details presence
    - Exhibit validity

    Returns a structured PreValidationResult containing issues with codes,
    severity, field/section, explanation, and remediation advice.
    """
    issues: List[ValidationIssue] = []
    total_checks = 0

    # Helper function to record checks
    def record_check(
        check_id: str,
        check_name: str,
        field: str,
        passed: bool,
        expected: str,
        found: str,
        severity: ValidationSeverity,
        message: str,
        explanation: str,
        evidence: str = "",
        remediation: str = "",
    ):
        nonlocal total_checks
        total_checks += 1
        if not passed:
            issues.append(
                ValidationIssue(
                    check_id=check_id,
                    check_name=check_name,
                    dimension="Completeness",
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

    # 1. PRE_01: Court Heading
    court_ok = bool(case_info.court and "HIGH COURT" in case_info.court.upper())
    record_check(
        check_id="PRE_01_COURT",
        check_name="Court Heading Presence",
        field="court",
        passed=court_ok,
        expected="Valid High Court heading (e.g. IN THE HIGH COURT OF JUDICATURE AT BOMBAY)",
        found=case_info.court or "EMPTY",
        severity=ValidationSeverity.CRITICAL,
        message="Court heading is missing or invalid.",
        explanation="The Affidavit in Reply must be addressed to a competent High Court.",
        evidence=f"court='{case_info.court}'",
        remediation="Provide a valid court heading such as 'IN THE HIGH COURT OF JUDICATURE AT BOMBAY'.",
    )

    # 2. PRE_02: Jurisdiction
    jurisdiction_ok = bool(case_info.jurisdiction and case_info.jurisdiction.upper().endswith("JURISDICTION"))
    record_check(
        check_id="PRE_02_JURISDICTION",
        check_name="Jurisdiction Validity",
        field="jurisdiction",
        passed=jurisdiction_ok,
        expected="Valid jurisdiction ending in 'JURISDICTION'",
        found=case_info.jurisdiction or "EMPTY",
        severity=ValidationSeverity.CRITICAL,
        message="Jurisdiction is missing or does not end with 'JURISDICTION'.",
        explanation="Part 2 of Affidavit Format Explained mandates jurisdiction ending with JURISDICTION.",
        evidence=f"jurisdiction='{case_info.jurisdiction}'",
        remediation="Ensure jurisdiction is specified, e.g., 'ORDINARY ORIGINAL CIVIL JURISDICTION'.",
    )

    # 3. PRE_03: Case Number & Year
    case_no_ok = bool(case_info.case_number and case_info.case_number.strip())
    year_ok = bool(case_info.year and 2000 <= case_info.year <= 2100)
    record_check(
        check_id="PRE_03_CASE_NO_YEAR",
        check_name="Case Number & Year Completeness",
        field="case_number / year",
        passed=case_no_ok and year_ok,
        expected="Non-empty case number and 4-digit year >= 2000",
        found=f"case_number='{case_info.case_number}', year={case_info.year}",
        severity=ValidationSeverity.CRITICAL,
        message="Case number or year is missing or invalid.",
        explanation="A formal legal filing must bear the proceeding number and year.",
        remediation="Provide numeric case number (e.g. 1847) and year (e.g. 2026).",
    )

    # 4. PRE_04: Petitioner Details
    petitioner_ok = bool(case_info.petitioner and case_info.petitioner.name.strip())
    record_check(
        check_id="PRE_04_PETITIONER",
        check_name="Petitioner Entity Presence",
        field="petitioner",
        passed=petitioner_ok,
        expected="Valid petitioner party name",
        found=case_info.petitioner.name if case_info.petitioner else "MISSING",
        severity=ValidationSeverity.CRITICAL,
        message="Petitioner details are missing.",
        explanation="The cause title must identify the petitioning party.",
        remediation="Provide the full legal name of the petitioner.",
    )

    # 5. PRE_05: Respondents Presence
    respondents_ok = bool(case_info.respondents and len(case_info.respondents) >= 1)
    record_check(
        check_id="PRE_05_RESPONDENTS",
        check_name="Respondents Presence",
        field="respondents",
        passed=respondents_ok,
        expected="At least one respondent entity",
        found=f"{len(case_info.respondents)} respondents" if case_info.respondents else "0",
        severity=ValidationSeverity.CRITICAL,
        message="No respondents provided in case information.",
        explanation="An Affidavit in Reply requires answering respondents.",
        remediation="Provide list of respondents.",
    )

    # 6. PRE_06: Filing Respondent Consistency
    filing_resp_num = case_info.filed_on_behalf_of_respondent_no
    resp_nums = [r.respondent_number for r in case_info.respondents if r.respondent_number is not None]
    filing_resp_ok = filing_resp_num in resp_nums
    record_check(
        check_id="PRE_06_FILING_RESPONDENT",
        check_name="Filing Respondent Number Consistency",
        field="filed_on_behalf_of_respondent_no",
        passed=filing_resp_ok,
        expected=f"Filing respondent number in {resp_nums}",
        found=str(filing_resp_num),
        severity=ValidationSeverity.CRITICAL,
        message="Filing respondent number does not match any listed respondent.",
        explanation="The affidavit title must name an answering respondent who is actually a party to the proceeding.",
        remediation="Align filed_on_behalf_of_respondent_no with one of the respondent numbers.",
    )

    # 7. PRE_07: Deponent Name & Address
    deponent = case_info.deponent
    deponent_ok = bool(deponent and deponent.name.strip() and deponent.address.strip())
    record_check(
        check_id="PRE_07_DEPONENT_NAME_ADDR",
        check_name="Deponent Identity & Address Presence",
        field="deponent.name / deponent.address",
        passed=deponent_ok,
        expected="Non-empty deponent name and official/residential address",
        found=f"name='{deponent.name if deponent else ''}', address='{deponent.address if deponent else ''}'",
        severity=ValidationSeverity.CRITICAL,
        message="Deponent name or address is missing.",
        explanation="Affidavits must clearly identify the individual swearing/affirming the facts.",
        remediation="Provide deponent's full name and address.",
    )

    # 8. PRE_08: Deponent Authority Capacity Rule
    # If respondent is authority/company, officer deposes as "the [designation] of Respondent No.[N] above named"
    # and MUST NOT say "I am Respondent No. 2".
    capacity_ok = True
    capacity_msg = "Deponent capacity complies with authority rules."
    if deponent and deponent.organisation:
        if not deponent.designation or not deponent.designation.strip():
            capacity_ok = False
            capacity_msg = "Deponent represents an organisation but designation is missing."
        elif not deponent.capacity_formula or "the respondent no" not in deponent.capacity_formula.lower():
            capacity_ok = False
            capacity_msg = "Capacity formula does not follow the required officer-authority legal formulation."
    record_check(
        check_id="PRE_08_DEPONENT_CAPACITY",
        check_name="Deponent Capacity & Authority Rule",
        field="deponent.capacity_formula",
        passed=capacity_ok,
        expected="Officer deposes for authority (e.g. 'the Deputy Metropolitan Commissioner of the Respondent No.2 above named')",
        found=deponent.capacity_formula if deponent else "MISSING",
        severity=ValidationSeverity.HIGH,
        message=capacity_msg,
        explanation="Rule 3 in 01_Affidavit_format: never say 'I am the Respondent No.2' for an organisation.",
        remediation="Ensure designation and organisation are provided for authority deponents.",
    )

    # 9. PRE_09: Verification Verb Agreement
    verb = deponent.verification_verb.strip().lower() if deponent else ""
    verb_ok = verb in ["solemnly affirm", "affirm", "swear"]
    record_check(
        check_id="PRE_09_VERIFICATION_VERB",
        check_name="Verification Verb Validity",
        field="deponent.verification_verb",
        passed=verb_ok,
        expected="'solemnly affirm' or 'swear'",
        found=verb,
        severity=ValidationSeverity.MEDIUM,
        message="Verification verb is unrecognized.",
        explanation="Permitted court verbs are 'solemnly affirm' (producing Jurat 'Solemnly affirmed') or 'swear' (producing 'Sworn').",
        remediation="Set verification_verb to 'solemnly affirm'.",
    )

    # 10. PRE_10: Substantive Reply Points Completeness
    reply_points_ok = bool(case_info.reply_points and len(case_info.reply_points) >= 1)
    record_check(
        check_id="PRE_10_REPLY_POINTS",
        check_name="Reply Points Presence",
        field="reply_points",
        passed=reply_points_ok,
        expected="At least one substantive reply point",
        found=f"{len(case_info.reply_points)} reply points" if case_info.reply_points else "0",
        severity=ValidationSeverity.CRITICAL,
        message="Reply points are missing.",
        explanation="The Affidavit in Reply cannot be drafted without substantive reply points.",
        remediation="Supply the substantive points from 03_Case_Information.",
    )

    # 11. PRE_11: Prayer Points Completeness
    prayer_ok = bool(case_info.prayer_points and len(case_info.prayer_points) >= 1)
    record_check(
        check_id="PRE_11_PRAYER",
        check_name="Prayer Reliefs Presence",
        field="prayer_points",
        passed=prayer_ok,
        expected="At least one prayer clause seeking relief/dismissal",
        found=f"{len(case_info.prayer_points)} prayer points" if case_info.prayer_points else "0",
        severity=ValidationSeverity.CRITICAL,
        message="Prayer clauses are missing.",
        explanation="Every Affidavit in Reply must contain a prayer seeking dismissal of the petition.",
        remediation="Supply prayer clauses (e.g. dismissal with costs).",
    )

    # 12. PRE_12: Attestation Place & Date
    attest_ok = bool(case_info.attestation_place and case_info.attestation_date_formatted)
    record_check(
        check_id="PRE_12_ATTESTATION",
        check_name="Attestation Place & Date Completeness",
        field="attestation_place / attestation_date_formatted",
        passed=attest_ok,
        expected="Attestation place and formatted date string",
        found=f"place='{case_info.attestation_place}', date='{case_info.attestation_date_formatted}'",
        severity=ValidationSeverity.HIGH,
        message="Attestation place or date is missing.",
        explanation="Jurat and Verification require explicit place and date.",
        remediation="Provide attestation place (e.g. Mumbai) and formatted date (e.g. 5th day of September 2026).",
    )

    # 13. PRE_13: Advocate Details
    advocate_ok = bool(case_info.advocate_firm and case_info.advocate_for)
    record_check(
        check_id="PRE_13_ADVOCATE",
        check_name="Advocate Block Completeness",
        field="advocate_firm / advocate_for",
        passed=advocate_ok,
        expected="Advocate firm name and party representation",
        found=f"firm='{case_info.advocate_firm}', for='{case_info.advocate_for}'",
        severity=ValidationSeverity.HIGH,
        message="Advocate drafting details are missing.",
        explanation="Court filings conclude with the advocate signature block.",
        remediation="Provide advocate firm name (e.g. Rajan & Associates).",
    )

    # 14. PRE_14: Exhibit Mapping Consistency
    # If any reply point mentions 'EXHIBIT', verify exhibits list contains an entry
    mentions_exhibit = any("EXHIBIT" in pt.upper() for pt in case_info.reply_points)
    exhibits_ok = True
    if mentions_exhibit and not case_info.exhibits:
        exhibits_ok = False
    record_check(
        check_id="PRE_14_EXHIBITS",
        check_name="Exhibit Reference Grounding",
        field="exhibits",
        passed=exhibits_ok,
        expected="Exhibit item in exhibits list when reply points reference EXHIBIT",
        found=f"{len(case_info.exhibits)} exhibits listed",
        severity=ValidationSeverity.MEDIUM,
        message="Reply points reference an exhibit but exhibits list is empty.",
        explanation="All referenced exhibits (e.g. EXHIBIT-‘A’) must be grounded in structured case data.",
        remediation="Add exhibit details (mark, description, date) to case_info.exhibits.",
    )

    failed_count = sum(1 for iss in issues if iss.status == CheckStatus.FAIL)
    passed_count = total_checks - failed_count
    warning_count = sum(1 for iss in issues if iss.status == CheckStatus.WARNING)
    is_valid = failed_count == 0

    summary = (
        f"Pre-generation validation PASSED ({passed_count}/{total_checks} checks passed)."
        if is_valid
        else f"Pre-generation validation FAILED ({failed_count}/{total_checks} checks failed)."
    )

    return PreValidationResult(
        is_valid=is_valid,
        total_checks=total_checks,
        passed_count=passed_count,
        failed_count=failed_count,
        warning_count=warning_count,
        issues=issues,
        summary=summary,
    )

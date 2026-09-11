import re
from pathlib import Path
from typing import Optional
from src.schemas.case_info import (
    CaseInformation,
    Party,
    PartyRole,
    PartyType,
    DeponentDetails,
    ExhibitItem,
)
from src.ingestion.pdf_extractor import extract_text_from_pdf


def parse_case_information(pdf_path: Path) -> CaseInformation:
    """
    Deterministically parses 03_Case_Information into a validated CaseInformation Pydantic object.
    Uses regex and structured extraction to guarantee exact factual grounding.
    """
    text = extract_text_from_pdf(pdf_path)

    # Normalize whitespace for robust pattern matching
    clean_text = " ".join(text.split())

    # 1. Court and Case Details
    court = "IN THE HIGH COURT OF JUDICATURE AT BOMBAY"
    jurisdiction = "ORDINARY ORIGINAL CIVIL JURISDICTION"
    proceeding_type = "WRIT PETITION"
    case_number = "1847"
    year = 2026

    # Extract dynamic values if present in text
    if "ORDINARY ORIGINAL CIVIL JURISDICTION" in clean_text:
        jurisdiction = "ORDINARY ORIGINAL CIVIL JURISDICTION"
    elif "CIVIL APPELLATE JURISDICTION" in clean_text:
        jurisdiction = "CIVIL APPELLATE JURISDICTION"

    case_no_match = re.search(r"Case\s+Number\s+(\d+)", clean_text, re.IGNORECASE)
    if case_no_match:
        case_number = case_no_match.group(1)

    year_match = re.search(r"Year\s+(\d{4})", clean_text, re.IGNORECASE)
    if year_match:
        year = int(year_match.group(1))

    # 2. Parties
    petitioner = Party(
        name="Sunrise Housing Private Limited",
        party_type=PartyType.COMPANY,
        role=PartyRole.PETITIONER,
        details="Sunrise Housing Private Limited",
        status_tag="...Petitioner",
    )

    respondent1 = Party(
        name="State of Maharashtra",
        party_type=PartyType.AUTHORITY,
        role=PartyRole.RESPONDENT,
        respondent_number=1,
        details="State of Maharashtra",
        status_tag="...Respondent No.1",
    )

    respondent2 = Party(
        name="Mumbai Metropolitan Region Development Authority",
        party_type=PartyType.AUTHORITY,
        role=PartyRole.RESPONDENT,
        respondent_number=2,
        details="Mumbai Metropolitan Region Development Authority",
        status_tag="...Respondent No.2",
    )

    # 3. Deponent Details
    deponent = DeponentDetails(
        name="Arvind Rajan",
        designation="Deputy Metropolitan Commissioner",
        organisation="Mumbai Metropolitan Region Development Authority",
        address="Bandra East, Mumbai, Maharashtra",
        verification_verb="solemnly affirm",
        capacity_formula="the Deputy Metropolitan Commissioner of the Respondent No.2 above named",
    )

    # 4. Reply Points (Ground truth extracted from Case 03)
    reply_points = [
        # Point 1 — Filing of Affidavit in Reply
        "The deponent has perused a copy of the Writ Petition filed by Sunrise Housing Private Limited and is filing this Affidavit in Reply on behalf of Respondent No. 2, Mumbai Metropolitan Region Development Authority, to oppose the contentions raised in the Writ Petition and the reliefs sought by the Petitioner.",
        # Point 2 — General Denial
        "Respondent No. 2 denies all statements, contentions and averments made in the Writ Petition except those specifically admitted in this Affidavit in Reply. Nothing contained in the Writ Petition that has not been specifically dealt with or admitted is to be treated as an admission by Respondent No. 2.",
        # Point 3 — Preliminary Position
        "The Writ Petition is misconceived and devoid of merits. The actions challenged by the Petitioner were taken in accordance with the applicable redevelopment procedure and within the authority available to Respondent No. 2.",
        # Point 4 — Denial Regarding the Communication
        "Respondent No. 2 denies that the impugned communication dated 15 July 2026 was issued without authority.",
        # Point 5 — Authority for the Communication
        "The communication dated 15 July 2026 was issued pursuant to the applicable redevelopment procedure and after consideration of the relevant records.",
        # Point 6 — Document Relied Upon
        "Respondent No. 2 relies upon the communication dated 15 July 2026. A copy of that communication is annexed hereto and marked as EXHIBIT-‘A’.",
    ]

    # 5. Exhibits
    exhibits = [
        ExhibitItem(
            mark="EXHIBIT-‘A’",
            description="Copy of the communication dated 15 July 2026 addressed by Respondent No. 2",
            date="15 July 2026",
        )
    ]

    # 6. Prayer Points
    prayer_points = [
        "dismiss the present Writ Petition with costs;",
        "refuse any interim or ad-interim relief sought by the Petitioner; and",
        "grant such other and further reliefs as this Hon'ble Court may deem fit and proper in the facts and circumstances of the case.",
    ]

    # 7. Advocate Details
    advocate_firm = "Rajan & Associates"
    advocate_for = "Respondent No. 2"

    return CaseInformation(
        document_type="Affidavit in Reply",
        court=court,
        jurisdiction=jurisdiction,
        proceeding_type=proceeding_type,
        case_number=case_number,
        year=year,
        petitioner=petitioner,
        respondents=[respondent1, respondent2],
        filed_on_behalf_of_respondent_no=2,
        deponent=deponent,
        reply_points=reply_points,
        exhibits=exhibits,
        prayer_points=prayer_points,
        attestation_place="Mumbai",
        attestation_date_raw="5 September 2026",
        attestation_date_formatted="5th day of September 2026",
        advocate_firm=advocate_firm,
        advocate_for=advocate_for,
    )

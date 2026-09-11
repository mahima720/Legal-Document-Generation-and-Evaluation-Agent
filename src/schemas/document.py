from pydantic import BaseModel, Field, model_validator
from typing import List, Tuple, Optional


class BodyParagraph(BaseModel):
    number: int = Field(..., ge=1, description="Paragraph number")
    move_type: str = Field(..., description="Legal move classification")
    text: str = Field(..., min_length=5, description="Full substantive legal text")
    source_reference: Optional[str] = Field(None, description="Source provenance marker")


class PrayerClause(BaseModel):
    letter: str = Field(..., description="Lettered marker, e.g. '(a)', '(b)', '(c)'")
    text: str = Field(..., min_length=5, description="Prayer relief text")


class JuratBlock(BaseModel):
    place: str = Field(default="Mumbai", description="Attestation location")
    date_line: str = Field(default="On this 5th day of September 2026", description="Attestation date string")
    deponent_marker: str = Field(default="DEPONENT", description="Right-aligned deponent tag")
    before_me_marker: str = Field(default="Before Me", description="Left-aligned Before Me tag")
    verb: str = Field(default="Solemnly affirmed", description="Jurat verb agreeing with deponent clause")


class VerificationBlock(BaseModel):
    heading: str = Field(default="VERIFICATION", description="Section heading")
    deponent_name: str = Field(..., description="Name of deponent")
    paragraph_range_start: int = Field(default=1, description="Starting paragraph index")
    paragraph_range_end: int = Field(..., ge=1, description="Ending paragraph index")
    verification_text: str = Field(..., description="Full text of verification clause")
    place: str = Field(default="Mumbai", description="Place of verification")
    date_line: str = Field(default="on this 5th day of September 2026", description="Date of verification")
    deponent_marker: str = Field(default="DEPONENT", description="Right-aligned deponent tag")


class AdvocateBlock(BaseModel):
    firm_name: str = Field(..., description="Advocate firm or counsel name")
    advocate_for: str = Field(..., description="Party represented")


class AffidavitDocument(BaseModel):
    court_heading: str = Field(default="IN THE HIGH COURT OF JUDICATURE AT BOMBAY")
    jurisdiction: str = Field(default="ORDINARY ORIGINAL CIVIL JURISDICTION")
    case_number_line: str = Field(default="WRIT PETITION NO. 1847 OF 2026")
    cause_title_petitioner: str = Field(...)
    cause_title_petitioner_tag: str = Field(default="...Petitioner")
    cause_title_versus: str = Field(default="VERSUS")
    cause_title_respondents: List[Tuple[str, str]] = Field(
        ..., description="List of tuples: (Respondent details string, status tag)"
    )
    affidavit_title: str = Field(default="AFFIDAVIT IN REPLY ON BEHALF OF RESPONDENT NO. 2")
    deponent_clause: str = Field(...)
    body_paragraphs: List[BodyParagraph] = Field(..., min_length=1)
    prayer_heading: str = Field(default="PRAYER")
    prayer_clauses: List[PrayerClause] = Field(..., min_length=1)
    jurat: JuratBlock = Field(...)
    verification: VerificationBlock = Field(...)
    advocate_block: AdvocateBlock = Field(...)

    @model_validator(mode="after")
    def validate_invariants(self) -> "AffidavitDocument":
        # Invariant 1: Monotonic paragraph numbering 1 to N
        for idx, p in enumerate(self.body_paragraphs, start=1):
            if p.number != idx:
                raise ValueError(f"Body paragraph numbering out of sequence: expected {idx}, got {p.number}")

        # Invariant 2: Verification paragraph range must dynamically match actual body paragraph count
        body_count = len(self.body_paragraphs)
        if self.verification.paragraph_range_end != body_count:
            raise ValueError(
                f"Verification paragraph_range_end ({self.verification.paragraph_range_end}) "
                f"does not match actual body paragraph count ({body_count})"
            )

        expected_range_str = f"paragraphs 1 to {body_count}"
        if expected_range_str not in self.verification.verification_text.lower():
            raise ValueError(
                f"Verification text missing expected range '{expected_range_str}': "
                f"found '{self.verification.verification_text}'"
            )

        return self

from pydantic import BaseModel, Field, model_validator
from typing import List, Optional
from src.schemas.case_info import CaseInformation
from src.schemas.template import LegalMoveType


class EvidenceSource(BaseModel):
    source_file: str = Field(default="03_Case_Information.pdf", description="Source document name")
    source_section: str = Field(..., description="Section inside source document")
    source_point_label: Optional[str] = Field(None, description="e.g. 'Point 1 — Filing of Affidavit in Reply'")
    source_text: str = Field(..., description="Raw text from the input case information")


class ContentMappingItem(BaseModel):
    target_paragraph_number: Optional[int] = Field(None, ge=1, description="Target body paragraph index, or None if Prayer")
    target_section: str = Field(..., description="Target document section, e.g. 'Numbered Paragraphs, Paragraph 1'")
    move_type: LegalMoveType = Field(..., description="Structural legal move")
    source_evidence: EvidenceSource = Field(..., description="Evidence provenance mapping")
    intent: str = Field(..., description="Drafting objective for this item")
    required_phrases: List[str] = Field(default_factory=list, description="Fixed court phrases to include")


class ContentPlan(BaseModel):
    case_info: CaseInformation = Field(..., description="Structured case input data")
    mappings: List[ContentMappingItem] = Field(..., min_length=1, description="Ordered mapping from evidence to paragraphs/prayer")
    expected_body_paragraph_count: int = Field(..., ge=1, description="Total expected body paragraphs")
    expected_verification_range: str = Field(..., description="Expected verification range string (e.g. 'paragraphs 1 to 7')")

    @model_validator(mode="after")
    def validate_range_matches_count(self) -> "ContentPlan":
        expected_str = f"paragraphs 1 to {self.expected_body_paragraph_count}"
        if self.expected_verification_range.strip().lower() != expected_str.lower():
            raise ValueError(
                f"expected_verification_range '{self.expected_verification_range}' does not match "
                f"expected body count {self.expected_body_paragraph_count} ('{expected_str}')"
            )
        return self

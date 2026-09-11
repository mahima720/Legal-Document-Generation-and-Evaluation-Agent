from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum


class SectionType(str, Enum):
    FORUM_HEADING = "FORUM_HEADING"
    JURISDICTION = "JURISDICTION"
    CASE_NUMBER = "CASE_NUMBER"
    CAUSE_TITLE = "CAUSE_TITLE"
    AFFIDAVIT_TITLE = "AFFIDAVIT_TITLE"
    DEPONENT_CLAUSE = "DEPONENT_CLAUSE"
    NUMBERED_PARAGRAPHS = "NUMBERED_PARAGRAPHS"
    PRAYER = "PRAYER"
    JURAT = "JURAT"
    VERIFICATION = "VERIFICATION"
    ADVOCATE_BLOCK = "ADVOCATE_BLOCK"


class LegalMoveType(str, Enum):
    IDENTITY_AND_PERUSAL = "IDENTITY_AND_PERUSAL"
    BLANKET_DENIAL = "BLANKET_DENIAL"
    PRELIMINARY_POSITION = "PRELIMINARY_POSITION"
    SUBSTANTIVE_ANSWER = "SUBSTANTIVE_ANSWER"
    DOCUMENT_RELIED_UPON = "DOCUMENT_RELIED_UPON"
    CLOSING = "CLOSING"
    PRAYER_TO_DISMISS = "PRAYER_TO_DISMISS"


class TemplateSection(BaseModel):
    order: int = Field(..., ge=1, le=11, description="Strict 1-indexed section order")
    name: str = Field(..., description="Section title or name")
    section_type: SectionType = Field(..., description="Type of structural section")
    is_mandatory: bool = Field(default=True, description="Whether section is compulsory")
    formatting_rules: List[str] = Field(default_factory=list, description="Typesetting rules for this section")


class AffidavitTemplate(BaseModel):
    name: str = Field(default="Affidavit in Reply - Bombay High Court Standard", description="Template name")
    court_seat: str = Field(default="BOMBAY", description="Court seat")
    sections: List[TemplateSection] = Field(..., min_length=10, description="10 mandatory structural sections")
    fixed_phrases: Dict[str, str] = Field(default_factory=dict, description="Standard court boilerplate phrases")
    rules: List[str] = Field(default_factory=list, description="Core legal formatting rules")

    def get_section(self, section_type: SectionType) -> Optional[TemplateSection]:
        for s in self.sections:
            if s.section_type == section_type:
                return s
        return None

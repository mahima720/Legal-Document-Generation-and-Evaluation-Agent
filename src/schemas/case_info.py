from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional
from enum import Enum


class PartyRole(str, Enum):
    PETITIONER = "Petitioner"
    RESPONDENT = "Respondent"


class PartyType(str, Enum):
    INDIVIDUAL = "Individual"
    AUTHORITY = "Authority"
    COMPANY = "Company"


class Party(BaseModel):
    name: str = Field(..., description="Full legal name of the party")
    party_type: PartyType = Field(default=PartyType.INDIVIDUAL, description="Individual, Authority, or Company")
    role: PartyRole = Field(..., description="Petitioner or Respondent")
    respondent_number: Optional[int] = Field(None, description="Number if respondent (e.g. 1, 2)")
    details: Optional[str] = Field(None, description="Party details such as age, occupation, address, or representation")
    status_tag: str = Field(..., description="Court status tag, e.g. '...Petitioner' or '...Respondent No.1'")


class DeponentDetails(BaseModel):
    name: str = Field(..., description="Name of the person deposing")
    designation: Optional[str] = Field(None, description="Designation if deposing on behalf of authority/company")
    organisation: Optional[str] = Field(None, description="Organisation/Authority represented")
    address: str = Field(..., description="Official office or residential address")
    verification_verb: str = Field(default="solemnly affirm", description="Affirmation verb: 'solemnly affirm' or 'swear'")
    capacity_formula: Optional[str] = Field(None, description="Legal capacity formula")

    @model_validator(mode="after")
    def validate_capacity_and_formula(self) -> "DeponentDetails":
        # Deponent Rule (Part 6 of Affidavit Format Explained):
        # Respondent is authority/company -> an officer deposes for it:
        # "the [designation] of the Respondent No.2 above named". Never "I am the Respondent No.2".
        if self.organisation:
            if not self.designation:
                raise ValueError("Deponent representing an organisation must have a designation.")
            if not self.capacity_formula:
                self.capacity_formula = f"the {self.designation} of the Respondent No.2 above named"
        elif not self.capacity_formula:
            self.capacity_formula = "the Respondent No.2 above named"
        return self


class ExhibitItem(BaseModel):
    mark: str = Field(..., description="Exhibit identifier, e.g. EXHIBIT-'A'")
    description: str = Field(..., description="Description of the exhibited document")
    date: Optional[str] = Field(None, description="Date on the exhibited document if applicable")


class CaseInformation(BaseModel):
    document_type: str = Field(default="Affidavit in Reply", description="Type of legal document")
    court: str = Field(default="IN THE HIGH COURT OF JUDICATURE AT BOMBAY", description="Court heading")
    jurisdiction: str = Field(..., description="Court jurisdiction side")
    proceeding_type: str = Field(default="WRIT PETITION", description="Proceeding type")
    case_number: str = Field(..., description="Proceeding case number")
    year: int = Field(..., description="Proceeding year")
    petitioner: Party = Field(..., description="Petitioner party details")
    respondents: List[Party] = Field(..., min_length=1, description="List of respondents")
    filed_on_behalf_of_respondent_no: int = Field(default=2, description="Which respondent is filing this reply")
    deponent: DeponentDetails = Field(..., description="Deponent personal and capacity details")
    reply_points: List[str] = Field(..., min_length=1, description="Substantive reply points to be incorporated")
    exhibits: List[ExhibitItem] = Field(default_factory=list, description="Exhibits referred to in the reply")
    prayer_points: List[str] = Field(..., min_length=1, description="Reliefs sought in the prayer")
    attestation_place: str = Field(default="Mumbai", description="Place of jurat and verification")
    attestation_date_raw: str = Field(default="5 September 2026", description="Raw date string")
    attestation_date_formatted: str = Field(default="5th day of September 2026", description="Court-formatted date string")
    advocate_firm: str = Field(..., description="Name of advocate or law firm")
    advocate_for: str = Field(default="Respondent No. 2", description="Party the advocate represents")

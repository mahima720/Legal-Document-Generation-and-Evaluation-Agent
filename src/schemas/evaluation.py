from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from enum import Enum


class ValidationSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CheckStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"


class ValidationIssue(BaseModel):
    check_id: str = Field(..., description="Unique check identifier, e.g. PRE_01 or CHK_08")
    check_name: str = Field(..., description="Human-readable check name")
    dimension: str = Field(default="Completeness", description="Target dimension among the 6 required areas")
    status: CheckStatus = Field(..., description="PASS, FAIL, or WARNING")
    expected: str = Field(..., description="Expected value or pattern")
    found: str = Field(..., description="Found value or pattern")
    severity: ValidationSeverity = Field(..., description="Severity of defect")
    field_or_section: Optional[str] = Field(None, description="Field or section examined")
    message: str = Field(..., description="Detailed diagnostic explanation")
    explanation: Optional[str] = Field(None, description="In-depth explanation of failure")
    evidence: Optional[str] = Field(None, description="Ground truth excerpt or quotation")
    remediation: Optional[str] = Field(None, description="Recommended remediation action")


class PreValidationResult(BaseModel):
    is_valid: bool = Field(..., description="Whether pre-generation validation passed overall")
    total_checks: int = Field(default=0, description="Total number of checks run")
    passed_count: int = Field(default=0, description="Number of passed checks")
    failed_count: int = Field(default=0, description="Number of failed checks")
    warning_count: int = Field(default=0, description="Number of warnings")
    issues: List[ValidationIssue] = Field(default_factory=list, description="List of detected validation issues")
    summary: str = Field(default="", description="Executive summary of pre-generation validation")


class DimensionScore(BaseModel):
    dimension_name: str = Field(..., description="Name of the evaluation area")
    weight: float = Field(..., ge=0.0, le=1.0, description="Dimension weight in overall score")
    base_score: float = Field(default=100.0, description="Starting score before deductions")
    deductions: float = Field(default=0.0, description="Total penalties deducted")
    final_score: float = Field(default=100.0, ge=0.0, le=100.0, description="Score after penalties")
    issues_count: int = Field(default=0, description="Number of issues detected")
    issues: List[ValidationIssue] = Field(default_factory=list, description="Issues impacting this dimension")


class EvaluationReport(BaseModel):
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Composite weighted score out of 100")
    dimension_scores: Dict[str, DimensionScore] = Field(..., description="Scores for the 6 required dimensions")
    all_issues: List[ValidationIssue] = Field(default_factory=list, description="Complete list of detected issues")
    summary_explanation: str = Field(..., description="Short explanation of how score was calculated")
    scoring_breakdown: List[str] = Field(default_factory=list, description="Step-by-step scoring formula explanation")
    document_metadata: Dict[str, str] = Field(default_factory=dict, description="Generated document metadata")

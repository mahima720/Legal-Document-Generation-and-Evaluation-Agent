from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List
from src.config import FILE_CASE_INFO, FILE_FORMAT_EXPLAINED, OUTPUTS_DIR
from src.ingestion.case_parser import parse_case_information
from src.ingestion.template_parser import load_authoritative_template
from src.mapping.mapper import map_case_to_content_plan
from src.validation.pre_validator import validate_case_information
from src.generation.drafter import AffidavitDrafter
from src.generation.docx_renderer import render_affidavit_to_docx
from src.validation.post_validator import validate_affidavit_document
from src.evaluation.semantic_evaluator import SemanticAuditor, SemanticEvaluationResult
from src.evaluation.scorer import ScoringEngine
from src.schemas.case_info import CaseInformation
from src.schemas.template import AffidavitTemplate
from src.schemas.content_plan import ContentPlan
from src.schemas.document import AffidavitDocument
from src.schemas.evaluation import PreValidationResult, EvaluationReport, ValidationIssue


@dataclass
class PipelineResult:
    success: bool
    case_info: CaseInformation
    template: AffidavitTemplate
    content_plan: ContentPlan
    pre_validation: PreValidationResult
    document_ir: Optional[AffidavitDocument]
    docx_path: Optional[Path]
    det_issues: List[ValidationIssue]
    semantic_result: Optional[SemanticEvaluationResult]
    report: Optional[EvaluationReport]
    json_report_path: Optional[Path]
    md_report_path: Optional[Path]
    error_message: Optional[str] = None


def run_legal_document_pipeline(
    case_pdf_path: Path = FILE_CASE_INFO,
    mode: str = "mock",
    api_key: Optional[str] = None,
    output_dir: Path = OUTPUTS_DIR,
) -> PipelineResult:
    """
    Executes the complete end-to-end Legal Document Generation & Evaluation pipeline:
    1. Ingestion: Ingests case information and authoritative Bombay High Court template.
    2. Content Mapping: Maps reply points and prayer to legal moves with provenance.
    3. Pre-Generation Validation: Validates all mandatory case input fields.
    4. Generation: Drafts AffidavitDocument IR in specified mode (mock or llm).
    5. DOCX Rendering: Compiles high-fidelity court filing DOCX.
    6. Post-Generation Validation: Runs 10 deterministic invariant checks.
    7. Semantic Evaluation: Performs semantic grounding audit and hallucination scan.
    8. Scoring & Reporting: Calculates 6-dimension scores and writes JSON & Markdown reports.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Ingestion
    case_info = parse_case_information(case_pdf_path)
    template = load_authoritative_template()

    # 2. Content Mapping
    content_plan = map_case_to_content_plan(case_info, template)

    # 3. Pre-Generation Validation
    pre_val = validate_case_information(case_info)
    if not pre_val.is_valid:
        return PipelineResult(
            success=False,
            case_info=case_info,
            template=template,
            content_plan=content_plan,
            pre_validation=pre_val,
            document_ir=None,
            docx_path=None,
            det_issues=[],
            semantic_result=None,
            report=None,
            json_report_path=None,
            md_report_path=None,
            error_message="Pre-generation validation failed. Halting generation.",
        )

    # 4. Generation
    drafter = AffidavitDrafter()
    try:
        doc_ir = drafter.draft(content_plan, mode=mode, api_key=api_key)
    except Exception as e:
        return PipelineResult(
            success=False,
            case_info=case_info,
            template=template,
            content_plan=content_plan,
            pre_validation=pre_val,
            document_ir=None,
            docx_path=None,
            det_issues=[],
            semantic_result=None,
            report=None,
            json_report_path=None,
            md_report_path=None,
            error_message=f"Generation failed: {str(e)}",
        )

    # 5. DOCX Rendering
    docx_path = output_dir / "generated_affidavit.docx"
    render_affidavit_to_docx(doc_ir, docx_path)

    # 6. Post-Generation Validation (10 checks)
    det_issues = validate_affidavit_document(doc_ir, case_info)

    # 7. Semantic Evaluation
    auditor = SemanticAuditor()
    sem_result = auditor.evaluate(doc_ir, case_info, content_plan, mode=mode, api_key=api_key)

    # 8. Scoring & Reporting
    scorer = ScoringEngine()
    report = scorer.score(doc_ir, case_info, det_issues, sem_result)

    json_path = output_dir / "evaluation_report.json"
    md_path = output_dir / "evaluation_report.md"
    scorer.write_reports(report, sem_result, json_path, md_path)

    return PipelineResult(
        success=True,
        case_info=case_info,
        template=template,
        content_plan=content_plan,
        pre_validation=pre_val,
        document_ir=doc_ir,
        docx_path=docx_path,
        det_issues=det_issues,
        semantic_result=sem_result,
        report=report,
        json_report_path=json_path,
        md_report_path=md_path,
        error_message=None,
    )

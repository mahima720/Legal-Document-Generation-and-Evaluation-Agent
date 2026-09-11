import subprocess
import sys
from pathlib import Path
import pytest
from unittest.mock import patch
from src.config import FILE_CASE_INFO, ASSIGNMENT_MATERIALS_DIR
from src.pipeline import run_legal_document_pipeline, PipelineResult
from src.schemas.evaluation import PreValidationResult, ValidationIssue, CheckStatus, ValidationSeverity


def test_pipeline_e2e_mock_success(tmp_path):
    """Verifies that the full pipeline executes cleanly in mock mode and generates all expected outputs."""
    result = run_legal_document_pipeline(
        case_pdf_path=FILE_CASE_INFO,
        mode="mock",
        output_dir=tmp_path,
    )

    assert isinstance(result, PipelineResult)
    assert result.success is True
    assert result.error_message is None

    # Check that case info and document IR are populated
    assert result.case_info.case_number == "1847"
    assert result.case_info.year == 2026
    assert result.document_ir is not None
    assert "1847" in result.document_ir.case_number_line
    assert len(result.document_ir.body_paragraphs) == 7

    # Check DOCX file
    assert result.docx_path.exists()
    assert result.docx_path.stat().st_size > 20000

    # Check reports
    assert result.json_report_path.exists()
    assert result.json_report_path.stat().st_size > 500
    assert result.md_report_path.exists()
    assert result.md_report_path.stat().st_size > 500

    # Check score and deterministic validation
    assert result.report.overall_score == 100.0
    assert len(result.det_issues) == 0
    assert not result.semantic_result.hallucination_detected


def test_pipeline_pre_validation_failure(tmp_path):
    """Verifies that the pipeline cleanly aborts if pre-generation validation fails."""
    mock_failed_pre = PreValidationResult(
        is_valid=False,
        total_checks=1,
        failed_count=1,
        issues=[
            ValidationIssue(
                check_id="PRE_01_TEST",
                check_name="Mandatory Field Check",
                dimension="Completeness",
                status=CheckStatus.FAIL,
                expected="Valid number",
                found="None",
                severity=ValidationSeverity.CRITICAL,
                field_or_section="case_number",
                message="Case number missing",
            )
        ],
        summary="Pre-generation validation failed.",
    )

    with patch("src.pipeline.validate_case_information", return_value=mock_failed_pre):
        result = run_legal_document_pipeline(
            case_pdf_path=FILE_CASE_INFO,
            mode="mock",
            output_dir=tmp_path,
        )

        assert result.success is False
        assert result.document_ir is None
        assert result.docx_path is None
        assert "Pre-generation validation failed" in result.error_message


def test_cli_runner_subprocess():
    """Verifies that run_pipeline.py executes cleanly as a standalone CLI command."""
    cmd = [sys.executable, "run_pipeline.py"]
    res = subprocess.run(cmd, capture_output=True, text=True)

    assert res.returncode == 0
    assert "Pipeline completed successfully." in res.stdout
    assert "Overall Score: 100.0 / 100" in res.stdout
    assert "Deterministic checks: 10/10 passed" in res.stdout
    assert "Hallucination detected: No" in res.stdout


def test_original_materials_unmodified():
    """Asserts that the assignment source materials remain intact and pristine."""
    expected_files = [
        "01_Affidavit_format_explained.pdf",
        "02_Affidavit_in_reply_sample.pdf",
        "03_Case_Information.pdf",
        "AI_Intern_Assignment.pdf",
    ]
    for fname in expected_files:
        fpath = ASSIGNMENT_MATERIALS_DIR / fname
        assert fpath.exists(), f"Missing assignment material: {fname}"
        assert fpath.stat().st_size > 0, f"Empty assignment material: {fname}"

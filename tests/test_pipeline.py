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


def test_pipeline_llm_mode_missing_api_key(tmp_path, monkeypatch):
    """Verifies that the pipeline explicitly rejects LLM mode when GEMINI_API_KEY is missing."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    result = run_legal_document_pipeline(
        case_pdf_path=FILE_CASE_INFO,
        mode="llm",
        api_key=None,
        output_dir=tmp_path,
    )

    assert result.success is False
    assert result.document_ir is None
    assert "GEMINI_API_KEY is required when running in LLM mode" in result.error_message


def test_pipeline_llm_mode_api_failure(tmp_path):
    """Verifies that Gemini API failures are honestly reported without silent mock fallback."""
    with patch("requests.post") as mock_post:
        mock_resp = mock_post.return_value
        mock_resp.status_code = 403
        mock_resp.json.return_value = {"error": {"message": "The caller does not have permission"}}
        mock_resp.text = "Permission denied"

        result = run_legal_document_pipeline(
            case_pdf_path=FILE_CASE_INFO,
            mode="llm",
            api_key="invalid_test_key",
            output_dir=tmp_path,
        )

        assert result.success is False
        assert result.document_ir is None
        assert "Generation failed: Gemini API call failed with status 403" in result.error_message


def test_pipeline_llm_mode_gemini_success(tmp_path):
    """Verifies end-to-end LLM mode execution with Gemini response, checking 10 post-checks and audit."""
    gemini_paragraphs_json = (
        '[\n'
        '  {"number": 1, "move_type": "deponent_identity_and_authority", "text": "I say that I am the Deputy Metropolitan Commissioner of the Respondent No.2 in the above Writ Petition and am well acquainted with the facts and circumstances of the case. I have perused the Petition and the documents annexed thereto and am competent to affirm this Affidavit in Reply on behalf of Respondent No. 2, Mumbai Metropolitan Region Development Authority."},\n'
        '  {"number": 2, "move_type": "general_denial", "text": "At the outset, I deny each and every allegation, contention and submission made in the Writ Petition, save and except those specifically admitted herein. I say that the Petition is misconceived, devoid of merits and is liable to be dismissed in limine. Nothing contained in the Writ Petition that has not been specifically dealt with or admitted is to be treated as an admission by Respondent No. 2."},\n'
        '  {"number": 3, "move_type": "preliminary_submission_authority", "text": "I say that the Writ Petition is misconceived and devoid of merits. The actions challenged by the Petitioner were taken strictly in accordance with the applicable redevelopment procedure and within the authority available to Respondent No. 2. Strictly in accordance with law and after following due procedure, no legal, constitutional or fundamental right of the Petitioner has been infringed."},\n'
        '  {"number": 4, "move_type": "substantive_denial_communication", "text": "With reference to the averments made in the Petition, I say that the same are false, incorrect and denied. Respondent No. 2 specifically denies that the impugned communication dated 15 July 2026 was issued without authority. The Petitioner has failed to make out any case warranting interference in the extraordinary writ jurisdiction of this Hon\'ble Court."},\n'
        '  {"number": 5, "move_type": "substantive_defense_procedure", "text": "I say that the communication dated 15 July 2026 was issued pursuant to the applicable redevelopment procedure and after consideration of the relevant records. The contention of the Petitioner to the contrary is baseless, incorrect and denied."},\n'
        '  {"number": 6, "move_type": "document_reliance_annexure", "text": "Respondent No. 2 relies upon the communication dated 15 July 2026. Hereto annexed and marked as EXHIBIT-‘A’ is a copy of the communication dated 15 July 2026 issued by Respondent No. 2."},\n'
        '  {"number": 7, "move_type": "prayer_closing", "text": "In the premises aforesaid, I say that the Writ Petition deserves to be dismissed with costs."}\n'
        ']'
    )

    fake_api_response = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": gemini_paragraphs_json}
                    ]
                }
            }
        ]
    }

    with patch("requests.post") as mock_post:
        mock_resp = mock_post.return_value
        mock_resp.status_code = 200
        mock_resp.json.return_value = fake_api_response

        result = run_legal_document_pipeline(
            case_pdf_path=FILE_CASE_INFO,
            mode="llm",
            api_key="valid_test_key",
            output_dir=tmp_path,
        )

        assert result.success is True
        assert result.document_ir is not None
        assert len(result.document_ir.body_paragraphs) == 7
        assert result.docx_path.exists()
        assert len(result.det_issues) == 0
        assert result.report.overall_score == 100.0
        assert not result.semantic_result.hallucination_detected
        assert result.semantic_result.mode == "llm (provider verified)"


def test_get_gemini_api_key_from_secrets(monkeypatch):
    """Verifies that get_gemini_api_key correctly reads from Streamlit Secrets."""
    import streamlit as st
    from app import get_gemini_api_key

    with patch.object(st, "secrets", {"GEMINI_API_KEY": "secret_key_value"}):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        assert get_gemini_api_key() == "secret_key_value"


def test_get_gemini_api_key_from_env_fallback(monkeypatch):
    """Verifies that get_gemini_api_key falls back to os.environ when st.secrets has no key."""
    import streamlit as st
    from app import get_gemini_api_key

    with patch.object(st, "secrets", {}):
        monkeypatch.setenv("GEMINI_API_KEY", "env_key_value")
        assert get_gemini_api_key() == "env_key_value"


def test_get_gemini_api_key_returns_none_when_unset(monkeypatch):
    """Verifies that get_gemini_api_key returns None when neither secrets nor env is set."""
    import streamlit as st
    from app import get_gemini_api_key

    with patch.object(st, "secrets", {}):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        assert get_gemini_api_key() is None


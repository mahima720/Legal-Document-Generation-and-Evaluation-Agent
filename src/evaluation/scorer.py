import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime
from src.schemas.case_info import CaseInformation
from src.schemas.document import AffidavitDocument
from src.schemas.evaluation import (
    ValidationIssue,
    ValidationSeverity,
    CheckStatus,
    DimensionScore,
    EvaluationReport,
)
from src.evaluation.semantic_evaluator import SemanticEvaluationResult


# Assignment-Approved Dimension Weights (Must sum to 1.0)
DIMENSION_WEIGHTS = {
    "Entity Accuracy": 0.20,
    "Completeness": 0.15,
    "Structure": 0.15,
    "Consistency": 0.15,
    "Template Fidelity": 0.15,
    "Hallucination": 0.20,
}

# Penalty Deductions by Severity
SEVERITY_DEDUCTIONS = {
    ValidationSeverity.CRITICAL: 25.0,
    ValidationSeverity.HIGH: 15.0,
    ValidationSeverity.MEDIUM: 10.0,
    ValidationSeverity.LOW: 5.0,
}


class ScoringEngine:
    """
    Hybrid Scoring Engine.
    Combines deterministic validation issues and semantic evaluation findings
    into transparent scores across the 6 required dimensions.
    Outputs:
    - evaluation_report.json
    - evaluation_report.md
    """

    def score(
        self,
        doc: AffidavitDocument,
        case_info: CaseInformation,
        deterministic_issues: List[ValidationIssue],
        semantic_result: SemanticEvaluationResult,
    ) -> EvaluationReport:
        dimension_scores: Dict[str, DimensionScore] = {}
        all_issues: List[ValidationIssue] = list(deterministic_issues)

        # Map semantic issues to ValidationIssues
        if semantic_result.hallucination_detected:
            for ev in semantic_result.hallucination_evidence:
                all_issues.append(
                    ValidationIssue(
                        check_id="SEM_HALLUCINATION",
                        check_name="Semantic Hallucination Check",
                        dimension="Hallucination",
                        status=CheckStatus.FAIL,
                        expected="Only supplied facts from Case Information",
                        found=ev,
                        severity=ValidationSeverity.CRITICAL,
                        field_or_section="semantic_content",
                        message=f"Hallucination detected: {ev}",
                        explanation="No extraneous legal facts, parties, dates, or claims may be introduced.",
                        evidence=ev,
                        remediation="Remove unsupported statement from generated content.",
                    )
                )

        if semantic_result.missing_meaning:
            for mis in semantic_result.missing_meaning:
                all_issues.append(
                    ValidationIssue(
                        check_id="SEM_COMPLETENESS",
                        check_name="Semantic Meaning Completeness",
                        dimension="Completeness",
                        status=CheckStatus.FAIL,
                        expected="Full expression of supplied case point",
                        found=mis,
                        severity=ValidationSeverity.HIGH,
                        field_or_section="body_paragraphs",
                        message=f"Missing substantive content: {mis}",
                        explanation="All reply points in Case Information must be represented.",
                        evidence=mis,
                        remediation="Draft the missing substantive point into the reply paragraphs.",
                    )
                )

        # Calculate scores per dimension
        scoring_breakdown: List[str] = []
        overall_score = 0.0

        for dim_name, weight in DIMENSION_WEIGHTS.items():
            dim_issues = [i for i in all_issues if i.dimension.lower() == dim_name.lower()]
            total_deductions = 0.0
            for iss in dim_issues:
                if iss.status == CheckStatus.FAIL:
                    deduction = SEVERITY_DEDUCTIONS.get(iss.severity, 10.0)
                    total_deductions += deduction

            final_score = max(0.0, 100.0 - total_deductions)
            weighted_contrib = final_score * weight
            overall_score += weighted_contrib

            dim_score_obj = DimensionScore(
                dimension_name=dim_name,
                weight=weight,
                base_score=100.0,
                deductions=total_deductions,
                final_score=final_score,
                issues_count=len(dim_issues),
                issues=dim_issues,
            )
            dimension_scores[dim_name] = dim_score_obj

            scoring_breakdown.append(
                f"{dim_name}: base 100.0 - deductions {total_deductions:.1f} = {final_score:.1f} (weight {weight:.2f} -> {weighted_contrib:.2f} pts)"
            )

        overall_score = round(overall_score, 1)

        summary_explanation = (
            f"Overall score {overall_score}/100 calculated across 6 dimensions using transparent "
            f"deterministic deductions and semantic grounding verification."
        )

        doc_metadata = {
            "case_number": case_info.case_number,
            "year": str(case_info.year),
            "petitioner": case_info.petitioner.name,
            "answering_respondent": f"Respondent No. {case_info.filed_on_behalf_of_respondent_no}",
            "body_paragraph_count": str(len(doc.body_paragraphs)),
            "verification_range": f"paragraphs 1 to {doc.verification.paragraph_range_end}",
            "semantic_mode": semantic_result.mode,
        }

        return EvaluationReport(
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            all_issues=all_issues,
            summary_explanation=summary_explanation,
            scoring_breakdown=scoring_breakdown,
            document_metadata=doc_metadata,
        )

    def write_reports(
        self,
        report: EvaluationReport,
        semantic_result: SemanticEvaluationResult,
        json_path: Path,
        md_path: Path,
    ):
        """Writes both JSON and human-readable Markdown evaluation reports."""
        json_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 1. Write JSON Report
        json_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")

        # 2. Write Markdown Report
        md_lines = [
            "# Evaluation Report: Legal Document Generation Agent",
            f"**Generated At:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
            f"**Case Number:** {report.document_metadata.get('case_number')} OF {report.document_metadata.get('year')}  ",
            f"**Answering Party:** {report.document_metadata.get('answering_respondent')}  ",
            f"**Evaluation Mode:** Hybrid (Deterministic Rules + Semantic Grounding [{semantic_result.mode}])  ",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            f"**Overall Score:** {report.overall_score} / 100  ",
            f"{report.summary_explanation}",
            "",
            "---",
            "",
            "## 1. Dimension Scores",
            "",
            "| Dimension | Weight | Base Score | Deductions | Final Score | Weighted Contribution | Issues |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]

        for dim_name, ds in report.dimension_scores.items():
            contrib = ds.final_score * ds.weight
            md_lines.append(
                f"| **{dim_name}** | {ds.weight:.2f} | {ds.base_score:.1f} | -{ds.deductions:.1f} | **{ds.final_score:.1f} / 100** | {contrib:.2f} | {ds.issues_count} |"
            )

        md_lines.extend([
            "",
            "**Composite Score Formula:**",
            "\\text{Overall Score} = 0.20 S_{\\text{Entity}} + 0.15 S_{\\text{Completeness}} + 0.15 S_{\\text{Structure}} + 0.15 S_{\\text{Consistency}} + 0.15 S_{\\text{Fidelity}} + 0.20 S_{\\text{Hallucination}}  ",
            "",
            "---",
            "",
            "## 2. Deterministic Validation Results (10 Checks)",
            "",
            "| Check ID | Check Name | Target Dimension | Severity | Status | Expected | Found |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ])

        det_checks = [
            ("CHK_01_REQUIRED_SECTIONS", "Required Section Presence", "Structure", "CRITICAL"),
            ("CHK_02_SECTION_ORDER", "Section Order Invariant", "Structure", "CRITICAL"),
            ("CHK_03_FORUM_JURISDICTION", "Forum & Jurisdiction Match", "Entity Accuracy", "HIGH"),
            ("CHK_04_CASE_NUMBER_YEAR", "Case Number & Year Match", "Entity Accuracy", "HIGH"),
            ("CHK_05_PARTY_RESPONDENT_CONSISTENCY", "Party & Respondent Consistency", "Consistency", "HIGH"),
            ("CHK_06_DEPONENT_CAPACITY", "Deponent Capacity Rule", "Template Fidelity", "HIGH"),
            ("CHK_07_SEQUENTIAL_NUMBERING", "Sequential Numbering", "Structure", "HIGH"),
            ("CHK_08_VERIFICATION_RANGE", "Dynamic Verification Range", "Consistency", "CRITICAL"),
            ("CHK_09_JURAT_VERIFICATION_VERB", "Jurat / Deponent Verb Agreement", "Template Fidelity", "MEDIUM"),
            ("CHK_10_PRAYER_EXHIBIT", "Prayer Structure & Exhibit Grounding", "Completeness", "HIGH"),
        ]

        failed_check_ids = {i.check_id: i for i in report.all_issues if i.check_id.startswith("CHK_")}

        for cid, cname, cdim, csev in det_checks:
            if cid in failed_check_ids:
                iss = failed_check_ids[cid]
                exp_short = iss.expected[:35] + "..." if len(iss.expected) > 35 else iss.expected
                fnd_short = iss.found[:35] + "..." if len(iss.found) > 35 else iss.found
                md_lines.append(f"| {cid} | {cname} | {cdim} | {csev} | ❌ FAIL | {exp_short} | {fnd_short} |")
            else:
                md_lines.append(f"| {cid} | {cname} | {cdim} | {csev} | ✅ PASS | Verified | Satisfied |")

        md_lines.extend([
            "",
            "---",
            "",
            "## 3. Semantic Evaluation & Hallucination Audit",
            "",
            f"- **Execution Mode:** {semantic_result.mode}",
            f"- **Supported by Ground Truth:** {'Yes' if semantic_result.supported else 'No'}",
            f"- **Hallucination Detected:** {'Yes' if semantic_result.hallucination_detected else 'No'}",
            f"- **Grounding Score:** {semantic_result.grounding_score:.1f} / 100",
            "",
            "### Meaning Preservation Observations",
        ])

        for note in semantic_result.meaning_preservation_notes:
            md_lines.append(f"- ✅ {note}")

        if semantic_result.unsupported_claims:
            md_lines.append("### Unsupported / Hallucinated Claims")
            for claim in semantic_result.unsupported_claims:
                md_lines.append(f"- ❌ {claim}")

        md_lines.extend([
            "",
            "---",
            "",
            "## 4. Issues Detected & Remediation",
            "",
        ])

        if not report.all_issues:
            md_lines.append("No defects detected. All deterministic invariants and semantic checks satisfied.")
        else:
            for idx, iss in enumerate(report.all_issues, start=1):
                md_lines.extend([
                    f"### Issue {idx}: {iss.check_name} ({iss.check_id})",
                    f"- **Severity:** {iss.severity.value.upper()}",
                    f"- **Dimension Affected:** {iss.dimension}",
                    f"- **Field / Section:** {iss.field_or_section}",
                    f"- **Message:** {iss.message}",
                    f"- **Why it matters:** {iss.explanation}",
                    f"- **Expected:** {iss.expected}",
                    f"- **Found:** {iss.found}",
                    f"- **Recommended Remediation:** {iss.remediation or 'Review against court requirements.'}",
                    "",
                ])

        md_lines.extend([
            "---",
            "",
            "## 5. Scoring Explanation",
            "",
            "Each dimension starts at a baseline of 100 points. Deductions are strictly proportional to issue severity:",
            "- CRITICAL Severity: -25.0 points (Fatal structural defects, e.g., verification range mismatch)",
            "- HIGH Severity: -15.0 points (Substantive omissions, party/jurisdiction mismatch, ungrounded claims)",
            "- MEDIUM Severity: -10.0 points (Stylistic or procedural deviations, e.g., verb disagreement)",
            "- LOW Severity: -5.0 points (Minor formatting irregularities)",
            "",
            "Deterministic failures are authoritative and cannot be overridden by subjective LLM ratings.",
        ])

        md_path.write_text("\n".join(md_lines), encoding="utf-8")

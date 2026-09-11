import sys
from pathlib import Path
from src.pipeline import run_legal_document_pipeline


def main():
    print("==================================================")
    print("Legal Document Generation & Evaluation Agent")
    print("Proof of Concept — Bombay High Court Affidavit in Reply")
    print("==================================================\n")

    result = run_legal_document_pipeline(mode="mock")

    if not result.success:
        print(f"FAILED: {result.error_message}")
        for iss in result.pre_validation.issues:
            print(f"  - [{iss.check_id}] {iss.message}")
        sys.exit(1)

    print("Pipeline completed successfully.\n")
    print("Generated document:")
    print(f"  {result.docx_path}\n")

    print("Evaluation report:")
    print(f"  {result.json_report_path}")
    print(f"  {result.md_report_path}\n")

    rep = result.report
    print(f"Overall Score: {rep.overall_score} / 100\n")

    for dim_name, ds in rep.dimension_scores.items():
        print(f"  {dim_name:18}: {ds.final_score:5.1f} / 100 (weight {ds.weight:.2f})")

    failed_det = len([i for i in result.det_issues if i.status.value == "FAIL"])
    passed_det = 10 - failed_det
    print(f"\nDeterministic checks: {passed_det}/10 passed")
    print(f"Semantic mode: {result.semantic_result.mode}")
    print(f"Hallucination detected: {'Yes' if result.semantic_result.hallucination_detected else 'No'}")
    print("\n==================================================")


if __name__ == "__main__":
    main()

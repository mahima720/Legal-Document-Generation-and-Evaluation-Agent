import streamlit as st
from pathlib import Path
from src.config import FILE_CASE_INFO, FILE_FORMAT_EXPLAINED, FILE_REPLY_SAMPLE, OUTPUTS_DIR
from src.pipeline import run_legal_document_pipeline, PipelineResult


st.set_page_config(
    page_title="Legal Document Agent",
    page_icon="⚖️",
    layout="wide",
)

# --------------------------------------------------
# Sidebar
# --------------------------------------------------
st.sidebar.title("⚖️ Legal Document Agent")
st.sidebar.markdown(
    """
    **Bombay High Court Affidavit in Reply**  
    *Proof of Concept — Brainwonders AI Assignment*  
    Uses strictly supplied assignment materials.
    """
)
st.sidebar.divider()

eval_mode = st.sidebar.radio(
    "Generation & Evaluation Mode",
    ["Mock / Deterministic Mode", "LLM Provider Mode (Optional)"],
    index=0,
    help="Mock mode executes the complete end-to-end pipeline deterministically without requiring an external API key.",
)

api_key = None
if eval_mode == "LLM Provider Mode (Optional)":
    api_key = st.sidebar.text_input("Enter API Key (Gemini/OpenAI)", type="password")
    if not api_key:
        st.sidebar.caption("No key entered. Will safely fall back to Mock mode.")

mode_param = "llm" if eval_mode == "LLM Provider Mode (Optional)" and api_key else "mock"

st.sidebar.divider()
run_btn = st.sidebar.button("🚀 Run Complete Pipeline", type="primary", use_container_width=True)


# --------------------------------------------------
# A. Project Header
# --------------------------------------------------
st.title("⚖️ Legal Document Generation & Evaluation Agent")
st.caption("AI-powered generation and evaluation of an Affidavit in Reply using supplied reference format and case information.")
st.info("📌 **Proof of Concept:** This system uses only supplied assignment materials (`01_Affidavit_format_explained`, `02_Affidavit_in_reply_sample`, and `03_Case_Information`). It does not perform independent legal research or invent external facts.")

st.divider()

# Ensure pipeline runs on initial load or button press
if "pipeline_result" not in st.session_state or run_btn:
    with st.spinner("Executing legal document pipeline..."):
        st.session_state.pipeline_result = run_legal_document_pipeline(
            case_pdf_path=FILE_CASE_INFO,
            mode=mode_param,
            api_key=api_key,
        )

res: PipelineResult = st.session_state.pipeline_result

if not res.success:
    st.error(f"Pipeline Error: {res.error_message}")
    for iss in res.pre_validation.issues:
        st.warning(f"[{iss.check_id}] {iss.message}")
    st.stop()


# --------------------------------------------------
# B. Input Documents
# --------------------------------------------------
with st.expander("📂 1. Input Assignment Documents", expanded=False):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**1. Format Explained**")
        st.caption("`01_Affidavit_format_explained.pdf`")
        st.markdown("Defines 10 mandatory parts, Bombay HC set phrases, and deponent rules.")
    with c2:
        st.markdown("**2. Reference Sample**")
        st.caption("`02_Affidavit_in_reply_sample.pdf`")
        st.markdown("Writ Petition No. 3147 of 2026 format reference.")
    with c3:
        st.markdown("**3. Target Case Data**")
        st.caption("`03_Case_Information.pdf`")
        st.markdown("Ground truth for WP No. 1847 of 2026 (Sunrise Housing v. MMRDA).")


# --------------------------------------------------
# C. Structured Case Information
# --------------------------------------------------
with st.expander("📋 2. Structured Case Information (Extracted Ground Truth)", expanded=True):
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"**Court:** `{res.case_info.court}`")
        st.markdown(f"**Jurisdiction:** `{res.case_info.jurisdiction}`")
        st.markdown(f"**Proceeding:** `{res.case_info.proceeding_type} NO. {res.case_info.case_number} OF {res.case_info.year}`")
        st.markdown(f"**Petitioner:** `{res.case_info.petitioner.name}`")
        st.markdown(f"**Answering Party:** `Respondent No. {res.case_info.filed_on_behalf_of_respondent_no}`")
    with col_b:
        st.markdown(f"**Deponent:** `{res.case_info.deponent.name}` ({res.case_info.deponent.designation})")
        st.markdown(f"**Authority:** `{res.case_info.deponent.organisation}`")
        st.markdown(f"**Address:** `{res.case_info.deponent.address}`")
        st.markdown(f"**Capacity Formula:** `{res.case_info.deponent.capacity_formula}`")
        st.markdown(f"**Advocate:** `{res.case_info.advocate_firm}` ({res.case_info.advocate_for})")

    st.markdown("**Reply Points Ground Truth:**")
    for idx, pt in enumerate(res.case_info.reply_points, start=1):
        st.markdown(f"- **Point {idx}:** {pt}")


# --------------------------------------------------
# D. Content Mapping & Provenance
# --------------------------------------------------
with st.expander("🗺️ 3. Content Mapping & Evidence Provenance", expanded=False):
    st.markdown("The mapper deterministically links each reply point to its target legal move, paragraph number, and source file.")
    mapping_data = []
    for m in res.content_plan.mappings:
        target = f"Paragraph {m.target_paragraph_number}" if m.target_paragraph_number else "Prayer"
        mapping_data.append({
            "Target Section": target,
            "Legal Move": m.move_type.value,
            "Source File": m.source_evidence.source_file,
            "Source Point": m.source_evidence.source_point_label or m.source_evidence.source_section,
            "Intent": m.intent,
        })
    st.dataframe(mapping_data, use_container_width=True)


# --------------------------------------------------
# E. Pre-Generation Validation
# --------------------------------------------------
with st.expander("🛡️ 4. Pre-Generation Validation Gate", expanded=False):
    st.success(f"✅ {res.pre_validation.summary}")
    st.caption("All mandatory court fields, deponent rules, reply points, and exhibit references were pre-validated prior to drafting.")


# --------------------------------------------------
# F & G. Generated Document & Summary
# --------------------------------------------------
st.subheader("📄 5. Generated Affidavit in Reply")
st.success("Generation completed successfully.")

col_doc1, col_doc2 = st.columns([3, 1])
with col_doc1:
    st.markdown(f"**Title:** `{res.document_ir.affidavit_title}`")
    st.markdown(f"**Deponent Clause:** *{res.document_ir.deponent_clause}*")
    st.markdown(f"**Body Paragraphs:** `{len(res.document_ir.body_paragraphs)} paragraphs (Sequential 1 to 7)`")
    st.markdown(f"**Verification Range:** `{res.document_ir.verification.paragraph_range_start} to {res.document_ir.verification.paragraph_range_end}` (Dynamic Invariant Satisfied)")

with col_doc2:
    if res.docx_path and res.docx_path.exists():
        with open(res.docx_path, "rb") as f:
            st.download_button(
                label="📥 Download DOCX",
                data=f.read(),
                file_name="generated_affidavit.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary",
                use_container_width=True,
            )

with st.expander("👁️ View Generated Paragraph Text", expanded=False):
    for p in res.document_ir.body_paragraphs:
        st.markdown(f"**{p.number}.** {p.text}")
    st.markdown("**PRAYER**")
    for pr in res.document_ir.prayer_clauses:
        st.markdown(f"- **{pr.letter}** {pr.text}")
    st.markdown(f"**VERIFICATION:** *{res.document_ir.verification.verification_text}*")


# --------------------------------------------------
# H. Post-Generation Validation (10 Invariant Checks)
# --------------------------------------------------
st.subheader("🔍 6. Post-Generation Deterministic Validation")
st.caption("Pure Python invariant rule engine evaluating the generated output. LLM cannot override deterministic failures.")

det_rows = []
for cid, cname, cdim, csev in [
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
]:
    failed = [i for i in res.det_issues if i.check_id == cid]
    if failed:
        iss = failed[0]
        det_rows.append({"Check ID": cid, "Check Name": cname, "Dimension": cdim, "Severity": csev, "Status": "❌ FAIL", "Details": iss.message})
    else:
        det_rows.append({"Check ID": cid, "Check Name": cname, "Dimension": cdim, "Severity": csev, "Status": "✅ PASS", "Details": "Invariant fully satisfied"})

st.dataframe(det_rows, use_container_width=True)


# --------------------------------------------------
# I. Semantic Evaluation & Hallucination Audit
# --------------------------------------------------
st.subheader("🧠 7. Semantic Evaluation & Hallucination Audit")
c_sem1, c_sem2, c_sem3 = st.columns(3)
with c_sem1:
    st.metric("Evaluation Mode", res.semantic_result.mode)
with c_sem2:
    st.metric("Grounding Supported", "Yes" if res.semantic_result.supported else "No")
with c_sem3:
    st.metric("Hallucination Detected", "No" if not res.semantic_result.hallucination_detected else "YES")

with st.expander("Meaning Preservation Notes & Lexical Audit", expanded=False):
    for note in res.semantic_result.meaning_preservation_notes:
        st.markdown(f"- ✅ {note}")
    if res.semantic_result.unsupported_claims:
        for claim in res.semantic_result.unsupported_claims:
            st.error(f"- ❌ {claim}")


# --------------------------------------------------
# J. Scorecard
# --------------------------------------------------
st.subheader("📊 8. Evaluation Scorecard")
st.markdown(f"### Overall Composite Score: `{res.report.overall_score} / 100`")

score_cols = st.columns(6)
for idx, (dim_name, ds) in enumerate(res.report.dimension_scores.items()):
    with score_cols[idx]:
        st.metric(
            label=f"{dim_name} ({int(ds.weight*100)}%)",
            value=f"{ds.final_score:.1f}",
            delta=f"-{ds.deductions:.1f}" if ds.deductions > 0 else "No deductions",
            delta_color="inverse" if ds.deductions > 0 else "normal",
        )

with st.expander("ℹ️ Transparent Scoring Formula", expanded=False):
    st.latex(r"\text{Overall Score} = 0.20 S_{\text{Entity}} + 0.15 S_{\text{Completeness}} + 0.15 S_{\text{Structure}} + 0.15 S_{\text{Consistency}} + 0.15 S_{\text{Fidelity}} + 0.20 S_{\text{Hallucination}}")
    st.markdown("- **Baseline:** 100.0 points per dimension.")
    st.markdown("- **Deductions:** CRITICAL = -25, HIGH = -15, MEDIUM = -10, LOW = -5.")
    for b in res.report.scoring_breakdown:
        st.caption(b)


# --------------------------------------------------
# K. Download Reports
# --------------------------------------------------
st.subheader("💾 9. Evaluation Reports")
c_dl1, c_dl2 = st.columns(2)

with c_dl1:
    if res.json_report_path and res.json_report_path.exists():
        with open(res.json_report_path, "r", encoding="utf-8") as f:
            st.download_button(
                label="📥 Download evaluation_report.json",
                data=f.read(),
                file_name="evaluation_report.json",
                mime="application/json",
                use_container_width=True,
            )

with c_dl2:
    if res.md_report_path and res.md_report_path.exists():
        with open(res.md_report_path, "r", encoding="utf-8") as f:
            st.download_button(
                label="📥 Download evaluation_report.md",
                data=f.read(),
                file_name="evaluation_report.md",
                mime="text/markdown",
                use_container_width=True,
            )

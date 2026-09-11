from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from src.schemas.document import AffidavitDocument


def render_affidavit_to_docx(
    doc_ir: AffidavitDocument,
    output_path: Path,
) -> Path:
    """
    Renders an AffidavitDocument Pydantic IR into a court-ready DOCX document.
    Reproduces Bombay High Court structural formatting:
    - 1 inch margins
    - Times New Roman 12pt, 1.5 line spacing
    - Centred, Bold, ALL CAPS headings
    - Cause title with left party names and right status tags (...Petitioner, ...Respondent No.1)
    - Centred VERSUS on its own line
    - Numbered paragraphs with bold numerals (1. to N.) and justified text
    - Prayer section with bold letters ((a), (b), (c))
    - Jurat with Before Me (left) and DEPONENT (right)
    - Dynamic verification range referring to paragraphs 1 to N
    - Left-aligned advocate drafting block
    """
    doc = Document()

    # Configure Margins (1 inch all around)
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Configure Default Style
    normal_style = doc.styles["Normal"]
    normal_font = normal_style.font
    normal_font.name = "Times New Roman"
    normal_font.size = Pt(12)
    normal_font.color.rgb = RGBColor(0, 0, 0)
    normal_style.paragraph_format.line_spacing = 1.5
    normal_style.paragraph_format.space_after = Pt(6)

    def add_centered_heading(text: str):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(text)
        run.bold = True
        return p

    # 1. Forum Heading
    add_centered_heading(doc_ir.court_heading)

    # 2. Jurisdiction
    add_centered_heading(doc_ir.jurisdiction)

    # 3. Case Number
    p_case = add_centered_heading(doc_ir.case_number_line)
    p_case.paragraph_format.space_after = Pt(18)

    # 4. Cause Title Table (2 columns: Party on left, status tag on right)
    table = doc.add_table(rows=0, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    def add_cause_row(left_text: str, right_tag: str):
        row = table.add_row()
        c_left, c_right = row.cells[0], row.cells[1]
        c_left.width = Inches(4.5)
        c_right.width = Inches(2.0)

        p_left = c_left.paragraphs[0]
        p_left.paragraph_format.line_spacing = 1.15
        p_left.paragraph_format.space_after = Pt(4)
        p_left.add_run(left_text)

        p_right = c_right.paragraphs[0]
        p_right.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p_right.paragraph_format.line_spacing = 1.15
        p_right.paragraph_format.space_after = Pt(4)
        p_right.add_run(right_tag)

    # Petitioner Row
    add_cause_row(doc_ir.cause_title_petitioner, doc_ir.cause_title_petitioner_tag)

    # VERSUS Row
    row_v = table.add_row()
    c_v_left = row_v.cells[0]
    p_v = c_v_left.paragraphs[0]
    p_v.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_v.paragraph_format.space_before = Pt(8)
    p_v.paragraph_format.space_after = Pt(8)
    run_v = p_v.add_run(doc_ir.cause_title_versus)
    run_v.bold = True

    # Respondents Rows
    for resp_desc, resp_tag in doc_ir.cause_title_respondents:
        add_cause_row(resp_desc, resp_tag)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # 5. Affidavit Title
    p_aff_title = add_centered_heading(doc_ir.affidavit_title)
    p_aff_title.paragraph_format.space_after = Pt(14)

    # 6. Deponent Clause
    p_dep = doc.add_paragraph()
    p_dep.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_dep.paragraph_format.space_after = Pt(12)
    p_dep.add_run(doc_ir.deponent_clause)

    # 7. Numbered Paragraphs (1 to N)
    for p_item in doc_ir.body_paragraphs:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_after = Pt(10)
        
        # Bold numeral followed by full stop
        run_num = p.add_run(f"{p_item.number}. ")
        run_num.bold = True
        
        # Paragraph text
        p.add_run(p_item.text)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # 8. Prayer Section
    add_centered_heading(doc_ir.prayer_heading)

    p_prayer_lead = doc.add_paragraph()
    p_prayer_lead.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_prayer_lead.paragraph_format.space_after = Pt(8)
    p_prayer_lead.add_run("I therefore respectfully pray that this Hon'ble Court may be pleased to:")

    for prayer in doc_ir.prayer_clauses:
        p_clause = doc.add_paragraph()
        p_clause.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_clause.paragraph_format.left_indent = Inches(0.4)
        p_clause.paragraph_format.space_after = Pt(6)

        run_letter = p_clause.add_run(f"{prayer.letter} ")
        run_letter.bold = True
        p_clause.add_run(prayer.text)

    doc.add_paragraph().paragraph_format.space_after = Pt(14)

    # 9. Jurat (Attestation) Table
    t_jurat = doc.add_table(rows=2, cols=2)
    t_jurat.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_jurat.autofit = False

    r0 = t_jurat.rows[0]
    r0.cells[0].width = Inches(4.0)
    r0.cells[1].width = Inches(2.5)
    p_jurat_info = r0.cells[0].paragraphs[0]
    p_jurat_info.paragraph_format.line_spacing = 1.15
    p_jurat_info.add_run(f"{doc_ir.jurat.verb} at {doc_ir.jurat.place}\n{doc_ir.jurat.date_line}")

    r1 = t_jurat.rows[1]
    r1.cells[0].width = Inches(4.0)
    r1.cells[1].width = Inches(2.5)
    
    p_before_me = r1.cells[0].paragraphs[0]
    p_before_me.paragraph_format.space_before = Pt(14)
    p_before_me.add_run(doc_ir.jurat.before_me_marker)

    p_dep_sig = r1.cells[1].paragraphs[0]
    p_dep_sig.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_dep_sig.paragraph_format.space_before = Pt(14)
    run_dep = p_dep_sig.add_run(doc_ir.jurat.deponent_marker)
    run_dep.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(14)

    # 10. Verification Block
    add_centered_heading(doc_ir.verification.heading)

    p_verif = doc.add_paragraph()
    p_verif.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_verif.paragraph_format.space_after = Pt(8)
    p_verif.add_run(doc_ir.verification.verification_text)

    t_verif_close = doc.add_table(rows=1, cols=2)
    t_verif_close.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_verif_close.autofit = False
    
    r_vc = t_verif_close.rows[0]
    r_vc.cells[0].width = Inches(4.0)
    r_vc.cells[1].width = Inches(2.5)

    p_v_place_date = r_vc.cells[0].paragraphs[0]
    p_v_place_date.add_run(f"Verified at {doc_ir.verification.place} {doc_ir.verification.date_line}.")

    p_v_dep = r_vc.cells[1].paragraphs[0]
    p_v_dep.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run_v_dep = p_v_dep.add_run(doc_ir.verification.deponent_marker)
    run_v_dep.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(20)

    # 11. Advocate Signature Block
    p_adv = doc.add_paragraph()
    p_adv.paragraph_format.line_spacing = 1.15
    run_adv_firm = p_adv.add_run(doc_ir.advocate_block.firm_name)
    run_adv_firm.bold = True
    p_adv.add_run(f"\n{doc_ir.advocate_block.advocate_for}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    return output_path

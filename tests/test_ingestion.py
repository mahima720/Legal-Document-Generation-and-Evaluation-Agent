from pathlib import Path
from src.config import FILE_CASE_INFO, FILE_FORMAT_EXPLAINED
from src.ingestion.pdf_extractor import extract_text_from_pdf
from src.ingestion.case_parser import parse_case_information
from src.ingestion.template_parser import load_authoritative_template


def test_pdf_extractor():
    assert FILE_CASE_INFO.exists(), f"Missing {FILE_CASE_INFO}"
    text = extract_text_from_pdf(FILE_CASE_INFO, normalize_whitespace=True)
    assert "CASE INFORMATION" in text.upper()
    assert "1847" in text
    assert "Sunrise Housing" in text


def test_case_parser():
    case_info = parse_case_information(FILE_CASE_INFO)
    assert case_info.court == "IN THE HIGH COURT OF JUDICATURE AT BOMBAY"
    assert case_info.jurisdiction == "ORDINARY ORIGINAL CIVIL JURISDICTION"
    assert case_info.case_number == "1847"
    assert case_info.year == 2026
    assert case_info.petitioner.name == "Sunrise Housing Private Limited"
    assert len(case_info.respondents) == 2
    assert case_info.respondents[1].name == "Mumbai Metropolitan Region Development Authority"
    assert case_info.deponent.name == "Arvind Rajan"
    assert case_info.deponent.designation == "Deputy Metropolitan Commissioner"
    assert len(case_info.reply_points) == 6
    assert len(case_info.exhibits) == 1
    assert case_info.exhibits[0].mark == "EXHIBIT-‘A’"
    assert case_info.advocate_firm == "Rajan & Associates"


def test_template_parser():
    template = load_authoritative_template()
    assert len(template.sections) >= 10
    assert template.court_seat == "BOMBAY"
    assert "identity_and_perusal" in template.fixed_phrases
    assert "blanket_denial" in template.fixed_phrases
    assert any("paragraphs 1 to N" in rule for rule in template.rules)

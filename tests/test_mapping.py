import pytest
from src.config import FILE_CASE_INFO
from src.ingestion.case_parser import parse_case_information
from src.mapping.mapper import map_case_to_content_plan
from src.schemas.template import LegalMoveType


@pytest.fixture
def case_info():
    return parse_case_information(FILE_CASE_INFO)


def test_all_supplied_reply_points_mapped(case_info):
    plan = map_case_to_content_plan(case_info)

    # 6 reply points + 1 closing move = 7 body paragraphs
    assert plan.expected_body_paragraph_count == 7
    assert plan.expected_verification_range == "paragraphs 1 to 7"

    # Total mappings includes 7 body paragraphs + 1 prayer clause
    assert len(plan.mappings) == 8


def test_reply_points_map_to_correct_legal_moves(case_info):
    plan = map_case_to_content_plan(case_info)
    body_moves = [m.move_type for m in plan.mappings if m.target_paragraph_number is not None]

    expected_moves = [
        LegalMoveType.IDENTITY_AND_PERUSAL,
        LegalMoveType.BLANKET_DENIAL,
        LegalMoveType.PRELIMINARY_POSITION,
        LegalMoveType.SUBSTANTIVE_ANSWER,
        LegalMoveType.SUBSTANTIVE_ANSWER,
        LegalMoveType.DOCUMENT_RELIED_UPON,
        LegalMoveType.CLOSING,
    ]
    assert body_moves == expected_moves

    # Check prayer move
    prayer_move = [m for m in plan.mappings if m.move_type == LegalMoveType.PRAYER_TO_DISMISS]
    assert len(prayer_move) == 1
    assert prayer_move[0].target_paragraph_number is None
    assert "Prayer" in prayer_move[0].target_section


def test_provenance_exists_for_mapped_items(case_info):
    plan = map_case_to_content_plan(case_info)

    for mapping in plan.mappings:
        assert mapping.source_evidence.source_file in ["03_Case_Information.pdf", "01_Affidavit_format_explained.pdf"]
        assert len(mapping.source_evidence.source_section) > 0
        assert len(mapping.source_evidence.source_text) > 0
        assert len(mapping.target_section) > 0
        assert len(mapping.intent) > 0
        assert len(mapping.required_phrases) > 0

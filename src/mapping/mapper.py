from typing import Optional, List
from src.schemas.case_info import CaseInformation
from src.schemas.template import (
    AffidavitTemplate,
    LegalMoveType,
)
from src.schemas.content_plan import (
    EvidenceSource,
    ContentMappingItem,
    ContentPlan,
)
from src.ingestion.template_parser import load_authoritative_template


def map_case_to_content_plan(
    case_info: CaseInformation,
    template: Optional[AffidavitTemplate] = None,
) -> ContentPlan:
    """
    Transforms structured CaseInformation into a structured ContentPlan.
    Maps each reply point and prayer to the Bombay High Court legal reply moves:
    - IDENTITY_AND_PERUSAL
    - BLANKET_DENIAL
    - PRELIMINARY_POSITION
    - SUBSTANTIVE_ANSWER
    - DOCUMENT_RELIED_UPON
    - CLOSING
    - PRAYER_TO_DISMISS

    Maintains rigorous evidence provenance for every paragraph.
    Calculates expected body count and verification range dynamically.
    """
    if template is None:
        template = load_authoritative_template()

    mappings: List[ContentMappingItem] = []

    # Map Point 1 -> IDENTITY_AND_PERUSAL (Body Para 1)
    if len(case_info.reply_points) >= 1:
        p1_text = case_info.reply_points[0]
        mappings.append(
            ContentMappingItem(
                target_paragraph_number=1,
                target_section="Numbered Paragraphs, Paragraph 1",
                move_type=LegalMoveType.IDENTITY_AND_PERUSAL,
                source_evidence=EvidenceSource(
                    source_file="03_Case_Information.pdf",
                    source_section="3. Reply Points to be Incorporated",
                    source_point_label="Point 1 — Filing of Affidavit in Reply",
                    source_text=p1_text,
                ),
                intent="Establish deponent capacity, affirm perusal of petition, and confirm competence to oppose reliefs on behalf of answering respondent.",
                required_phrases=[
                    "am well acquainted with the facts and circumstances of the case",
                    "I have perused the Petition and the documents annexed thereto",
                    "am competent to affirm this Affidavit in Reply",
                ],
            )
        )

    # Map Point 2 -> BLANKET_DENIAL (Body Para 2)
    if len(case_info.reply_points) >= 2:
        p2_text = case_info.reply_points[1]
        mappings.append(
            ContentMappingItem(
                target_paragraph_number=2,
                target_section="Numbered Paragraphs, Paragraph 2",
                move_type=LegalMoveType.BLANKET_DENIAL,
                source_evidence=EvidenceSource(
                    source_file="03_Case_Information.pdf",
                    source_section="3. Reply Points to be Incorporated",
                    source_point_label="Point 2 — General Denial",
                    source_text=p2_text,
                ),
                intent="Express blanket denial of all statements, contentions and averments not specifically admitted, asserting petition is misconceived and devoid of merits.",
                required_phrases=[
                    "At the outset, I deny each and every allegation, contention and submission",
                    "save and except those specifically admitted herein",
                    "misconceived, devoid of merits and is liable to be dismissed in limine",
                ],
            )
        )

    # Map Point 3 -> PRELIMINARY_POSITION (Body Para 3)
    if len(case_info.reply_points) >= 3:
        p3_text = case_info.reply_points[2]
        mappings.append(
            ContentMappingItem(
                target_paragraph_number=3,
                target_section="Numbered Paragraphs, Paragraph 3",
                move_type=LegalMoveType.PRELIMINARY_POSITION,
                source_evidence=EvidenceSource(
                    source_file="03_Case_Information.pdf",
                    source_section="3. Reply Points to be Incorporated",
                    source_point_label="Point 3 — Preliminary Position",
                    source_text=p3_text,
                ),
                intent="Assert preliminary position that challenged actions were taken strictly in accordance with applicable redevelopment procedure within available authority, and no right of petitioner is infringed.",
                required_phrases=[
                    "strictly in accordance with law and after following due procedure",
                    "No legal, constitutional or fundamental right... has been infringed",
                ],
            )
        )

    # Map Point 4 -> SUBSTANTIVE_ANSWER (Body Para 4)
    if len(case_info.reply_points) >= 4:
        p4_text = case_info.reply_points[3]
        mappings.append(
            ContentMappingItem(
                target_paragraph_number=4,
                target_section="Numbered Paragraphs, Paragraph 4",
                move_type=LegalMoveType.SUBSTANTIVE_ANSWER,
                source_evidence=EvidenceSource(
                    source_file="03_Case_Information.pdf",
                    source_section="3. Reply Points to be Incorporated",
                    source_point_label="Point 4 — Denial Regarding the Communication",
                    source_text=p4_text,
                ),
                intent="Specifically deny that the impugned communication dated 15 July 2026 was issued without authority.",
                required_phrases=[
                    "With reference to the averments made in the Petition, I say that the same are false, incorrect and denied",
                    "has failed to make out any case warranting interference in the extraordinary writ jurisdiction",
                ],
            )
        )

    # Map Point 5 -> SUBSTANTIVE_ANSWER (Body Para 5)
    if len(case_info.reply_points) >= 5:
        p5_text = case_info.reply_points[4]
        mappings.append(
            ContentMappingItem(
                target_paragraph_number=5,
                target_section="Numbered Paragraphs, Paragraph 5",
                move_type=LegalMoveType.SUBSTANTIVE_ANSWER,
                source_evidence=EvidenceSource(
                    source_file="03_Case_Information.pdf",
                    source_section="3. Reply Points to be Incorporated",
                    source_point_label="Point 5 — Authority for the Communication",
                    source_text=p5_text,
                ),
                intent="Substantiate that the communication dated 15 July 2026 was issued pursuant to the applicable redevelopment procedure and after consideration of the relevant records.",
                required_phrases=[
                    "issued pursuant to the applicable redevelopment procedure",
                    "after consideration of the relevant records",
                ],
            )
        )

    # Map Point 6 -> DOCUMENT_RELIED_UPON (Body Para 6)
    if len(case_info.reply_points) >= 6:
        p6_text = case_info.reply_points[5]
        mappings.append(
            ContentMappingItem(
                target_paragraph_number=6,
                target_section="Numbered Paragraphs, Paragraph 6",
                move_type=LegalMoveType.DOCUMENT_RELIED_UPON,
                source_evidence=EvidenceSource(
                    source_file="03_Case_Information.pdf",
                    source_section="3. Reply Points to be Incorporated",
                    source_point_label="Point 6 — Document Relied Upon",
                    source_text=p6_text,
                ),
                intent="Formally rely upon the communication dated 15 July 2026 and annex a copy marked as EXHIBIT-‘A’.",
                required_phrases=[
                    "Hereto annexed and marked as EXHIBIT-‘A’ is a copy of",
                ],
            )
        )

    # Map Mandatory Closing Move -> CLOSING (Body Para 7)
    closing_para_num = len(mappings) + 1
    mappings.append(
        ContentMappingItem(
            target_paragraph_number=closing_para_num,
            target_section=f"Numbered Paragraphs, Paragraph {closing_para_num}",
            move_type=LegalMoveType.CLOSING,
            source_evidence=EvidenceSource(
                source_file="01_Affidavit_format_explained.pdf",
                source_section="3. Paragraph sequence (Part 7) — Last",
                source_point_label="Mandatory Closing Move",
                source_text="In the premises aforesaid, I say that the Writ Petition deserves to be dismissed with costs.",
            ),
            intent="State the formal closing move that the Writ Petition deserves dismissal with costs.",
            required_phrases=[
                "In the premises aforesaid, I say that the Writ Petition deserves to be dismissed with costs",
            ],
        )
    )

    # Map Prayer -> PRAYER_TO_DISMISS (Section 8 Prayer)
    prayer_text = "; ".join(case_info.prayer_points)
    mappings.append(
        ContentMappingItem(
            target_paragraph_number=None,  # Prayer is lettered, not a body paragraph
            target_section="Prayer, Clauses (a) to (c)",
            move_type=LegalMoveType.PRAYER_TO_DISMISS,
            source_evidence=EvidenceSource(
                source_file="03_Case_Information.pdf",
                source_section="4. Prayer",
                source_point_label="Prayer Reliefs",
                source_text=prayer_text,
            ),
            intent="Formally pray for dismissal of the Writ Petition with costs and refusal of interim relief.",
            required_phrases=[
                "I therefore respectfully pray that this Hon'ble Court may be pleased to:",
                "dismiss the present Writ Petition with costs",
            ],
        )
    )

    expected_body_count = closing_para_num
    expected_verification_range = f"paragraphs 1 to {expected_body_count}"

    return ContentPlan(
        case_info=case_info,
        mappings=mappings,
        expected_body_paragraph_count=expected_body_count,
        expected_verification_range=expected_verification_range,
    )

from pathlib import Path
from src.schemas.template import (
    AffidavitTemplate,
    TemplateSection,
    SectionType,
)


def load_authoritative_template() -> AffidavitTemplate:
    """
    Builds the authoritative Bombay High Court Affidavit in Reply template
    defined in 01_Affidavit_format_explained.pdf.
    """
    sections = [
        TemplateSection(
            order=1,
            name="Forum Heading",
            section_type=SectionType.FORUM_HEADING,
            is_mandatory=True,
            formatting_rules=["First line", "Bold", "ALL CAPS", "Centred"],
        ),
        TemplateSection(
            order=2,
            name="Jurisdiction",
            section_type=SectionType.JURISDICTION,
            is_mandatory=True,
            formatting_rules=["Bold", "ALL CAPS", "Centred", "Always ends with JURISDICTION"],
        ),
        TemplateSection(
            order=3,
            name="Case Number",
            section_type=SectionType.CASE_NUMBER,
            is_mandatory=True,
            formatting_rules=["Bold", "ALL CAPS", "Centred", "Fixed words: NO. and OF"],
        ),
        TemplateSection(
            order=4,
            name="Cause Title",
            section_type=SectionType.CAUSE_TITLE,
            is_mandatory=True,
            formatting_rules=[
                "Names left-aligned",
                "Status tags right-aligned beginning with three dots: ...Petitioner, ...Respondent No.1",
                "VERSUS centred on its own line",
                "Respondents numbered 1., 2.",
            ],
        ),
        TemplateSection(
            order=5,
            name="Affidavit Title",
            section_type=SectionType.AFFIDAVIT_TITLE,
            is_mandatory=True,
            formatting_rules=["Bold", "ALL CAPS", "Centred", "Always carries the respondent number"],
        ),
        TemplateSection(
            order=6,
            name="Deponent Clause",
            section_type=SectionType.DEPONENT_CLAUSE,
            is_mandatory=True,
            formatting_rules=[
                "One sentence, unnumbered",
                "Deponent rule: if authority, officer deposes as 'the [designation] of the Respondent No.[N] above named'",
                "Never write 'I am the Respondent No.2' for an organisation",
            ],
        ),
        TemplateSection(
            order=7,
            name="Numbered Paragraphs",
            section_type=SectionType.NUMBERED_PARAGRAPHS,
            is_mandatory=True,
            formatting_rules=[
                "Bold number followed by full stop",
                "One continuous sequence (1 to N)",
                "Prayer is not part of body sequence",
                "Paragraph sequence: Identity/Perusal -> Blanket Denial -> Preliminary Position -> Substantive Answers -> Closing",
            ],
        ),
        TemplateSection(
            order=8,
            name="Prayer",
            section_type=SectionType.PRAYER,
            is_mandatory=True,
            formatting_rules=[
                "Heading PRAYER bold caps centred",
                "Clauses lettered (a), (b), (c) with bold letters",
                "Never numbered with the body",
            ],
        ),
        TemplateSection(
            order=9,
            name="Jurat",
            section_type=SectionType.JURAT,
            is_mandatory=True,
            formatting_rules=[
                "Solemnly affirmed at [PLACE] / On this [Nth] day of [MONTH] [YEAR]",
                "DEPONENT right-aligned caps",
                "Before Me left-aligned",
                "Verb must match deponent clause (solemnly affirm -> Solemnly affirmed)",
            ],
        ),
        TemplateSection(
            order=10,
            name="Verification",
            section_type=SectionType.VERIFICATION,
            is_mandatory=True,
            formatting_rules=[
                "Heading VERIFICATION bold caps centred",
                "Range must dynamically match actual body count (paragraphs 1 to N)",
                "Place and date repeat jurat",
                "DEPONENT right-aligned caps",
            ],
        ),
        TemplateSection(
            order=11,
            name="Advocate Block",
            section_type=SectionType.ADVOCATE_BLOCK,
            is_mandatory=True,
            formatting_rules=["Left-aligned", "Firm name bold caps", "Advocates for the Respondent No.[N]"],
        ),
    ]

    fixed_phrases = {
        "identity_and_perusal": "I say that I am the {capacity} in the above {proceeding_type} and am well acquainted with the facts and circumstances of the case. I have perused the Petition and the documents annexed thereto and am competent to affirm this Affidavit in Reply.",
        "blanket_denial": "At the outset, I deny each and every allegation, contention and submission made in the {proceeding_type}, save and except those specifically admitted herein. I say that the Petition is misconceived, devoid of merits and is liable to be dismissed in limine.",
        "preliminary_position": "The action complained of has been taken strictly in accordance with law and after following due procedure. No legal, constitutional or fundamental right of the Petitioner has been infringed.",
        "substantive_answer": "With reference to the averments made in the Petition, I say that the same are false, incorrect and denied. The Petitioner has failed to make out any case warranting interference in the extraordinary writ jurisdiction of this Hon'ble Court.",
        "closing": "In the premises aforesaid, I say that the {proceeding_type} deserves to be dismissed with costs.",
        "verification_boilerplate": "true and correct to my knowledge and belief and that nothing material has been concealed therefrom.",
    }

    rules = [
        "Rule 1: Verification verb in Part 6 matches the jurat verb in Part 9.",
        "Rule 2: Paragraph range in Part 10 matches the actual number of body paragraphs (paragraphs 1 to N).",
        "Rule 3: Authority deponent rule: an officer deposes for an organisation as 'the [designation] of Respondent No.2 above named'.",
        "Rule 4: Prayer clauses are lettered (a), (b), (c) and never numbered with body paragraphs.",
    ]

    return AffidavitTemplate(
        name="Affidavit in Reply — Bombay High Court Format",
        court_seat="BOMBAY",
        sections=sections,
        fixed_phrases=fixed_phrases,
        rules=rules,
    )

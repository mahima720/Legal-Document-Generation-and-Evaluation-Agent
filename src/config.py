from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
ASSIGNMENT_MATERIALS_DIR = BASE_DIR / "assignment_materials"
OUTPUTS_DIR = BASE_DIR / "outputs"

FILE_FORMAT_EXPLAINED = ASSIGNMENT_MATERIALS_DIR / "01_Affidavit_format_explained.pdf"
FILE_REPLY_SAMPLE = ASSIGNMENT_MATERIALS_DIR / "02_Affidavit_in_reply_sample.pdf"
FILE_CASE_INFO = ASSIGNMENT_MATERIALS_DIR / "03_Case_Information.pdf"

COURT_NAME = "IN THE HIGH COURT OF JUDICATURE AT BOMBAY"
DEFAULT_FONT_NAME = "Times New Roman"
BODY_FONT_SIZE_PT = 12
LINE_SPACING = 1.5

OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

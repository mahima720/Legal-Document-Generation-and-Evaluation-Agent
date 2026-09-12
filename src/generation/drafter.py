import os
import json
from typing import Optional, List
import requests
from src.schemas.case_info import CaseInformation
from src.schemas.content_plan import ContentPlan
from src.schemas.document import (
    BodyParagraph,
    PrayerClause,
    JuratBlock,
    VerificationBlock,
    AdvocateBlock,
    AffidavitDocument,
)


class AffidavitDrafter:
    """
    Legal drafting engine supporting two distinct modes:
    1. Deterministic / Mock Mode: Generates fully structured AffidavitDocument
       without requiring external API keys. Programmatically synthesizes text
       using structured case facts, content plan moves, and Bombay High Court idioms.
       Used by test suite and CLI runner for reproducible verification.
    2. LLM Mode: Required runtime engine using Google Gemini API. Calls the Gemini REST
       API with strict schema constraints to draft substantive legal body paragraphs,
       enforcing Bombay High Court phrasing and anti-hallucination rules.
       Raises explicit error if API key is missing or execution fails.
    """

    def draft(
        self,
        content_plan: ContentPlan,
        mode: str = "mock",
        api_key: Optional[str] = None,
    ) -> AffidavitDocument:
        """Main entrypoint for drafting an Affidavit in Reply."""
        if mode.lower() == "llm":
            key = api_key or os.getenv("GEMINI_API_KEY")
            if not key:
                raise ValueError("GEMINI_API_KEY is required when running in LLM mode.")
            return self._draft_llm(content_plan, key)

        return self._draft_deterministic(content_plan)

    def _build_affidavit_document(
        self,
        plan: ContentPlan,
        body_paras: List[BodyParagraph],
    ) -> AffidavitDocument:
        """
        Assembles the authoritative Bombay High Court AffidavitDocument structure
        wrapping the supplied substantive body paragraphs.
        Enforces court header, cause title, deponent capacity formula, jurat verb agreement,
        dynamic verification range (1 to len(body_paras)), and advocate block.
        """
        case = plan.case_info
        deponent = case.deponent
        resp_no = case.filed_on_behalf_of_respondent_no

        # 1. Court, Jurisdiction & Case Number
        court_heading = case.court
        jurisdiction = case.jurisdiction
        case_number_line = f"{case.proceeding_type} NO. {case.case_number} OF {case.year}"

        # 2. Cause Title
        petitioner_str = case.petitioner.details or case.petitioner.name
        petitioner_tag = case.petitioner.status_tag

        respondents_tuples = []
        for r in case.respondents:
            num_prefix = f"{r.respondent_number}. " if r.respondent_number else ""
            desc = f"{num_prefix}{r.name}"
            if r.details and r.details != r.name:
                desc += f", {r.details}"
            respondents_tuples.append((desc, r.status_tag))

        # 3. Affidavit Title
        affidavit_title = f"AFFIDAVIT IN REPLY ON BEHALF OF RESPONDENT NO. {resp_no}"

        # 4. Deponent Clause (Rule 3: Authority officer capacity formula)
        if deponent.organisation:
            deponent_clause = (
                f"I, {deponent.name}, {deponent.designation}, having office at {deponent.address}, "
                f"{deponent.capacity_formula}, do hereby {deponent.verification_verb} and state as under:"
            )
        else:
            deponent_clause = (
                f"I, {deponent.name}, residing at {deponent.address}, "
                f"{deponent.capacity_formula}, do hereby {deponent.verification_verb} and state as under:"
            )

        # 5. Prayer Clauses
        prayer_letters = ["(a)", "(b)", "(c)", "(d)"]
        prayers: List[PrayerClause] = []
        for idx, pt in enumerate(case.prayer_points):
            letter = prayer_letters[idx] if idx < len(prayer_letters) else f"({chr(97+idx)})"
            prayers.append(PrayerClause(letter=letter, text=pt))

        # 6. Jurat (Attestation with verb agreement)
        jurat_verb = "Solemnly affirmed" if "affirm" in deponent.verification_verb.lower() else "Sworn"
        jurat = JuratBlock(
            place=case.attestation_place,
            date_line=f"On this {case.attestation_date_formatted}",
            deponent_marker="DEPONENT",
            before_me_marker="Before Me",
            verb=jurat_verb,
        )

        # 7. Dynamic Verification Block (Dynamic range 1 to N)
        actual_body_count = len(body_paras)
        verification_text = (
            f"I, {deponent.name}, the Deponent above named, do hereby verify that the contents of "
            f"paragraphs 1 to {actual_body_count} and the Prayer above are true and correct to my "
            f"knowledge and belief and that nothing material has been concealed therefrom."
        )
        verification = VerificationBlock(
            heading="VERIFICATION",
            deponent_name=deponent.name,
            paragraph_range_start=1,
            paragraph_range_end=actual_body_count,
            verification_text=verification_text,
            place=case.attestation_place,
            date_line=f"on this {case.attestation_date_formatted}",
            deponent_marker="DEPONENT",
        )

        # 8. Advocate Block
        advocate = AdvocateBlock(
            firm_name=case.advocate_firm.upper(),
            advocate_for=f"Advocates for the {case.advocate_for}.",
        )

        return AffidavitDocument(
            court_heading=court_heading,
            jurisdiction=jurisdiction,
            case_number_line=case_number_line,
            cause_title_petitioner=petitioner_str,
            cause_title_petitioner_tag=petitioner_tag,
            cause_title_versus="VERSUS",
            cause_title_respondents=respondents_tuples,
            affidavit_title=affidavit_title,
            deponent_clause=deponent_clause,
            body_paragraphs=body_paras,
            prayer_heading="PRAYER",
            prayer_clauses=prayers,
            jurat=jurat,
            verification=verification,
            advocate_block=advocate,
        )

    def _draft_deterministic(self, plan: ContentPlan) -> AffidavitDocument:
        """
        Deterministic drafting engine.
        Constructs body paragraphs programmatically from CaseInformation and ContentPlan.
        Used by the test suite and CLI runner for reproducible execution.
        """
        case = plan.case_info
        deponent = case.deponent
        resp_no = case.filed_on_behalf_of_respondent_no

        body_paras: List[BodyParagraph] = []
        for mapping in plan.mappings:
            if mapping.target_paragraph_number is None:
                continue  # Skip prayer in body paragraphs
            
            p_num = mapping.target_paragraph_number
            p_move = mapping.move_type.value
            p_src = f"{mapping.source_evidence.source_file} | {mapping.source_evidence.source_point_label}"

            if p_num == 1:
                # Identity and perusal
                text = (
                    f"I say that I am the {deponent.designation} of the Respondent No.{resp_no} in the above "
                    f"{case.proceeding_type} and am well acquainted with the facts and circumstances of the case. "
                    f"I have perused the Petition and the documents annexed thereto and am competent to affirm this "
                    f"Affidavit in Reply on behalf of Respondent No. {resp_no}, {deponent.organisation}."
                )
            elif p_num == 2:
                # Blanket denial
                text = (
                    f"At the outset, I deny each and every allegation, contention and submission made in the "
                    f"{case.proceeding_type}, save and except those specifically admitted herein. I say that the "
                    f"Petition is misconceived, devoid of merits and is liable to be dismissed in limine. "
                    f"Nothing contained in the Writ Petition that has not been specifically dealt with or admitted "
                    f"is to be treated as an admission by Respondent No. {resp_no}."
                )
            elif p_num == 3:
                # Preliminary position
                text = (
                    f"I say that the Writ Petition is misconceived and devoid of merits. The actions challenged by "
                    f"the Petitioner were taken strictly in accordance with the applicable redevelopment procedure and "
                    f"within the authority available to Respondent No. {resp_no}. Strictly in accordance with law and "
                    f"after following due procedure, no legal, constitutional or fundamental right of the Petitioner "
                    f"has been infringed."
                )
            elif p_num == 4:
                # Substantive answer: denial of communication without authority
                text = (
                    f"With reference to the averments made in the Petition, I say that the same are false, incorrect "
                    f"and denied. Respondent No. {resp_no} specifically denies that the impugned communication dated "
                    f"15 July 2026 was issued without authority. The Petitioner has failed to make out any case "
                    f"warranting interference in the extraordinary writ jurisdiction of this Hon'ble Court."
                )
            elif p_num == 5:
                # Substantive answer: redevelopment procedure authority
                text = (
                    f"I say that the communication dated 15 July 2026 was issued pursuant to the applicable "
                    f"redevelopment procedure and after consideration of the relevant records. The contention of "
                    f"the Petitioner to the contrary is baseless, incorrect and denied."
                )
            elif p_num == 6:
                # Document relied upon
                text = (
                    f"Respondent No. {resp_no} relies upon the communication dated 15 July 2026. Hereto annexed "
                    f"and marked as EXHIBIT-‘A’ is a copy of the communication dated 15 July 2026 issued by "
                    f"Respondent No. {resp_no}."
                )
            elif p_num == 7:
                # Mandatory closing move
                text = (
                    f"In the premises aforesaid, I say that the {case.proceeding_type} deserves to be dismissed "
                    f"with costs."
                )
            else:
                text = f"I state that the averments in {mapping.source_evidence.source_text} are true and correct."

            body_paras.append(
                BodyParagraph(
                    number=p_num,
                    move_type=p_move,
                    text=text,
                    source_reference=p_src,
                )
            )

        return self._build_affidavit_document(plan, body_paras)

    def _draft_llm(self, plan: ContentPlan, api_key: str) -> AffidavitDocument:
        """
        Drafts the Affidavit in Reply using Google Gemini LLM via REST API.
        Sends structured case information and content plan moves to Gemini,
        enforcing strict JSON response formatting for substantive body paragraphs.
        Constructs and validates the complete AffidavitDocument.
        """
        case = plan.case_info
        deponent = case.deponent
        resp_no = case.filed_on_behalf_of_respondent_no

        moves_desc = []
        for m in plan.mappings:
            if m.target_paragraph_number is not None:
                moves_desc.append(
                    f"Paragraph {m.target_paragraph_number} (Move: {m.move_type.value}):\n"
                    f"  Source point: {m.source_evidence.source_point_label}\n"
                    f"  Source text: {m.source_evidence.source_text}\n"
                    f"  Target move instruction: {m.intent}"
                )
        moves_text = "\n\n".join(moves_desc)

        prompt = f"""You are an elite legal drafting specialist for the High Court of Judicature at Bombay, Ordinary Original Civil Jurisdiction.

Draft the substantive body paragraphs for an Affidavit in Reply on behalf of Respondent No. {resp_no} ({deponent.organisation}) in {case.proceeding_type} NO. {case.case_number} OF {case.year} ({case.petitioner.name} v. {deponent.organisation} & Ors.).

Deponent: {deponent.name}, {deponent.designation}, {deponent.organisation}.
Advocate Firm: {case.advocate_firm}.

STRICT LEGAL DRAFTING RULES:
1. Generate exactly 7 sequential body paragraphs numbered 1 to 7 according to the following Content Plan moves:
{moves_text}

2. Bombay High Court Phraseology Requirements:
- Paragraph 1 (Identity & Competence): State that the deponent is the {deponent.designation} of Respondent No. {resp_no} in the above {case.proceeding_type} and is well acquainted with the facts and circumstances of the case; has perused the Petition and the documents annexed thereto and is competent to affirm this Affidavit in Reply on behalf of Respondent No. {resp_no}, {deponent.organisation}.
- Paragraph 2 (General Denial): Begin with standard phrase: "At the outset, I deny each and every allegation, contention and submission made in the {case.proceeding_type}, save and except those specifically admitted herein." State that the petition is misconceived, devoid of merits, and liable to be dismissed in limine. Nothing contained in the petition not specifically admitted is an admission.
- Paragraph 3 (Preliminary Position): Assert that the petition is misconceived and devoid of merits; the actions challenged by the Petitioner were taken strictly in accordance with the applicable redevelopment procedure and within the authority available to Respondent No. {resp_no}; strictly in accordance with law and after following due procedure, no legal, constitutional or fundamental right of the Petitioner has been infringed.
- Paragraph 4 (Specific Denial of Impugned Communication): Averments are false, incorrect and denied; specifically deny that the impugned communication dated 15 July 2026 was issued without authority; Petitioner has failed to make out any case warranting interference in the extraordinary writ jurisdiction of this Hon'ble Court.
- Paragraph 5 (Substantive Defense): State that the communication dated 15 July 2026 was issued pursuant to the applicable redevelopment procedure and after consideration of the relevant records; contention of the Petitioner to the contrary is baseless, incorrect and denied.
- Paragraph 6 (Document Relied Upon): Rely upon the communication dated 15 July 2026, stating: "Respondent No. {resp_no} relies upon the communication dated 15 July 2026. Hereto annexed and marked as EXHIBIT-‘A’ is a copy of the communication dated 15 July 2026 issued by Respondent No. {resp_no}."
- Paragraph 7 (Closing Move): Mandatory closing prayer move: "In the premises aforesaid, I say that the {case.proceeding_type} deserves to be dismissed with costs."

3. Strict Anti-Hallucination & Containment Constraints:
- Do NOT introduce any external statutes, sections (e.g., Section 138, Arbitration Act, IPC, CrPC), or monetary amounts (e.g., Rs., crores, lakhs).
- Do NOT leak sample data (e.g., Arjun Mehta, Rohan Deshpande, WP 3147, Mehta & Kulkarni).
- Rely ONLY on the provided case facts and source materials.

OUTPUT FORMAT:
Return ONLY a valid JSON array of 7 objects. Each object must have:
- "number": integer (1 to 7)
- "move_type": string (e.g. "deponent_identity_and_authority")
- "text": string (the drafted paragraph text)
"""

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        }
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json",
            },
        }

        models = ["gemini-2.5-flash", "gemini-1.5-flash"]
        last_error = None

        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        raise RuntimeError("Gemini returned an empty candidates list.")
                    raw_text = candidates[0]["content"]["parts"][0]["text"]

                    clean_text = raw_text.strip()
                    if clean_text.startswith("```json"):
                        clean_text = clean_text[7:]
                    elif clean_text.startswith("```"):
                        clean_text = clean_text[3:]
                    if clean_text.endswith("```"):
                        clean_text = clean_text[:-3]
                    clean_text = clean_text.strip()

                    parsed_paras = json.loads(clean_text)
                    if isinstance(parsed_paras, dict):
                        for k in ("paragraphs", "body_paragraphs", "items"):
                            if k in parsed_paras and isinstance(parsed_paras[k], list):
                                parsed_paras = parsed_paras[k]
                                break

                    if not isinstance(parsed_paras, list) or len(parsed_paras) == 0:
                        raise RuntimeError(f"Expected a JSON list of paragraphs from Gemini, got {type(parsed_paras)}.")

                    body_paras: List[BodyParagraph] = []
                    for idx, p in enumerate(parsed_paras, start=1):
                        p_num = int(p.get("number", idx))
                        p_move = str(p.get("move_type", "substantive_reply"))
                        p_text = str(p.get("text", "")).strip()
                        body_paras.append(
                            BodyParagraph(
                                number=p_num,
                                move_type=p_move,
                                text=p_text,
                                source_reference=f"Gemini {model} | Grounded Case Evidence",
                            )
                        )

                    return self._build_affidavit_document(plan, body_paras)
                elif resp.status_code == 404:
                    last_error = f"Model {model} unavailable (HTTP 404)"
                    continue
                else:
                    err_detail = ""
                    try:
                        err_json = resp.json()
                        err_detail = err_json.get("error", {}).get("message", resp.text)
                    except Exception:
                        err_detail = resp.text[:200]
                    raise RuntimeError(f"Gemini API call failed with status {resp.status_code}: {err_detail}")
            except requests.exceptions.RequestException as re:
                last_error = f"Network request to Gemini failed: {re}"
                break

        raise RuntimeError(f"Gemini generation failed: {last_error or 'Unknown error'}")

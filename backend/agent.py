import json
import os
import re
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from kmap_engine import build_kmap_grid, find_kmap_groups, verify_truth_table

load_dotenv()

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


def build_tutor_walkthrough(
    kmap_data: Dict[str, Any],
    grouping_data: Dict[str, Any],
    verification: Dict[str, Any],
    llm_narrative: Optional[str] = None,
) -> Dict[str, Any]:
    """Formats the step-by-step tutor explanation and structured result payload."""
    vars_str = ", ".join(kmap_data["variables"])
    m_str = ", ".join(f"m{m}" for m in kmap_data["minterms"]) or "None"
    d_str = ", ".join(f"d{d}" for d in kmap_data["dont_cares"]) or "None"

    step1 = (
        f"Constructed a {kmap_data['rows']}x{kmap_data['cols']} Gray-code K-Map for F({vars_str}). "
        f"Placed 1s at minterms [{m_str}] and Don't-Cares (X) at [{d_str}] using Gray-code ordering "
        f"({kmap_data['row_labels']} for rows, {kmap_data['col_labels']} for columns) so adjacent cells differ by 1 bit."
    )

    if grouping_data["groups"]:
        group_lines = []
        for g in grouping_data["groups"]:
            epi_tag = " [Essential Prime Implicant]" if g["is_essential"] else " [Prime Implicant]"
            group_lines.append(
                f"Group {g['id']} ({g['size_name']}{epi_tag}, {g['wrap_type']}): "
                f"Covers minterms {g['minterms']} -> Term: {g['term']}."
            )
        step2 = " ".join(group_lines)
    else:
        step2 = "No 1s were present on the K-Map, so no groups were formed."

    if grouping_data["groups"]:
        elim_lines = []
        for g in grouping_data["groups"]:
            kept = ", ".join(g["kept_vars"]) if g["kept_vars"] else "None"
            elim = ", ".join(g["eliminated_vars"]) if g["eliminated_vars"] else "None"
            elim_lines.append(
                f"For {g['term']}: Constant literals [{kept}] remained; variables [{elim}] changed state (0 <-> 1) and cancelled out."
            )
        step3 = " ".join(elim_lines)
    else:
        step3 = "All outputs are 0; expression simplifies directly to F = 0."

    step4 = (
        f"Exhaustive {verification['total_rows']}-row truth table verification "
        f"{'PASSED (100% match across all input combinations)' if verification['all_passed'] else 'FAILED'} "
        f"for SOP: F = {grouping_data['minimized_sop']} and POS: F = {grouping_data['minimized_pos']}."
    )

    return {
        "kmap": kmap_data,
        "grouping": grouping_data,
        "verification": verification,
        "tutor_steps": {
            "step_1_plotting": step1,
            "step_2_grouping": step2,
            "step_3_elimination": step3,
            "step_4_verification": step4,
            "ai_tutor_summary": llm_narrative or (
                f"Grouping 1s yields SOP: F = {grouping_data['minimized_sop']}, "
                f"while grouping 0s yields POS: F = {grouping_data['minimized_pos']}."
            ),
        },
    }
    


def _parse_prompt_fallback(prompt: str) -> Dict[str, Any]:
    """Regex fallback parser supporting both minterms and maxterms."""
    text = prompt.lower()
    var_match = re.search(r"(\d)\s*[- ]?var", text)
    num_vars = int(var_match.group(1)) if var_match else 4
    num_vars = max(2, min(4, num_vars))

    is_maxterm = "maxterm" in text or "pos" in text
    dc_split = re.split(r"don['’]?t[- ]?cares?", text, maxsplit=1)
    main_part = dc_split[0]
    dc_part = dc_split[1] if len(dc_split) > 1 else ""

    # Strip the variable-count phrase so "4 variable" isn't read as minterm 4
    main_part = re.sub(r"\b[2-4]\s*[- ]?var\w*\b", "", main_part)

    raw_terms = [int(n) for n in re.findall(r"\d+", main_part)]
    dont_cares = [int(n) for n in re.findall(r"\d+", dc_part)]

    if not raw_terms and not is_maxterm:
        raw_terms = [0, 1, 2, 5, 8, 9, 10]

    if is_maxterm:
        excluded = set(raw_terms) | set(dont_cares)
        minterms = [i for i in range(1 << num_vars) if i not in excluded]
    else:
        minterms = raw_terms

    return {
        "num_vars": num_vars,
        "minterms": minterms,
        "dont_cares": dont_cares,
        "is_maxterm": is_maxterm,
    }


def run_kmap_agent(
    num_vars: Optional[int] = None,
    minterms: Optional[List[int]] = None,
    dont_cares: Optional[List[int]] = None,
    user_prompt: Optional[str] = None,
) -> Dict[str, Any]:
    """Runs the Agentic AI workflow with tool-calling trace and self-verification."""
    tool_trace: List[Dict[str, Any]] = []
    api_key = os.getenv("GEMINI_API_KEY")

    # If natural language prompt is provided without explicit grid inputs, extract parameters
    if user_prompt and (num_vars is None or minterms is None):
        parsed = None
        if GENAI_AVAILABLE and api_key:
            try:
                client = genai.Client(
                    api_key=api_key,
                    http_options={"api_version": "v1beta"},
                )
                # Inside run_kmap_agent(), update the extraction instructions & parsing:
                extract_resp = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=(
                        "Extract num_vars (2, 3, or 4), terms (list of integers), dont_cares (list of integers), "
                        "and is_maxterm (true if the user specifies maxterms/POS, false if minterms/SOP) "
                        f"from: {user_prompt}"
                    ),
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "num_vars": types.Schema(type=types.Type.INTEGER),
                                "terms": types.Schema(
                                    type=types.Type.ARRAY,
                                    items=types.Schema(type=types.Type.INTEGER),
                                ),
                                "dont_cares": types.Schema(
                                    type=types.Type.ARRAY,
                                    items=types.Schema(type=types.Type.INTEGER),
                                ),
                                "is_maxterm": types.Schema(type=types.Type.BOOLEAN),
                            },
                            required=["num_vars", "terms", "dont_cares", "is_maxterm"],
                        ),
                    ),
                )
                raw_parsed = json.loads(extract_resp.text)
                if isinstance(raw_parsed, list) and raw_parsed:
                    raw_parsed = raw_parsed[0]

                num_vars = max(2, min(4, int(raw_parsed.get("num_vars") or 4)))
                raw_terms = [int(x) for x in (raw_parsed.get("terms") or [])]
                dont_cares = [int(x) for x in (raw_parsed.get("dont_cares") or [])]
                is_maxterm = bool(raw_parsed.get("is_maxterm", False))

                if is_maxterm:
                    excluded = set(raw_terms) | set(dont_cares)
                    minterms = [i for i in range(1 << num_vars) if i not in excluded]
                else:
                    minterms = raw_terms
                tool_trace.append(
                    {
                        "tool": "extract_boolean_parameters (Gemini)",
                        "input": {"prompt": user_prompt},
                        "output": parsed,
                    }
                )
            except Exception as e:
                tool_trace.append(
                    {
                        "tool": "extract_boolean_parameters (Gemini fallback)",
                        "error": str(e),
                    }
                )

        if parsed is None:
            parsed = _parse_prompt_fallback(user_prompt)
            num_vars = parsed["num_vars"]
            minterms = parsed["minterms"]
            dont_cares = parsed["dont_cares"]
            tool_trace.append(
                {
                    "tool": "extract_boolean_parameters (local parser)",
                    "input": {"prompt": user_prompt},
                    "output": parsed,
                }
            )

    dont_cares = dont_cares or []

    # Step 1: Tool Call - Build K-Map Grid
    kmap_data = build_kmap_grid(num_vars, minterms, dont_cares)
    tool_trace.append(
        {
            "tool": "build_kmap_grid",
            "input": {"num_vars": num_vars, "minterms": minterms, "dont_cares": dont_cares},
            "output": f"Built {kmap_data['rows']}x{kmap_data['cols']} Gray-code grid.",
        }
    )

    # Step 2: Tool Call - Find Prime Implicants & Minimal Cover
    grouping_data = find_kmap_groups(kmap_data)
    tool_trace.append(
        {
            "tool": "find_kmap_groups",
            "input": {"rows": kmap_data["rows"], "cols": kmap_data["cols"]},
            "output": {
                "minimized_sop": grouping_data["minimized_sop"],
                "group_count": grouping_data["total_terms"],
            },
        }
    )

    # Step 3: Tool Call - Verify Truth Table (Self-Check)
    verification = verify_truth_table(
        num_vars,
        minterms,
        dont_cares,
        grouping_data["minimized_sop"],
        grouping_data["minimized_pos"],
    )
    tool_trace.append(
        {
            "tool": "verify_truth_table",
            "input": {
                "minimized_sop": grouping_data["minimized_sop"],
                "minimized_pos": grouping_data["minimized_pos"],
            },
            "output": {
                "all_passed": verification["all_passed"],
                "checked_rows": verification["total_rows"],
            },
        }
    )

    # Step 4: LLM Tutor Synthesis (if API key available)
    llm_narrative = None
    if GENAI_AVAILABLE and api_key:
        try:
            client = genai.Client(api_key=api_key)
            tutor_prompt = (
                "You are an encouraging Digital Electronics lab tutor helping an engineering student "
                "understand Karnaugh Map minimization. Given the verified K-map grouping result below, "
                "write a concise, intuitive 3-sentence explanation highlighting why the largest groups "
                "were chosen (mentioning any edge/corner wrap-arounds or Don't-Cares if present) and how "
                "variables cancelled out.\n\n"
                f"Variables: {kmap_data['variables']}\n"
                f"Minterms: {kmap_data['minterms']}, Don't Cares: {kmap_data['dont_cares']}\n"
                f"Groups: {json.dumps(grouping_data['groups'])}\n"
                f"Verified Minimized SOP: {grouping_data['minimized_sop']}"
            )
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=tutor_prompt,
            )
            llm_narrative = resp.text.strip()
            tool_trace.append(
                {
                    "tool": "synthesize_tutor_explanation (Gemini)",
                    "input": {"minimized_sop": grouping_data["minimized_sop"]},
                    "output": "Generated personalized step-by-step tutor note.",
                }
            )
        except Exception as e:
            tool_trace.append(
                {
                    "tool": "synthesize_tutor_explanation",
                    "error": str(e),
                }
            )

    result = build_tutor_walkthrough(kmap_data, grouping_data, verification, llm_narrative)
    result["agent_trace"] = tool_trace
    return result
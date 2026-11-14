import re
from itertools import combinations
from typing import Dict, List, Set, Tuple, Any

GRAY_1 = [0, 1]
GRAY_2 = [0, 1, 3, 2]

GROUP_COLORS = [
    "#3b82f6",  # Blue
    "#10b981",  # Emerald
    "#f59e0b",  # Amber
    "#f43f5e",  # Rose
    "#8b5cf6",  # Violet
    "#06b6d4",  # Cyan
    "#ec4899",  # Pink
    "#84cc16",  # Lime
]

SIZE_NAMES = {
    16: "16-Cell Group (Tautology)",
    8: "Octet (8-Cell Group)",
    4: "Quad (4-Cell Group)",
    2: "Pair (2-Cell Group)",
    1: "Isolated Cell (1-Cell Group)",
}


def get_grid_config(num_vars: int) -> Dict[str, Any]:
    if num_vars == 2:
        return {
            "variables": ["A", "B"],
            "row_vars": ["A"],
            "col_vars": ["B"],
            "row_gray": GRAY_1,
            "col_gray": GRAY_1,
            "row_labels": ["0", "1"],
            "col_labels": ["0", "1"],
            "rows": 2,
            "cols": 2,
        }
    elif num_vars == 3:
        return {
            "variables": ["A", "B", "C"],
            "row_vars": ["A"],
            "col_vars": ["B", "C"],
            "row_gray": GRAY_1,
            "col_gray": GRAY_2,
            "row_labels": ["0", "1"],
            "col_labels": ["00", "01", "11", "10"],
            "rows": 2,
            "cols": 4,
        }
    elif num_vars == 4:
        return {
            "variables": ["A", "B", "C", "D"],
            "row_vars": ["A", "B"],
            "col_vars": ["C", "D"],
            "row_gray": GRAY_2,
            "col_gray": GRAY_2,
            "row_labels": ["00", "01", "11", "10"],
            "col_labels": ["00", "01", "11", "10"],
            "rows": 4,
            "cols": 4,
        }
    else:
        raise ValueError("num_vars must be 2, 3, or 4.")


def build_kmap_grid(
    num_vars: int, minterms: List[int], dont_cares: List[int] = None
) -> Dict[str, Any]:
    """Tool 1: Maps decimal minterms and don't-cares onto a Gray-code K-Map grid."""
    if dont_cares is None:
        dont_cares = []

    max_m = (1 << num_vars) - 1
    m_set = {m for m in minterms if 0 <= m <= max_m}
    d_set = {d for d in dont_cares if 0 <= d <= max_m and d not in m_set}

    cfg = get_grid_config(num_vars)
    col_bits = len(cfg["col_vars"])
    grid = []

    for r_idx, r_val in enumerate(cfg["row_gray"]):
        row_cells = []
        for c_idx, c_val in enumerate(cfg["col_gray"]):
            minterm = (r_val << col_bits) | c_val
            if minterm in m_set:
                val = "1"
            elif minterm in d_set:
                val = "X"
            else:
                val = "0"

            row_cells.append(
                {
                    "row": r_idx,
                    "col": c_idx,
                    "minterm": minterm,
                    "binary": format(minterm, f"0{num_vars}b"),
                    "value": val,
                }
            )
        grid.append(row_cells)

    return {
        "num_vars": num_vars,
        "variables": cfg["variables"],
        "row_vars": "".join(cfg["row_vars"]),
        "col_vars": "".join(cfg["col_vars"]),
        "row_labels": cfg["row_labels"],
        "col_labels": cfg["col_labels"],
        "rows": cfg["rows"],
        "cols": cfg["cols"],
        "minterms": sorted(list(m_set)),
        "dont_cares": sorted(list(d_set)),
        "grid": grid,
    }


def _group_to_term(
    cells: List[Dict[str, Any]], variables: List[str], form: str = "SOP"
) -> Tuple[str, List[str], List[str]]:
    """Derives the simplified SOP product term or POS sum term for a group."""
    num_vars = len(variables)
    if len(cells) == (1 << num_vars):
        return ("1" if form == "SOP" else "0"), [], variables

    kept_literals = []
    kept_vars = []
    eliminated_vars = []

    for i, var in enumerate(variables):
        bits = {cell["binary"][i] for cell in cells}
        if form == "SOP":
            if bits == {"1"}:
                kept_literals.append(var)
                kept_vars.append(f"{var}=1 ({var})")
            elif bits == {"0"}:
                kept_literals.append(f"{var}'")
                kept_vars.append(f"{var}=0 ({var}')")
            else:
                eliminated_vars.append(var)
        else:  # POS (grouping 0s: 0 -> uncomplemented, 1 -> complemented)
            if bits == {"0"}:
                kept_literals.append(var)
                kept_vars.append(f"{var}=0 ({var})")
            elif bits == {"1"}:
                kept_literals.append(f"{var}'")
                kept_vars.append(f"{var}=1 ({var}')")
            else:
                eliminated_vars.append(var)

    if form == "SOP":
        term = "".join(kept_literals) if kept_literals else "1"
    else:
        term = f"({' + '.join(kept_literals)})" if kept_literals else "0"

    return term, kept_vars, eliminated_vars


def _solve_for_target(
    kmap_data: Dict[str, Any], target_val: str
) -> Tuple[List[Dict[str, Any]], str]:
    """Finds Prime Implicants and minimal cover for target_val ('1' for SOP, '0' for POS)."""
    form = "SOP" if target_val == "1" else "POS"
    forbidden_val = "0" if target_val == "1" else "1"

    variables = kmap_data["variables"]
    rows = kmap_data["rows"]
    cols = kmap_data["cols"]
    grid = kmap_data["grid"]

    cell_lookup: Dict[Tuple[int, int], Dict[str, Any]] = {}
    target_coords: Set[Tuple[int, int]] = set()

    for r in range(rows):
        for c in range(cols):
            cell = grid[r][c]
            cell_lookup[(r, c)] = cell
            if cell["value"] == target_val:
                target_coords.add((r, c))

    if not target_coords:
        return [], ("0" if form == "SOP" else "1")

    valid_heights = [h for h in [1, 2, 4] if h <= rows]
    valid_widths = [w for w in [1, 2, 4] if w <= cols]

    raw_candidates: Dict[frozenset, Dict[str, Any]] = {}

    for h in valid_heights:
        for w in valid_widths:
            for r0 in range(rows):
                for c0 in range(cols):
                    coords = [
                        ((r0 + dr) % rows, (c0 + dc) % cols)
                        for dr in range(h)
                        for dc in range(w)
                    ]
                    coord_set = frozenset(coords)
                    if coord_set in raw_candidates:
                        continue

                    cells = [cell_lookup[rc] for rc in coords]
                    values = {cell["value"] for cell in cells}

                    if forbidden_val not in values and target_val in values:
                        wraps_row = (r0 + h) > rows
                        wraps_col = (c0 + w) > cols
                        raw_candidates[coord_set] = {
                            "coord_set": coord_set,
                            "coords": sorted(list(coord_set)),
                            "cells": sorted(cells, key=lambda x: x["minterm"]),
                            "size": len(coord_set),
                            "wraps_around": wraps_row or wraps_col,
                            "wrap_type": (
                                "Corner Wrap-Around"
                                if (wraps_row and wraps_col)
                                else (
                                    "Top-Bottom Edge Wrap-Around"
                                    if wraps_row
                                    else (
                                        "Left-Right Edge Wrap-Around"
                                        if wraps_col
                                        else "Contiguous Block"
                                    )
                                )
                            ),
                        }

    all_sets = list(raw_candidates.keys())
    prime_implicants = [
        raw_candidates[s1] for s1 in all_sets if not any(s1 < s2 for s2 in all_sets)
    ]

    selected_indices: Set[int] = set()
    essential_indices: Set[int] = set()
    covered_targets: Set[Tuple[int, int]] = set()

    for rc in target_coords:
        covering = [
            idx for idx, pi in enumerate(prime_implicants) if rc in pi["coord_set"]
        ]
        if len(covering) == 1:
            epi_idx = covering[0]
            essential_indices.add(epi_idx)
            selected_indices.add(epi_idx)
            covered_targets.update(prime_implicants[epi_idx]["coord_set"] & target_coords)

    uncovered = target_coords - covered_targets
    if uncovered:
        remaining_indices = [
            i for i in range(len(prime_implicants)) if i not in selected_indices
        ]
        best_combo = None
        for r_len in range(1, len(remaining_indices) + 1):
            valid_combos = []
            for combo in combinations(remaining_indices, r_len):
                union_covered = set()
                for idx in combo:
                    union_covered.update(
                        prime_implicants[idx]["coord_set"] & target_coords
                    )
                if uncovered.issubset(union_covered):
                    total_size = sum(prime_implicants[idx]["size"] for idx in combo)
                    valid_combos.append((total_size, combo))
            if valid_combos:
                valid_combos.sort(key=lambda x: x[0], reverse=True)
                best_combo = valid_combos[0][1]
                break
        if best_combo:
            selected_indices.update(best_combo)

    ordered_selected = sorted(
        list(selected_indices),
        key=lambda i: (-prime_implicants[i]["size"], prime_implicants[i]["coords"][0]),
    )

    formatted_groups = []
    terms = []
    for g_idx, pi_idx in enumerate(ordered_selected):
        pi = prime_implicants[pi_idx]
        term, kept_vars, eliminated_vars = _group_to_term(
            pi["cells"], variables, form=form
        )
        terms.append(term)
        formatted_groups.append(
            {
                "id": g_idx + 1,
                "form": form,
                "color": GROUP_COLORS[g_idx % len(GROUP_COLORS)],
                "size": pi["size"],
                "size_name": SIZE_NAMES.get(pi["size"], f"{pi['size']}-Cell Group"),
                "is_essential": pi_idx in essential_indices,
                "wraps_around": pi["wraps_around"],
                "wrap_type": pi["wrap_type"],
                "cells": [[r, c] for r, c in pi["coords"]],
                "minterms": [cell["minterm"] for cell in pi["cells"]],
                "term": term,
                "kept_vars": kept_vars,
                "eliminated_vars": eliminated_vars,
            }
        )

    if form == "SOP":
        expr = " + ".join(terms) if terms else "0"
    else:
        expr = "".join(terms) if terms else "1"

    return formatted_groups, expr


def find_kmap_groups(kmap_data: Dict[str, Any]) -> Dict[str, Any]:
    """Tool 2: Finds minimal SOP (grouping 1s) and minimal POS (grouping 0s) covers."""
    sop_groups, minimized_sop = _solve_for_target(kmap_data, target_val="1")
    pos_groups, minimized_pos = _solve_for_target(kmap_data, target_val="0")

    return {
        "groups": sop_groups,
        "minimized_sop": minimized_sop,
        "total_terms": len(sop_groups),
        "pos_groups": pos_groups,
        "minimized_pos": minimized_pos,
        "pos_total_terms": len(pos_groups),
    }


def _eval_literal_product(term: str, var_map: Dict[str, int]) -> int:
    if term == "1":
        return 1
    if term == "0":
        return 0
    i = 0
    while i < len(term):
        ch = term[i]
        if ch.isalpha():
            if i + 1 < len(term) and term[i + 1] == "'":
                val = 1 - var_map[ch]
                i += 2
            else:
                val = var_map[ch]
                i += 1
            if val == 0:
                return 0
        else:
            i += 1
    return 1


def evaluate_sop_expression(expr: str, var_map: Dict[str, int]) -> int:
    cleaned = expr.strip()
    if cleaned == "0":
        return 0
    if cleaned == "1":
        return 1
    terms = [t.strip() for t in cleaned.split("+") if t.strip()]
    return 1 if any(_eval_literal_product(t, var_map) == 1 for t in terms) else 0


def evaluate_pos_expression(expr: str, var_map: Dict[str, int]) -> int:
    cleaned = expr.strip()
    if cleaned == "0":
        return 0
    if cleaned == "1":
        return 1
    clauses = re.findall(r"\(([^()]+)\)", cleaned)
    if not clauses:
        clauses = [cleaned]
    for clause in clauses:
        literals = [lit.strip() for lit in clause.split("+") if lit.strip()]
        clause_val = 0
        for lit in literals:
            var = lit[0]
            val = (1 - var_map[var]) if lit.endswith("'") else var_map[var]
            if val == 1:
                clause_val = 1
                break
        if clause_val == 0:
            return 0
    return 1


def verify_truth_table(
    num_vars: int,
    minterms: List[int],
    dont_cares: List[int],
    minimized_sop: str,
    minimized_pos: str = None,
) -> Dict[str, Any]:
    """Tool 3: Verifies both minimized SOP and POS expressions across all 2^n rows."""
    cfg = get_grid_config(num_vars)
    variables = cfg["variables"]
    m_set = set(minterms)
    d_set = set(dont_cares or [])

    rows = []
    all_passed = True

    for i in range(1 << num_vars):
        bits = [int(b) for b in format(i, f"0{num_vars}b")]
        var_map = dict(zip(variables, bits))

        if i in m_set:
            expected = "1"
        elif i in d_set:
            expected = "X"
        else:
            expected = "0"

        actual_sop = str(evaluate_sop_expression(minimized_sop, var_map))
        sop_ok = (expected == "X") or (expected == actual_sop)

        if minimized_pos is not None:
            actual_pos = str(evaluate_pos_expression(minimized_pos, var_map))
            pos_ok = (expected == "X") or (expected == actual_pos)
        else:
            actual_pos = actual_sop
            pos_ok = True

        passed = sop_ok and pos_ok
        if not passed:
            all_passed = False

        rows.append(
            {
                "minterm": i,
                "inputs": var_map,
                "binary": "".join(str(b) for b in bits),
                "expected": expected,
                "actual": actual_sop,
                "actual_pos": actual_pos,
                "passed": passed,
            }
        )

    return {
        "all_passed": all_passed,
        "total_rows": len(rows),
        "rows": rows,
    }
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
    cells: List[Dict[str, Any]], variables: List[str]
) -> Tuple[str, List[str], List[str]]:
    """Derives the simplified SOP product term and explains kept vs. eliminated literals."""
    num_vars = len(variables)
    if len(cells) == (1 << num_vars):
        return "1", [], variables

    kept_literals = []
    kept_vars = []
    eliminated_vars = []

    for i, var in enumerate(variables):
        bits = {cell["binary"][i] for cell in cells}
        if bits == {"1"}:
            kept_literals.append(var)
            kept_vars.append(f"{var}=1 ({var})")
        elif bits == {"0"}:
            kept_literals.append(f"{var}'")
            kept_vars.append(f"{var}=0 ({var}')")
        else:
            eliminated_vars.append(var)

    term = "".join(kept_literals) if kept_literals else "1"
    return term, kept_vars, eliminated_vars


def find_kmap_groups(kmap_data: Dict[str, Any]) -> Dict[str, Any]:
    """Tool 2: Finds Prime Implicants (with wrap-around) and selects the minimal SOP cover."""
    num_vars = kmap_data["num_vars"]
    variables = kmap_data["variables"]
    rows = kmap_data["rows"]
    cols = kmap_data["cols"]
    grid = kmap_data["grid"]

    cell_lookup: Dict[Tuple[int, int], Dict[str, Any]] = {}
    ones_coords: Set[Tuple[int, int]] = set()

    for r in range(rows):
        for c in range(cols):
            cell = grid[r][c]
            cell_lookup[(r, c)] = cell
            if cell["value"] == "1":
                ones_coords.add((r, c))

    if not ones_coords:
        return {
            "groups": [],
            "minimized_sop": "0",
            "total_terms": 0,
        }

    valid_heights = [h for h in [1, 2, 4] if h <= rows]
    valid_widths = [w for w in [1, 2, 4] if w <= cols]

    raw_candidates: Dict[frozenset, Dict[str, Any]] = {}

    for h in valid_heights:
        for w in valid_widths:
            for r0 in range(rows):
                for c0 in range(cols):
                    coords = []
                    for dr in range(h):
                        for dc in range(w):
                            coords.append(((r0 + dr) % rows, (c0 + dc) % cols))

                    coord_set = frozenset(coords)
                    if coord_set in raw_candidates:
                        continue

                    cells = [cell_lookup[rc] for rc in coords]
                    values = {cell["value"] for cell in cells}

                    if "0" not in values and "1" in values:
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

    # Filter to Prime Implicants (remove any candidate strictly contained inside a larger one)
    all_sets = list(raw_candidates.keys())
    prime_implicants = []
    for s1 in all_sets:
        if not any(s1 < s2 for s2 in all_sets):
            prime_implicants.append(raw_candidates[s1])

    # Identify Essential Prime Implicants (EPIs)
    selected_indices: Set[int] = set()
    essential_indices: Set[int] = set()
    covered_ones: Set[Tuple[int, int]] = set()

    for one_rc in ones_coords:
        covering = [
            idx for idx, pi in enumerate(prime_implicants) if one_rc in pi["coord_set"]
        ]
        if len(covering) == 1:
            epi_idx = covering[0]
            essential_indices.add(epi_idx)
            selected_indices.add(epi_idx)
            covered_ones.update(prime_implicants[epi_idx]["coord_set"] & ones_coords)

    # Exact minimal cover for any remaining uncovered 1-cells
    uncovered = ones_coords - covered_ones
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
                    union_covered.update(prime_implicants[idx]["coord_set"] & ones_coords)
                if uncovered.issubset(union_covered):
                    total_size = sum(prime_implicants[idx]["size"] for idx in combo)
                    valid_combos.append((total_size, combo))
            if valid_combos:
                # Prefer larger groups (fewer literals) on ties
                valid_combos.sort(key=lambda x: x[0], reverse=True)
                best_combo = valid_combos[0][1]
                break
        if best_combo:
            selected_indices.update(best_combo)

    # Format final selected groups
    ordered_selected = sorted(
        list(selected_indices),
        key=lambda i: (-prime_implicants[i]["size"], prime_implicants[i]["coords"][0]),
    )

    formatted_groups = []
    terms = []
    for g_idx, pi_idx in enumerate(ordered_selected):
        pi = prime_implicants[pi_idx]
        term, kept_vars, eliminated_vars = _group_to_term(pi["cells"], variables)
        terms.append(term)
        formatted_groups.append(
            {
                "id": g_idx + 1,
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

    minimized_sop = " + ".join(terms) if terms else "0"

    return {
        "groups": formatted_groups,
        "minimized_sop": minimized_sop,
        "total_terms": len(formatted_groups),
    }


def _eval_sop_term(term: str, var_map: Dict[str, int]) -> int:
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
    return 1 if any(_eval_sop_term(t, var_map) == 1 for t in terms) else 0


def verify_truth_table(
    num_vars: int,
    minterms: List[int],
    dont_cares: List[int],
    minimized_sop: str,
) -> Dict[str, Any]:
    """Tool 3: Verifies the minimized SOP expression across all 2^n truth table rows."""
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

        actual = str(evaluate_sop_expression(minimized_sop, var_map))
        passed = (expected == "X") or (expected == actual)
        if not passed:
            all_passed = False

        rows.append(
            {
                "minterm": i,
                "inputs": var_map,
                "binary": "".join(str(b) for b in bits),
                "expected": expected,
                "actual": actual,
                "passed": passed,
            }
        )

    return {
        "all_passed": all_passed,
        "total_rows": len(rows),
        "rows": rows,
    }
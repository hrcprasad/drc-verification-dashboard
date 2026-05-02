#!/usr/bin/env python3
"""
simulate_drc_runs.py
Generates synthetic Calibre-style DRC summary reports (.rpt) that
match the exact format of real Calibre output — no Cadence or Calibre needed.

Usage:
    python simulate_drc_runs.py              # generates eco_run_01..03.rpt
    python simulate_drc_runs.py 5            # generates 5 runs
    python simulate_drc_runs.py 5 output/    # write to a specific folder
"""

import sys
import os
import random

# ── Rule definitions ────────────────────────────────────────────────
# (layer, rule_suffix, description, base_count, is_critical)
RULE_DEFS = [
    ("M1",      "Space",      "Metal1 minimum spacing",          50, True),
    ("M1",      "Width",      "Metal1 minimum width",            20, True),
    ("M2",      "Space",      "Metal2 minimum spacing",          15, True),
    ("M2",      "Width",      "Metal2 minimum width",            14, True),
    ("VIA1",    "Enclosure",  "Via1 enclosure below minimum",    18, True),
    ("POLY",    "Pitch",      "Poly minimum pitch",               8, True),
    ("ANTENNA", "M2",         "Gate antenna violation",           6, True),
    ("M3",      "Width",      "Metal3 minimum width",             5, False),
    ("DENSITY", "M1",         "Metal1 density out of range",      3, False),
    ("NWELL",   "Space",      "NWell minimum spacing",            2, False),
    ("DIFF",    "Enclosure",  "Diffusion enclosure violation",    2, False),
]


def decay(base: int, run_index: int, total_runs: int) -> int:
    """
    Exponential decay with noise — simulates realistic ECO convergence.
    Early runs improve faster, later runs slow down (diminishing returns).
    """
    if base == 0:
        return 0
    fraction = 1.0 - (run_index / total_runs) ** 0.6
    raw = base * fraction
    noise = random.randint(
        -max(1, int(raw * 0.10)),
         max(1, int(raw * 0.10))
    )
    return max(0, int(raw) + noise)


def generate_rpt(run_index: int, total_runs: int,
                 cell_name: str = "CHIP_TOP_28NM") -> str:
    """
    Returns a Calibre DRC summary report string matching the exact
    format of real Calibre output:
    RULECHECK M1.Space ............ TOTAL Result Count = 45 (45)
    """
    lines = [
        "=" * 82,
        "--- CALIBRE::DRC-H SUMMARY REPORT ---",
        f"Project: {cell_name}",
        f"ECO Run: {run_index + 1} of {total_runs}",
        "=" * 82,
        ""
    ]

    total = 0
    for layer, rule_suffix, _, base, _ in RULE_DEFS:
        count = decay(base, run_index, total_runs)
        total += count
        rule_str = f"RULECHECK {layer}.{rule_suffix}"
        # Pad with dots to column 55 — matches real Calibre format
        dots = "." * max(4, 55 - len(rule_str))
        lines.append(
            f"{rule_str} {dots} TOTAL Result Count = {count} ({count})"
        )

    lines += [
        "",
        "--- SUMMARY BY LAYER ---",
        "",
        f"--- TOTAL: {total} violations ---",
    ]
    return "\n".join(lines) + "\n"


def write_runs(n_runs: int, out_dir: str,
               cell_name: str = "CHIP_TOP_28NM") -> list:
    os.makedirs(out_dir, exist_ok=True)
    random.seed(42)   # reproducible output
    generated = []

    for i in range(n_runs):
        filename = f"eco_run_{i+1:02d}.rpt"
        filepath = os.path.join(out_dir, filename)
        content  = generate_rpt(run_index=i, total_runs=n_runs,
                                 cell_name=cell_name)
        with open(filepath, "w") as f:
            f.write(content)

        # Extract total for display
        total_line = [l for l in content.splitlines()
                      if "TOTAL:" in l][0]
        print(f"  {filename}  →  {total_line.strip()}")
        generated.append(filepath)

    print(f"\n  {n_runs} file(s) written to: {os.path.abspath(out_dir)}")
    return generated


if __name__ == "__main__":
    n_runs  = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    out_dir = sys.argv[2] if len(sys.argv) > 2 \
              else os.path.dirname(os.path.abspath(__file__))

    print(f"\n  Generating {n_runs} synthetic Calibre DRC report(s)...\n")
    write_runs(n_runs, out_dir)
    print()
    print("  Next step: upload the generated .rpt files to the dashboard")
    print("  Upload all at once to see the convergence trend chart!")

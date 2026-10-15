"""Post-review exploratory sensitivity sweep; never overwrites committed results."""
from __future__ import annotations

import csv
import json
from dataclasses import replace
from pathlib import Path

from aegis_care.config import CONFIG
from aegis_care.eval.runner import ExperimentRunner


def main() -> None:
    output = Path("results/revision_sensitivity")
    output.mkdir(parents=True, exist_ok=True)
    c, i, r = CONFIG.candidate, CONFIG.influence, CONFIG.repair
    variants = {
        "default": CONFIG,
        "candidate_similarity_high": replace(CONFIG, candidate=replace(c, b_similarity=0.54, c_patient=0.26)),
        "candidate_patient_high": replace(CONFIG, candidate=replace(c, b_similarity=0.14, c_patient=0.66)),
        "candidate_resource_high": replace(CONFIG, candidate=replace(c, b_similarity=0.24, c_patient=0.36, d_resource=0.40)),
        "candidate_threshold_low": replace(CONFIG, candidate=replace(c, tau_c=0.30)),
        "candidate_threshold_high": replace(CONFIG, candidate=replace(c, tau_c=0.55)),
        "candidate_cap_8": replace(CONFIG, candidate=replace(c, max_candidates=8)),
        "attribution_semantic_high": replace(CONFIG, influence=replace(i, w1_semantic=0.54, w2_patient=0.26)),
        "attribution_threshold_high": replace(CONFIG, influence=replace(i, tau_i=0.45)),
        "repair_cutoff_high": replace(CONFIG, repair=replace(r, tau_r=0.90)),
    }
    summary = []
    for name, config in variants.items():
        result = ExperimentRunner(config).run(
            depths=(3, 4),
            provenance_conditions=("random40", "targeted"),
            conditions=("I",),
            tasks_per_family=1,
            seeds=(0, 1),
        )
        rows = result["rows"]
        aggregate = result["by_condition"][0] if result["by_condition"] else {}
        summary.append({
            "variant": name,
            "planned_cells": 32,
            "completed_incidents": len(result["incidents"]),
            "condition_rows": len(rows),
            "verification_failures": len(result["verification_failures"]),
            "wall_seconds": result["wall_seconds"],
            "recall": aggregate.get("descendant_recall"),
            "precision": aggregate.get("descendant_precision"),
            "bsr": aggregate.get("bsr"),
            "rwh": aggregate.get("rwh"),
            "uer": aggregate.get("uer"),
            "drr": aggregate.get("drr"),
        })
        (output / f"{name}.json").write_text(json.dumps({
            "rows": rows,
            "incidents": result["incidents"],
            "verification_failures": result["verification_failures"],
            "config": result["config"],
        }, indent=2, default=str))
        print(name, summary[-1], flush=True)
    with (output / "summary.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=summary[0])
        writer.writeheader()
        writer.writerows(summary)


if __name__ == "__main__":
    main()

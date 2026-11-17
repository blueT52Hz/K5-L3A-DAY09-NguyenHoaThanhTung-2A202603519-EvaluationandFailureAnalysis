"""M7 integrity checks used by lab9.gate.integrity_check.

A gate that only compares metric values against thresholds can be turned green by editing the
report instead of fixing the agent. Each check below returns human-readable problems; an empty
list means the PR report (and its spec) can be trusted enough to compare with the baseline.
"""

from __future__ import annotations

import math
from typing import Any

from lab9.graders import GRADERS

Report = dict[str, Any]
Spec = dict[str, Any]


def graded_metric_ids(spec: Spec) -> list[str]:
    """Spec metrics that a grader scores row by row (pass_5, pass_hat_k, cost are aggregates)."""
    return [m["id"] for m in spec.get("metrics") or [] if m["id"] in GRADERS]


def _row_key(r: dict[str, Any]) -> tuple[Any, Any]:
    return (r.get("item_id"), r.get("seed"))


def check_metric_values(pr: Report) -> list[str]:
    """NaN / inf in the aggregate metrics: `nan < min` is False, so a naive gate passes it."""
    out = []
    for k, v in (pr.get("metrics") or {}).items():
        if isinstance(v, float) and not math.isfinite(v):
            out.append(f"metric {k} is {v} (NaN/inf hides failures from threshold checks)")
    return out


def check_row_count(pr: Report, base: Report) -> list[str]:
    """Rows must cover items x seeds exactly once, against the PR manifest AND the baseline manifest
    (a cherry-picked run rewrites its own manifest seeds to match its rows)."""
    out = []
    rows = pr.get("rows") or []
    for who, rep in (("PR", pr), ("baseline", base)):
        man = rep.get("manifest") or {}
        want = (man.get("items") or 0) * len(man.get("seeds") or [])
        if len(rows) != want:
            out.append(f"{len(rows)} rows, {who} manifest expects {want} (items x seeds): dropped or duplicated rows")
    keys = [_row_key(r) for r in rows]
    dups = sorted({k for k in keys if keys.count(k) > 1}, key=str)
    if dups:
        out.append(f"duplicated (item, seed) rows: {dups[:5]}")
    if sorted(map(str, (pr.get("manifest") or {}).get("seeds") or [])) != \
            sorted(map(str, (base.get("manifest") or {}).get("seeds") or [])):
        out.append(f"seeds {pr.get('manifest', {}).get('seeds')} differ from baseline "
                   f"{base.get('manifest', {}).get('seeds')}")
    return out


def check_case_set(pr: Report, base: Report) -> list[str]:
    """The (item, seed) set must equal the baseline's: no cherry-picked seeds or dropped items."""
    a = {_row_key(r) for r in pr.get("rows") or []}
    b = {_row_key(r) for r in base.get("rows") or []}
    out = []
    if b - a:
        out.append(f"{len(b - a)} (item, seed) case(s) of the baseline missing from PR, e.g. {sorted(b - a, key=str)[:3]}")
    if a - b:
        out.append(f"{len(a - b)} (item, seed) case(s) not in the baseline, e.g. {sorted(a - b, key=str)[:3]}")
    return out


def check_grader_health(pr: Report, spec: Spec) -> list[str]:
    """A crashed grader must never become a green run: evaluator_failures, None cells, non-bool cells."""
    out = []
    if pr.get("evaluator_failures"):
        out.append(f"{len(pr['evaluator_failures'])} evaluator failure(s), first: {pr['evaluator_failures'][0]}")
    for m in graded_metric_ids(spec):
        missing = [_row_key(r) for r in pr.get("rows") or [] if r.get(m) is None]
        if missing:
            out.append(f"{len(missing)} row(s) with no value for graded metric {m}, e.g. {missing[:3]}")
        odd = [_row_key(r) for r in pr.get("rows") or [] if r.get(m) is not None and not isinstance(r.get(m), bool)]
        if odd:
            out.append(f"{len(odd)} row(s) with a non-boolean value for {m}, e.g. {odd[:3]}")
    return out


def check_metrics_match_rows(pr: Report, spec: Spec) -> list[str]:
    """Aggregates must be what the rows say (same rule as lab9.eval.aggregate): an edited
    pr['metrics'] that disagrees with its own rows is a hand-edited report."""
    out = []
    kind = {m["id"]: m.get("kind") for m in spec.get("metrics") or []}
    metrics = pr.get("metrics") or {}
    for m in graded_metric_ids(spec):
        if m not in metrics or metrics[m] is None:
            continue
        vals = [r[m] for r in pr.get("rows") or [] if isinstance(r.get(m), bool)]
        if not vals:
            continue
        want = sum(vals) if kind.get(m) == "safety" else round(sum(vals) / len(vals), 4)
        got = metrics[m]
        if not isinstance(got, (int, float)) or not math.isfinite(float(got)) or abs(float(got) - want) > 1e-4:
            out.append(f"metric {m} = {got} but its rows give {want}")
    return out


def check_slice_tags(pr: Report, base: Report) -> list[str]:
    """Moving an item out of a slice hides its regression from the slice gate."""
    def tags(rep: Report) -> dict[Any, tuple[str, ...]]:
        out: dict[Any, tuple[str, ...]] = {}
        for r in rep.get("rows") or []:
            out.setdefault(r.get("item_id"), tuple(sorted(r.get("slices") or [])))
        return out

    a, b = tags(pr), tags(base)
    changed = sorted(k for k in set(a) & set(b) if a[k] != b[k])
    return [f"item {k} slices {list(a[k])} differ from baseline {list(b[k])}" for k in changed]


def _looser_threshold(where: str, new: dict, old: dict) -> list[str]:
    out = []
    if "max" in old and ("max" not in new or new["max"] > old["max"]):
        out.append(f"{where}: max {old['max']} -> {new.get('max')}")
    if "min" in old and ("min" not in new or new["min"] < old["min"]):
        out.append(f"{where}: min {old['min']} -> {new.get('min')}")
    if "max_increase" in old and ("max_increase" not in new or new["max_increase"] > old["max_increase"]):
        out.append(f"{where}: max_increase {old['max_increase']} -> {new.get('max_increase')}")
    if old.get("no_significant_drop") and not new.get("no_significant_drop"):
        out.append(f"{where}: no_significant_drop removed")
    return out


def check_ratchet(spec: Spec, base_spec: Spec | None) -> list[str]:
    """Same eval-set version => thresholds may only get stricter (metrics and slices)."""
    if not base_spec or spec.get("eval_set_version") != base_spec.get("eval_set_version"):
        return []
    out = []
    new_m = {m["id"]: m for m in spec.get("metrics") or []}
    for old in base_spec.get("metrics") or []:
        mid, new = old["id"], new_m.get(old["id"])
        if new is None:
            out.append(f"ratchet: metric {mid} removed")
            continue
        if old.get("blocking") and not new.get("blocking"):
            out.append(f"ratchet: metric {mid} no longer blocking")
        out += [f"ratchet: {p}" for p in _looser_threshold(f"metric {mid}", new.get("threshold") or {},
                                                            old.get("threshold") or {})]
    new_s = {(s["name"], s["metric"]): s for s in spec.get("slices") or []}
    for old in base_spec.get("slices") or []:
        key = (old["name"], old["metric"])
        new = new_s.get(key)
        if new is None:
            out.append(f"ratchet: slice {key[0]}/{key[1]} removed")
            continue
        if old.get("blocking") and not new.get("blocking"):
            out.append(f"ratchet: slice {key[0]}/{key[1]} no longer blocking")
        out += [f"ratchet: {p}" for p in _looser_threshold(f"slice {key[0]}/{key[1]}", new, old)]
    return out


def run_all(pr: Report, base: Report, spec: Spec, base_spec: Spec | None = None) -> list[str]:
    return (check_metric_values(pr) + check_row_count(pr, base) + check_case_set(pr, base)
            + check_grader_health(pr, spec) + check_metrics_match_rows(pr, spec)
            + check_slice_tags(pr, base) + check_ratchet(spec, base_spec))

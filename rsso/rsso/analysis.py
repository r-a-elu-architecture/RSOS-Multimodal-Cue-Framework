"""Pre-specified analyses for RSOS studies. Identical code for synthetic and real data.

  python -m rsso.analysis runs.csv [--triggers triggers.csv] [--srbai srbai.csv]

Methods use per-participant summaries (a robust, assumption-light approach for repeated measures):
  H1  distress drop and agency gain, override vs paced breathing: per-person mean difference,
      paired t-test, d_z, 95% CI.
  H2  practice: per-person slope of log latency over successive override runs; one-sample t-test
      against 0. Weekly SRBAI: week 4 vs week 1, paired.
  H5  device triggering: share of triggers that led to a run (coverage) and median latency,
      device arm vs self-only arm, Welch t-test on per-person values.
Mixed-effects models (e.g. statsmodels MixedLM) are a valid alternative and are recommended for the
final analysis of real studies; they are not used here so the kit runs with numpy, scipy and pandas only.
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd
from scipy import stats


def _paired(x: np.ndarray) -> dict:
    x = x[~np.isnan(x)]
    n = len(x)
    if n < 3:
        return {"n": n}
    m, sd = x.mean(), x.std(ddof=1)
    t = stats.ttest_1samp(x, 0)
    half = stats.t.ppf(0.975, n - 1) * sd / np.sqrt(n)
    return {"n": n, "mean": m, "ci": (m - half, m + half), "d_z": m / sd if sd > 0 else np.nan, "p": t.pvalue}


def h1(runs: pd.DataFrame) -> dict | None:
    if not {"override", "paced_breathing"} <= set(runs.protocol):
        return None
    d = runs.assign(relief=runs.sud_before - runs.sud_after, gain=runs.agency_after - runs.agency_before)
    per = d.groupby(["participant", "protocol"])[["relief", "gain"]].mean().unstack()
    out = {}
    for k in ("relief", "gain"):
        out[k] = _paired((per[k]["override"] - per[k]["paced_breathing"]).to_numpy(float))
    return out


def h2(runs: pd.DataFrame, srbai: pd.DataFrame | None = None) -> dict | None:
    o = runs[(runs.protocol == "override") & pd.to_numeric(runs.latency_s, errors="coerce").notna()].copy()
    if o.empty:
        return None
    o["lat"] = pd.to_numeric(o.latency_s)
    slopes = []
    for _, g in o.sort_values("timestamp").groupby("participant"):
        g = g[g.trigger == "self"] if (g.trigger == "self").sum() >= 5 else g
        if len(g) >= 5:
            slopes.append(np.polyfit(np.arange(len(g)), np.log(g.lat.clip(lower=0.5)), 1)[0])
    out = {"slope": _paired(np.array(slopes))}
    first = o.sort_values("timestamp").groupby("participant").head(5).lat.median()
    last = o.sort_values("timestamp").groupby("participant").tail(5).lat.median()
    out["latency_first5_median"], out["latency_last5_median"] = first, last
    if srbai is not None and not srbai.empty:
        w = srbai.pivot_table(index="participant", columns="week", values="srbai")
        if w.shape[1] >= 2:
            out["srbai"] = _paired((w[w.columns.max()] - w[w.columns.min()]).to_numpy(float))
            out["srbai_weeks"] = (int(w.columns.min()), int(w.columns.max()))
    return out


def h5(triggers: pd.DataFrame | None) -> dict | None:
    if triggers is None or triggers.empty or triggers.arm.nunique() < 2:
        return None
    t = triggers.copy(); t["lat"] = pd.to_numeric(t.latency_s, errors="coerce")
    per = t.groupby(["participant", "arm"]).agg(coverage=("responded", "mean"), latency=("lat", "median")).reset_index()
    out = {}
    for k in ("coverage", "latency"):
        a, b = per[per.arm == "device"][k].dropna(), per[per.arm == "self"][k].dropna()
        w = stats.ttest_ind(a, b, equal_var=False)
        out[k] = {"device": a.mean(), "self": b.mean(), "n": (len(a), len(b)), "p": w.pvalue}
    return out


def _fmt(r, unit=""):
    if r.get("n", 0) < 3:
        return f"not enough participants (n={r.get('n', 0)})"
    lo, hi = r["ci"]
    return f"{r['mean']:+.2f}{unit} (95% CI {lo:+.2f} to {hi:+.2f}), d_z = {r['d_z']:.2f}, p = {r['p']:.2g}, n = {r['n']}"


def report(runs, triggers=None, srbai=None, title="RSOS study report") -> str:
    L = [f"# {title}", "", f"{len(runs)} runs from {runs.participant.nunique()} participants.", ""]
    r1 = h1(runs)
    if r1:
        L += ["## H1 — override vs paced breathing (per-person difference)", "",
              f"- Distress drop: {_fmt(r1['relief'], ' points')}", f"- Agency gain: {_fmt(r1['gain'], ' points')}", ""]
    r2 = h2(runs, srbai)
    if r2:
        s = r2["slope"]
        L += ["## H2 — practice: faster and more automatic", "",
              f"- Log-latency slope per run: {_fmt(s)}" + (f" (about {100 * (1 - np.exp(s['mean'])):.1f}% faster per run)" if s.get("n", 0) >= 3 else ""),
              f"- Median latency, first 5 runs → last 5 runs: {r2['latency_first5_median']:.1f} s → {r2['latency_last5_median']:.1f} s"]
        if "srbai" in r2:
            L.append(f"- Automaticity (SRBAI), week {r2['srbai_weeks'][0]} → week {r2['srbai_weeks'][1]}: {_fmt(r2['srbai'], ' points')}")
        L.append("")
    r5 = h5(triggers)
    if r5:
        c, l = r5["coverage"], r5["latency"]
        L += ["## H5 — device triggering vs self-initiated only", "",
              f"- Share of triggers followed by a run: device arm {100 * c['device']:.0f}% vs self-only {100 * c['self']:.0f}% (p = {c['p']:.2g}, n = {c['n'][0]} + {c['n'][1]})",
              f"- Median latency: device arm {l['device']:.1f} s vs self-only {l['self']:.1f} s (p = {l['p']:.2g})", ""]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="rsso.analysis")
    ap.add_argument("runs"); ap.add_argument("--triggers"); ap.add_argument("--srbai"); ap.add_argument("--title", default="RSOS study report")
    a = ap.parse_args(argv)
    runs = pd.read_csv(a.runs)
    tr = pd.read_csv(a.triggers) if a.triggers else None
    sb = pd.read_csv(a.srbai) if a.srbai else None
    print(report(runs, tr, sb, a.title))


if __name__ == "__main__":
    main()

"""Sample-size planning for the Override Protocol hypotheses (spec/OVERRIDE_PROTOCOL.md section 10).

H1 (within-person, one run vs paced-breathing control) and H6 (rehearsed vs unrehearsed elements)
are paired comparisons: the planning quantity is the standardised mean of each person's difference, d_z.
H3 (multichannel vs single-channel tiers) is between-person: Cohen's d.
Effect sizes are unknown; the table spans small to large. Run a pilot and re-plan with its estimate.

Usage: python power.py   (writes power_table.txt)
"""
import pathlib

import numpy as np
from scipy import stats


def n_paired(d, power=0.8, alpha=0.05):
    for n in range(3, 5000):
        df = n - 1; nc = d * np.sqrt(n); t = stats.t.ppf(1 - alpha / 2, df)
        if 1 - stats.nct.cdf(t, df, nc) + stats.nct.cdf(-t, df, nc) >= power:
            return n
    return None


def n_two_groups(d, power=0.8, alpha=0.05):
    for n in range(3, 5000):
        df = 2 * n - 2; nc = d * np.sqrt(n / 2); t = stats.t.ppf(1 - alpha / 2, df)
        if 1 - stats.nct.cdf(t, df, nc) + stats.nct.cdf(-t, df, nc) >= power:
            return n
    return None


if __name__ == "__main__":
    lines = ["Participants needed for 80% power, two-sided alpha 0.05", "",
             "effect size | H1/H6 paired (people) | H3 two groups (people per group)",
             "---|---|---"]
    for d in (0.2, 0.3, 0.5, 0.8):
        lines.append(f"{d} | {n_paired(d)} | {n_two_groups(d)}")
    lines += ["", "Paired effect d_z = mean of per-person differences / their SD.",
              "Averaging several runs per person and condition raises d_z; plan on the pilot's per-person means."]
    text = "\n".join(lines) + "\n"
    (pathlib.Path(__file__).resolve().parent / "power_table.txt").write_text(text)
    print(text)

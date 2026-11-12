"""Synthetic studies with virtual participants. Output files have the same format as real studies.

  python -m rsso.study h1   --people 40 --out study_out/h1      # crossover: override vs paced breathing
  python -m rsso.study long --people 40 --weeks 4 --out study_out/long   # practice, latency, device triggering
  python -m rsso.study power --out study_out                            # H1 power by simulation

Then analyse exactly as you would real data:
  python -m rsso.analysis study_out/h1/runs.csv
  python -m rsso.analysis study_out/long/runs.csv --triggers study_out/long/triggers.csv --srbai study_out/long/srbai.csv
"""
from __future__ import annotations

import argparse
import pathlib

import numpy as np
import pandas as pd

from .participants import StudyConfig, VirtualParticipant

T0 = 1_800_000_000   # synthetic epoch for timestamps


def _day_triggers(p, rng):
    n = rng.poisson(p.rate)
    return np.sort(rng.uniform(8 * 3600, 22 * 3600, n))


def h1(people=40, runs_per_person=12, practice_days=7, seed=0, cfg=None):
    """Within-person crossover after one week of practice: each noticed trigger is randomly assigned
    to the Override Protocol or to paced breathing of the same length."""
    cfg, rng = cfg or StudyConfig(), np.random.default_rng(seed)
    rows = []
    for i in range(people):
        p = VirtualParticipant(f"s{i:03d}", cfg, rng)
        for _ in range(practice_days * cfg.practice_runs_per_day):
            p.practice()
        day, got = practice_days, 0
        while got < runs_per_person and day < practice_days + 60:
            for t in _day_triggers(p, rng):
                if got >= runs_per_person:
                    break
                r = p.trigger(t, "override" if rng.random() < 0.5 else "paced_breathing")
                if r:
                    rows.append(dict(timestamp=T0 + day * 86400 + int(t), **r)); got += 1
            day += 1
    return {"runs": pd.DataFrame(rows)}


def longitudinal(people=40, weeks=4, device_fraction=0.5, seed=0, cfg=None):
    """Four weeks of daily life. Week 1 includes stage A practice. Half the participants also opt in to
    device triggering (virtual heart-rate strap + detector, calibrated per person)."""
    cfg, rng = cfg or StudyConfig(), np.random.default_rng(seed)
    runs, trig, srbai = [], [], []
    for i in range(people):
        dev = i < int(round(people * device_fraction))
        p = VirtualParticipant(f"s{i:03d}", cfg, rng, device_arm=dev)
        for day in range(weeks * 7):
            if day < 7:
                for _ in range(cfg.practice_runs_per_day):
                    p.practice()
            for t in _day_triggers(p, rng):
                r = p.trigger(t, "override")
                trig.append(dict(participant=p.pid, arm="device" if dev else "self", day=day, t_s=round(float(t)),
                                 responded=int(r is not None), by=(r or {}).get("trigger", ""), latency_s=(r or {}).get("latency_s", "")))
                if r:
                    runs.append(dict(timestamp=T0 + day * 86400 + int(t), **r))
            if day % 7 == 6:
                score = float(np.clip(1 + 4 * p.automaticity() + rng.normal(0, 0.35), 1, 5))
                srbai.append(dict(participant=p.pid, arm="device" if dev else "self", week=day // 7 + 1, srbai=round(score, 2)))
    return {"runs": pd.DataFrame(runs), "triggers": pd.DataFrame(trig), "srbai": pd.DataFrame(srbai)}


def power(extras=(0.25, 0.5, 1.0), ns=(10, 20, 40, 80), reps=100, runs_per_person=12, seed=0):
    """Simulation-based power for H1: share of synthetic studies with p < 0.05 and the right sign,
    for an assumed extra distress drop of the override over paced breathing (rating points)."""
    from .analysis import h1 as analyse_h1
    rows = []
    for extra in extras:
        cfg = StudyConfig(override_relief=1.0 + extra, control_relief=1.0)
        for n in ns:
            hits = 0
            for r in range(reps):
                res = analyse_h1(h1(n, runs_per_person, seed=seed + 1000 * r + n, cfg=cfg)["runs"])["relief"]
                hits += res.get("p", 1) < 0.05 and res.get("mean", 0) > 0
            rows.append(dict(assumed_extra_relief=extra, participants=n, power=hits / reps))
    return pd.DataFrame(rows)


COLUMNS = ["timestamp", "participant", "protocol", "trigger", "trigger_channel", "trigger_note", "sud_before", "sud_after",
           "agency_before", "agency_after", "latency_s", "completed", "stopped_at_phase", "tier", "voice"]


def save(out: dict, folder) -> list[str]:
    folder = pathlib.Path(folder); folder.mkdir(parents=True, exist_ok=True)
    written = []
    for name, df in out.items():
        if name == "runs":
            df = df[COLUMNS]
        df.to_csv(folder / f"{name}.csv", index=False); written.append(str(folder / f"{name}.csv"))
    return written


def main(argv=None):
    ap = argparse.ArgumentParser(prog="rsso.study", description="Run a synthetic RSOS study with virtual participants.")
    ap.add_argument("design", choices=["h1", "long", "power"])
    ap.add_argument("--people", type=int, default=40)
    ap.add_argument("--weeks", type=int, default=4)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.design == "power":
        t = power(seed=a.seed).pivot(index="assumed_extra_relief", columns="participants", values="power")
        pathlib.Path(a.out).mkdir(parents=True, exist_ok=True); t.to_csv(pathlib.Path(a.out) / "h1_power.csv")
        print(t.to_string()); return
    out = h1(a.people, seed=a.seed) if a.design == "h1" else longitudinal(a.people, a.weeks, seed=a.seed)
    for f in save(out, a.out):
        print("wrote", f)


if __name__ == "__main__":
    main()

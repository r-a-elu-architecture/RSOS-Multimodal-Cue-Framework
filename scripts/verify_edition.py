"""Check the public edition against a copy of the original records (spec/PUBLIC_EDITION_2.md M; PUBLIC_EDITION E1).

    python3 scripts/verify_edition.py PATH/TO/archive        # the folder holding original-estates/ (private repository)

1. every original file matches its SHA-256 in archive/provenance/SOURCE-MANIFEST.csv;
2. the tier ledger reassembles from its parsed blocks byte for byte;
3. docs/data/ledger.json and docs/data/metrics.json equal the originals plus rule E1 ("GPT" -> "model"), exactly.
"""
import csv
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "rsso"))
from rsso import ledger, metrics  # noqa: E402
from rsso.edition import edit_all  # noqa: E402


def main(arch: pathlib.Path) -> int:
    fails = []
    est = arch / "original-estates"
    rows = list(csv.DictReader(open(ROOT / "archive/provenance/SOURCE-MANIFEST.csv", encoding="utf-8")))
    bad = [r["source_path"] for r in rows if hashlib.sha256((est / r["source_path"]).read_bytes()).hexdigest() != r["sha256"]]
    print(f"1. {len(rows) - len(bad)}/{len(rows)} original files match the manifest")
    fails += bad
    ledger.SOURCE = est / ledger.SOURCE.relative_to(ROOT / "archive/original-estates")
    led = ledger.build()
    ok2 = ledger.reassemble(led).encode("utf-8") == ledger.SOURCE.read_bytes()
    print(f"2. ledger reassembles byte for byte: {ok2}")
    ok3 = edit_all(led) == json.loads((ROOT / "docs/data/ledger.json").read_text(encoding="utf-8"))
    metrics.LOGS = {k: est / v.relative_to(ROOT / "archive/original-estates") for k, v in metrics.LOGS.items()}
    metrics.build = ledger.build
    ok4 = edit_all(metrics.registry()) == json.loads((ROOT / "docs/data/metrics.json").read_text(encoding="utf-8"))
    print(f"3. published ledger = originals + E1: {ok3}; published metrics = originals + E1: {ok4}")
    if bad or not (ok2 and ok3 and ok4):
        print("FAIL", bad[:5])
        return 1
    print("edition verified")
    return 0


if __name__ == "__main__":
    sys.exit(main(pathlib.Path(sys.argv[1])))

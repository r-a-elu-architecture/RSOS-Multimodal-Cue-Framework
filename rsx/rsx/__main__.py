"""Command line: python -m rsx compile <file.rsx> [-o out.json]  |  python -m rsx check <file.rsx>..."""
import argparse
import json
import sys

from .compiler import compile_rsx, RSXError


def main(argv=None):
    ap = argparse.ArgumentParser(prog="rsx", description="Compile and check RSX protocols.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compile", help="compile one file to a JSON timeline")
    c.add_argument("file"); c.add_argument("-o", "--output")
    k = sub.add_parser("check", help="check that files compile; print a summary")
    k.add_argument("files", nargs="+")
    a = ap.parse_args(argv)
    if a.cmd == "compile":
        try:
            tl = compile_rsx(open(a.file, encoding="utf-8").read())
        except RSXError as e:
            print(f"{a.file}: {e}", file=sys.stderr); return 1
        text = json.dumps(tl, ensure_ascii=False, indent=1, sort_keys=True)
        if a.output:
            open(a.output, "w", encoding="utf-8").write(text + "\n")
        else:
            print(text)
        for w in tl["warnings"]:
            print("warning:", w, file=sys.stderr)
        return 0
    bad = 0
    for f in a.files:
        try:
            tl = compile_rsx(open(f, encoding="utf-8").read())
            print(f"{f}: ok  {len(tl['phases'])} phases, {len(tl['events'])} events, {tl['duration_ms']/1000:.1f} s"
                  + (f", {len(tl['warnings'])} warnings" if tl["warnings"] else ""))
        except RSXError as e:
            bad += 1; print(f"{f}: {e}", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

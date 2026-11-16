"""One program in three forms for the RSX-V page (spec/SITE_CATCHUP.md S7.3): the RSX-V command, the RSX cue program the
bridge writes, and the device lines. Uses the real bridge; scripts/check_all.sh regenerates it and checks it is unchanged.
python3 -m rsxv.site_example     (from rsxv/)
"""
import json
import pathlib

from . import parse
from .bridge import compile_cue, device_lines, to_cue

HERE = pathlib.Path(__file__).resolve().parent
EXAMPLE = HERE.parent / "examples" / "dragon.rsxv"
OUT = HERE.parents[1] / "docs" / "data" / "rsxv_example.json"
LINES = 24


def build():
    command = EXAMPLE.read_text(encoding="utf-8")
    cue = to_cue(parse(command), pid="dragon")
    source = cue["source"] if isinstance(cue, dict) and "source" in cue else cue
    timeline = compile_cue(source)
    lines = device_lines(timeline)
    return {
        "source": "rsxv/examples/dragon.rsxv",
        "command": command.rstrip("\n"),
        "cue": source.rstrip("\n"),
        "device": lines[:LINES],
        "device_total": len(lines),
        "timeline": {"phases": len(timeline["phases"]), "events": len(timeline["events"]), "seconds": round(timeline["duration_ms"] / 1000, 1)},
    }


def main():
    OUT.write_text(json.dumps(build(), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("wrote", OUT.relative_to(HERE.parents[1]))


if __name__ == "__main__":
    main()

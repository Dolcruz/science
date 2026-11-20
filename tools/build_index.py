"""Validate index.json and regenerate the files derived from it.

    python3 tools/build_index.py          # rewrite README.md table and llms.txt
    python3 tools/build_index.py --check  # fail if anything is invalid or out of date

Standard library only. index.json is the single source of truth for the list of entries.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = ["id", "field", "title", "claim", "status", "verification", "limitations",
            "keywords", "readme", "novelty_search", "produced_by"]
START, END = "<!-- index:start -->", "<!-- index:end -->"
STATUS_LABEL = {"lean-proof": "Lean 4 proof", "certificate": "certificate + checker",
                "reproducible-empirical": "reproducible evaluation",
                "archival-analysis": "archival data analysis", "paper-proof": "paper proof"}


def load():
    data = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    errors = []
    levels = set(data["status_levels"])
    seen = set()
    for e in data["entries"]:
        for k in REQUIRED:
            if k not in e:
                errors.append(f"{e.get('id', '?')}: missing {k}")
        if e["id"] in seen:
            errors.append(f"duplicate id {e['id']}")
        seen.add(e["id"])
        if not (ROOT / e["id"]).is_dir():
            errors.append(f"{e['id']}: folder missing")
        for s in e["status"]:
            if s not in levels:
                errors.append(f"{e['id']}: unknown status {s}")
        paths = [e["readme"]] + ([e["paper"]] if e.get("paper") else [])
        for v in e["verification"]:
            paths += v.get("files", []) + ([v["statement_file"]] if "statement_file" in v else [])
        for p in paths:
            if not (ROOT / p).is_file():
                errors.append(f"{e['id']}: file missing {p}")
    return data, errors


def table(data):
    rows = ["| field | entry | claim | checked by |", "|---|---|---|---|"]
    for e in data["entries"]:
        short = e["claim"].split(". ")[0].rstrip(".") + "."
        checked = ", ".join(STATUS_LABEL[s] for s in e["status"])
        rows.append(f"| {e['field']} | [{e['title']}]({e['id']}) | {short} | {checked} |")
    return "\n".join(rows)


def llms(data):
    out = ["# Science notes (Dolcruz/science)", "",
           "> " + data["description"], "",
           "Machine-readable index of all entries: [index.json](index.json). "
           "Rules every entry must pass: [CONTRIBUTING.md](CONTRIBUTING.md). "
           "Notes for agents: [AGENTS.md](AGENTS.md).", "", "## Entries", ""]
    for e in data["entries"]:
        out.append(f"- [{e['title']}]({e['readme']}): {e['claim']} "
                   f"Evidence: {', '.join(STATUS_LABEL[s] for s in e['status'])}. "
                   f"Limits: {' '.join(e['limitations'])}")
    out += ["", "## Verification commands", ""]
    for e in data["entries"]:
        for v in e["verification"]:
            out.append(f"- {e['id']} ({v['kind']}): `{v['command']}`")
    return "\n".join(out) + "\n"


def main():
    data, errors = load()
    readme_path, llms_path = ROOT / "README.md", ROOT / "llms.txt"
    readme = readme_path.read_text(encoding="utf-8")
    if START not in readme or END not in readme:
        errors.append("README.md lacks index markers")
    else:
        new_readme = re.sub(re.escape(START) + ".*?" + re.escape(END),
                            START + "\n" + table(data) + "\n" + END, readme, flags=re.S)
    new_llms = llms(data)
    if errors:
        print("\n".join(errors)); sys.exit(1)
    if "--check" in sys.argv:
        stale = [p.name for p, new in ((readme_path, new_readme), (llms_path, new_llms))
                 if not p.exists() or p.read_text(encoding="utf-8") != new]
        if stale:
            print("out of date, run python3 tools/build_index.py:", ", ".join(stale)); sys.exit(1)
        print(f"index ok: {len(data['entries'])} entries, all paths exist, derived files current")
    else:
        readme_path.write_text(new_readme, encoding="utf-8")
        llms_path.write_text(new_llms, encoding="utf-8")
        print(f"wrote README.md table and llms.txt for {len(data['entries'])} entries")


if __name__ == "__main__":
    main()

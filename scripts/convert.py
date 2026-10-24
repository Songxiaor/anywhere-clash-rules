#!/usr/bin/env python3
"""Convert Anywhere .arrs rule sets into Clash classical YAML.

Source of truth: anywhere/*.arrs
Generated: clash/*.yaml, catalog.json, and the README link table.
Do not edit generated files by hand.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANYWHERE = ROOT / "anywhere"
CLASH = ROOT / "clash"
README = ROOT / "README.md"
CATALOG = ROOT / "catalog.json"
TEMPLATE = ROOT / "templates" / "README.md"

REPO = "Songxiaor/anywhere-clash-rules"
RAW = f"https://raw.githubusercontent.com/{REPO}/main"
MIRROR = f"https://testingcf.jsdelivr.net/gh/{REPO}@main"

TYPE_MAP = {
    "0": ("IP-CIDR", "ipv4"),
    "1": ("IP-CIDR6", "ipv6"),
    "2": ("DOMAIN-SUFFIX", "suffix"),
    "3": ("DOMAIN-KEYWORD", "keyword"),
}

BEGIN = "<!-- BEGIN:LINKS -->"
END = "<!-- END:LINKS -->"


def parse_arrs(path: Path) -> dict:
    name = path.stem
    routing = None
    comments = []
    rules = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("name ="):
            name = line.split("=", 1)[1].strip()
            continue
        if line.startswith("routing ="):
            routing = line.split("=", 1)[1].strip()
            continue
        if line.startswith("#"):
            comments.append(line[1:].strip())
            continue
        if "," not in line:
            raise ValueError(f"{path.name}: unreadable rule: {raw}")
        kind, value = line.split(",", 1)
        kind = kind.strip()
        value = value.strip()
        if kind not in TYPE_MAP:
            raise ValueError(f"{path.name}: unknown type {kind}: {raw}")
        clash_type, bucket = TYPE_MAP[kind]
        rules.append(
            {
                "anywhere_type": kind,
                "clash": f"{clash_type},{value}",
                "bucket": bucket,
                "value": value,
            }
        )
    policy = "DIRECT" if routing == "1" else "PROXY"
    return {
        "file": path.name,
        "stem": path.stem,
        "name": name,
        "routing": routing,
        "policy": policy,
        "comments": comments,
        "rules": rules,
        "count": len(rules),
    }


def yaml_quote(item: str) -> str:
    if any(ch in item for ch in ":#{}[],&*?|>!%@`'\""):
        return json.dumps(item, ensure_ascii=False)
    return item


def render_yaml(parsed: dict) -> str:
    lines = [
        f"# Generated from anywhere/{parsed['file']} — DO NOT EDIT",
        f"# Anywhere name: {parsed['name']}",
        f"# Suggested policy: {parsed['policy']}",
        f"# Rules: {parsed['count']}",
        "# Clash Verge: rule-providers behavior: classical, format: yaml",
        "payload:",
    ]
    if not parsed["rules"]:
        lines.append("  []")
    else:
        for rule in parsed["rules"]:
            lines.append(f"  - {yaml_quote(rule['clash'])}")
    lines.append("")
    return "\n".join(lines)


def render_table(catalog: list[dict]) -> str:
    rows = [
        "| 规则集 | 建议策略 | 条数 | Anywhere `.arrs` | Clash Verge `.yaml` |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for item in catalog:
        stem = item["stem"]
        arrs = f"{RAW}/anywhere/{stem}.arrs"
        yaml = f"{RAW}/clash/{stem}.yaml"
        rows.append(
            f"| `{stem}` · {item['name']} | {item['policy']} | {item['count']} "
            f"| [arrs]({arrs}) | [yaml]({yaml}) |"
        )
    rows.append("")
    rows.append("国内访问 GitHub raw 不稳定时，把主机换成 jsDelivr：")
    rows.append("")
    rows.append("```text")
    rows.append(f"{MIRROR}/anywhere/<文件名>.arrs")
    rows.append(f"{MIRROR}/clash/<文件名>.yaml")
    rows.append("```")
    return "\n".join(rows)


def update_readme(table: str) -> None:
    source = TEMPLATE.read_text(encoding="utf-8") if TEMPLATE.exists() else README.read_text(encoding="utf-8")
    if BEGIN not in source or END not in source:
        raise SystemExit("README template is missing BEGIN/END link markers")
    before, rest = source.split(BEGIN, 1)
    _, after = rest.split(END, 1)
    README.write_text(
        f"{before}{BEGIN}\n{table}\n{END}{after}",
        encoding="utf-8",
    )


def public_catalog(parsed_list: list[dict]) -> list[dict]:
    out = []
    for item in parsed_list:
        out.append(
            {
                "stem": item["stem"],
                "name": item["name"],
                "policy": item["policy"],
                "count": item["count"],
                "anywhere": f"{RAW}/anywhere/{item['stem']}.arrs",
                "clash": f"{RAW}/clash/{item['stem']}.yaml",
            }
        )
    return out


def convert(check: bool = False) -> int:
    files = sorted(ANYWHERE.glob("*.arrs"))
    if not files:
        raise SystemExit("no anywhere/*.arrs files found")

    CLASH.mkdir(parents=True, exist_ok=True)
    parsed_list = [parse_arrs(path) for path in files]
    generated = {}
    for parsed in parsed_list:
        generated[CLASH / f"{parsed['stem']}.yaml"] = render_yaml(parsed)

    stale = [p for p in CLASH.glob("*.yaml") if p not in generated]
    dirty = False

    if check:
        for path, text in generated.items():
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                print(f"out of sync: {path.relative_to(ROOT)}", file=sys.stderr)
                dirty = True
        for path in stale:
            print(f"stale generated file: {path.relative_to(ROOT)}", file=sys.stderr)
            dirty = True
        expected_catalog = json.dumps(public_catalog(parsed_list), ensure_ascii=False, indent=2) + "\n"
        if not CATALOG.exists() or CATALOG.read_text(encoding="utf-8") != expected_catalog:
            print("out of sync: catalog.json", file=sys.stderr)
            dirty = True
        table = render_table(parsed_list)
        if BEGIN not in README.read_text(encoding="utf-8") or table not in README.read_text(encoding="utf-8"):
            # Compare by regenerating expected README
            source = TEMPLATE.read_text(encoding="utf-8")
            before, rest = source.split(BEGIN, 1)
            _, after = rest.split(END, 1)
            expected = f"{before}{BEGIN}\n{table}\n{END}{after}"
            if README.read_text(encoding="utf-8") != expected:
                print("out of sync: README.md", file=sys.stderr)
                dirty = True
        if dirty:
            print("run: python3 scripts/convert.py", file=sys.stderr)
            return 1
        print(f"ok: {len(parsed_list)} rule sets in sync")
        return 0

    for path in stale:
        path.unlink()
    for path, text in generated.items():
        path.write_text(text, encoding="utf-8")
    CATALOG.write_text(
        json.dumps(public_catalog(parsed_list), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    update_readme(render_table(parsed_list))
    print(f"wrote {len(generated)} Clash YAML files from {len(parsed_list)} Anywhere rule sets")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 1 if generated files do not match anywhere/*.arrs",
    )
    args = parser.parse_args()
    return convert(check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())

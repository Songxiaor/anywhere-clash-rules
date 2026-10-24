#!/usr/bin/env python3
"""Build complete Clash rule packs from categories.json.

This is manual. It does not run on git push.
Anywhere .arrs stay as-is for the Anywhere app.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANYWHERE = ROOT / "anywhere"
CLASH = ROOT / "clash"
README = ROOT / "README.md"
TEMPLATE = ROOT / "templates" / "README.md"
CATEGORIES = ROOT / "categories.json"
SCRIPT = ROOT / "clash-verge.js"
CATALOG = ROOT / "catalog.json"

REPO = "Songxiaor/anywhere-clash-rules"
RAW = f"https://raw.githubusercontent.com/{REPO}/main"
MIRROR = f"https://testingcf.jsdelivr.net/gh/{REPO}@main"
LOYAL = "https://testingcf.jsdelivr.net/gh/Loyalsoldier/clash-rules@release"
VPS = "https://testingcf.jsdelivr.net/gh/VPSDance/ai-proxy-rules@main/rules/clash"
BM7 = "https://testingcf.jsdelivr.net/gh/blackmatrix7/ios_rule_script@master/rule/Clash"

CLASSICAL_PREFIXES = (
    "DOMAIN",
    "IP-CIDR",
    "IP-CIDR6",
    "PROCESS-NAME",
    "GEOSITE",
    "GEOIP",
    "DST-PORT",
    "SRC-PORT",
    "RULE-SET",
)

BEGIN = "<!-- BEGIN:LINKS -->"
END = "<!-- END:LINKS -->"


def load_spec() -> dict:
    return json.loads(CATEGORIES.read_text(encoding="utf-8"))


MIRRORS = (
    "https://testingcf.jsdelivr.net/gh/",
    "https://fastly.jsdelivr.net/gh/",
    "https://cdn.jsdelivr.net/gh/",
    "https://raw.githubusercontent.com/",
)


def _mirror_candidates(url: str) -> list[str]:
    urls = [url]
    for prefix in (
        "https://testingcf.jsdelivr.net/gh/",
        "https://fastly.jsdelivr.net/gh/",
        "https://cdn.jsdelivr.net/gh/",
    ):
        if url.startswith(prefix):
            rest = url[len(prefix) :]
            # owner/repo@ref/path
            if "@" in rest:
                repo_ref, path = rest.split("@", 1)
                ref, file_path = path.split("/", 1)
                urls.append(f"https://raw.githubusercontent.com/{repo_ref}/{ref}/{file_path}")
            for other in MIRRORS:
                alt = other + rest if other.endswith("gh/") else url
                if other.endswith("gh/") and url.startswith("https://") and "jsdelivr.net/gh/" in url:
                    urls.append(other + rest)
            break
    out = []
    for item in urls:
        if item not in out:
            out.append(item)
    return out


def fetch(url: str) -> str:
    last_error = None
    for candidate in _mirror_candidates(url):
        try:
            req = urllib.request.Request(
                candidate,
                headers={"User-Agent": "anywhere-clash-rules-build"},
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                text = resp.read().decode("utf-8", errors="replace")
            if candidate != url:
                print(f"  via {candidate}", flush=True)
            return text
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            print(f"  retry after {type(exc).__name__}: {candidate}", flush=True)
    raise RuntimeError(f"failed to fetch {url}: {last_error}") from last_error


def yaml_quote(item: str) -> str:
    if item.startswith(("'", '"')):
        return item
    if any(ch in item for ch in ":#{}[]&*?|>!%@`'\""):
        return json.dumps(item, ensure_ascii=False)
    return item


def parse_arrs_text(text: str, exclude: set[str] | None = None) -> list[str]:
    exclude = {x.lower() for x in (exclude or [])}
    type_map = {"0": "IP-CIDR", "1": "IP-CIDR6", "2": "DOMAIN-SUFFIX", "3": "DOMAIN-KEYWORD"}
    out = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" in line.split(",", 1)[0]:
            continue
        if "," not in line:
            continue
        kind, value = line.split(",", 1)
        kind = kind.strip()
        value = value.strip()
        if kind not in type_map:
            continue
        if value.lower() in exclude:
            continue
        out.append(f"{type_map[kind]},{value}")
    return out


def parse_payload_items(text: str) -> list[str]:
    items = []
    in_payload = False
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("payload:"):
            in_payload = True
            rest = line[len("payload:") :].strip()
            if rest and rest not in ("[]",):
                items.extend(_normalize_item(x.strip()) for x in rest.strip("[]").split(",") if x.strip())
            continue
        if not in_payload:
            if line.startswith("- "):
                items.append(_normalize_item(line[2:].strip()))
            continue
        if not line or line.startswith("#"):
            continue
        if line.startswith("- "):
            items.append(_normalize_item(line[2:].strip()))
    return [x for x in items if x]


def _normalize_item(val: str) -> str:
    val = val.strip().strip(",")
    if (val.startswith("'") and val.endswith("'")) or (val.startswith('"') and val.endswith('"')):
        val = val[1:-1]
    if not val:
        return ""
    if val.startswith(CLASSICAL_PREFIXES):
        return val
    if val.startswith("+."):
        return f"DOMAIN-SUFFIX,{val[2:]}"
    if re.match(r"^\d+\.\d+\.\d+\.\d+/\d+$", val):
        return f"IP-CIDR,{val}"
    if ":" in val and "/" in val:
        return f"IP-CIDR6,{val}"
    return f"DOMAIN,{val}"


def parse_arrs_file(path: Path, exclude: set[str] | None = None) -> list[str]:
    return parse_arrs_text(path.read_text(encoding="utf-8"), exclude)


def collect_source(src: dict, spec: dict, cache: dict) -> list[str]:
    kind = src["kind"]
    exclude_name = src.get("exclude")
    exclude = set(spec.get("exclude_sets", {}).get(exclude_name, [])) if exclude_name else set()

    if kind == "arrs":
        return parse_arrs_file(ANYWHERE / src["file"], exclude)

    url = None
    if kind == "arrs-url":
        url = src["url"]
    elif kind == "loyal":
        url = f"{LOYAL}/{src['id']}.txt"
    elif kind == "vpsdance":
        url = f"{VPS}/{src['id']}.yaml"
    elif kind == "blackmatrix7":
        url = f"{BM7}/{src['name']}/{src['name']}.yaml"
    else:
        raise SystemExit(f"unknown source kind: {kind}")

    if url not in cache:
        print(f"fetch {url}", flush=True)
        cache[url] = fetch(url)
    text = cache[url]
    if kind == "arrs-url":
        return parse_arrs_text(text, exclude)
    return parse_payload_items(text)


def merge_rules(parts: list[list[str]]) -> list[str]:
    seen = set()
    out = []
    for part in parts:
        for rule in part:
            key = rule.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(rule)
    return out


def behavior_for(rules: list[str]) -> str:
    for rule in rules:
        kind = rule.split(",", 1)[0]
        if kind not in ("DOMAIN", "DOMAIN-SUFFIX"):
            return "classical"
    return "domain"


def to_domain_entry(rule: str) -> str:
    kind, value = rule.split(",", 1)
    if kind == "DOMAIN-SUFFIX":
        return f"+.{value}"
    return value


def write_yaml(path: Path, cat: dict, rules: list[str], behavior: str) -> None:
    lines = [
        f"# {cat['title']} — {cat['summary']}",
        f"# Suggested policy: {cat['policy']}",
        f"# Clash group: {cat['group']}",
        f"# Rules: {len(rules)}",
        f"# behavior: {behavior}",
        "# Built by scripts/build.py. Not auto-generated on push.",
        "payload:",
    ]
    if not rules:
        lines.append("  []")
    elif behavior == "domain":
        for rule in rules:
            lines.append(f"  - {yaml_quote(to_domain_entry(rule))}")
    else:
        for rule in rules:
            lines.append(f"  - {yaml_quote(rule)}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def render_table(cats: list[dict], counts: dict[str, int]) -> str:
    rows = [
        "| 顺序 | 规则包 | 策略组 | 条数 | 链接 |",
        "| ---: | --- | --- | ---: | --- |",
    ]
    for i, cat in enumerate(cats, 1):
        url = f"{RAW}/clash/{cat['id']}.yaml"
        rows.append(
            f"| {i} | `{cat['id']}` · {cat['title']} | {cat['group']} | {counts[cat['id']]} | [yaml]({url}) |"
        )
    rows += [
        "",
        "国内镜像（把主机换掉即可）：",
        "",
        "```text",
        f"{MIRROR}/clash/<id>.yaml",
        "```",
    ]
    return "\n".join(rows)


def write_readme(cats: list[dict], counts: dict[str, int]) -> None:
    table = render_table(cats, counts)
    source = TEMPLATE.read_text(encoding="utf-8")
    before, rest = source.split(BEGIN, 1)
    _, after = rest.split(END, 1)
    README.write_text(f"{before}{BEGIN}\n{table}\n{END}{after}", encoding="utf-8")


def write_script(cats: list[dict], behaviors: dict[str, str]) -> None:
    provider_block = []
    rule_lines = []
    group_block = []
    ip_sets = {"direct", "social", "ai"}
    for cat in cats:
        cid = cat["id"]
        behavior = behaviors[cid]
        provider_block.append(
            f'  "{cid}": pack("{cid}", "{behavior}"),'
        )
        if cat["policy"] == "REJECT":
            dest = "广告过滤"
        elif cat["policy"] == "DIRECT":
            dest = "全局直连"
        elif cat["id"] == "proxy":
            dest = "节点选择"
        else:
            dest = cat["group"]
        resolve = ",no-resolve" if cid in ip_sets else ""
        rule_lines.append(f'  "RULE-SET,{cid},{dest}{resolve}",')

        if cat["policy"] == "REJECT":
            continue
        if cat["id"] in ("proxy", "direct"):
            continue
        group_block.append(
            f'''    selectWithNodes("{cat["group"]}", ["节点选择", "延迟选优", "故障转移", "全局直连"], "{cat["icon"]}"),'''
        )

    text = SCRIPT_TEMPLATE.format(
        providers="\n".join(provider_block),
        extra_groups="\n".join(group_block),
        rules="\n".join(rule_lines),
        repo=REPO,
    )
    SCRIPT.write_text(text, encoding="utf-8")


SCRIPT_TEMPLATE = '''/**
 * Clash Verge 全局扩展脚本
 * 来源：https://github.com/{repo}
 *
 * 用法：订阅页 → 全局扩展脚本 → 整份粘贴保存。
 * 先导入带节点的订阅；无节点时会报错。
 * Cursor / Claude 桌面版需要 TUN。
 */

const PACK = "https://testingcf.jsdelivr.net/gh/{repo}@main/clash";

const domesticNameservers = [
  "https://dns.alidns.com/dns-query",
  "https://doh.pub/dns-query",
  "https://doh.360.cn/dns-query",
];

const foreignNameservers = [
  "https://1.1.1.1/dns-query",
  "https://1.0.0.1/dns-query",
];

const dnsConfig = {{
  enable: true,
  listen: "0.0.0.0:1053",
  ipv6: true,
  "use-system-hosts": false,
  "cache-algorithm": "arc",
  "enhanced-mode": "fake-ip",
  "fake-ip-range": "198.18.0.1/16",
  "fake-ip-filter": ["+.lan", "+.local", "+.msftconnecttest.com", "+.msftncsi.com"],
  "default-nameserver": ["223.5.5.5", "119.29.29.29", "1.1.1.1", "8.8.8.8"],
  nameserver: [...domesticNameservers, ...foreignNameservers],
  "proxy-server-nameserver": [...domesticNameservers, ...foreignNameservers],
  "nameserver-policy": {{
    "geosite:private,cn,geolocation-cn": domesticNameservers,
    "geosite:google,youtube,telegram,gfw,geolocation-!cn": foreignNameservers,
  }},
}};

const pack = (id, behavior) => ({{
  type: "http",
  behavior,
  format: "yaml",
  url: `${{PACK}}/${{id}}.yaml`,
  path: `./ruleset/songxiaor/${{id}}.yaml`,
  interval: 86400,
}});

const ruleProviders = {{
{providers}
}};

const rules = [
{rules}
  "GEOIP,LAN,全局直连,no-resolve",
  "GEOIP,CN,全局直连,no-resolve",
  "MATCH,漏网之鱼",
];

const icon = (name) =>
  `https://testingcf.jsdelivr.net/gh/clash-verge-rev/clash-verge-rev.github.io@main/docs/assets/icons/${{name}}.svg`;

const groupBaseOption = {{
  interval: 300,
  timeout: 3000,
  url: "https://www.google.com/generate_204",
  lazy: true,
  "max-failed-times": 3,
  hidden: false,
}};

const selectWithNodes = (name, extra, iconName) => ({{
  ...groupBaseOption,
  name,
  type: "select",
  proxies: extra,
  "include-all": true,
  icon: icon(iconName),
}});

function main(config) {{
  const proxyCount = config?.proxies?.length ?? 0;
  const proxyProviderCount =
    typeof config?.["proxy-providers"] === "object"
      ? Object.keys(config["proxy-providers"]).length
      : 0;
  if (proxyCount === 0 && proxyProviderCount === 0) {{
    throw new Error("配置文件中未找到任何代理，请先导入带节点的订阅");
  }}

  config["dns"] = dnsConfig;
  config["proxy-groups"] = [
    selectWithNodes("节点选择", ["延迟选优", "故障转移"], "adjust"),
    {{
      ...groupBaseOption,
      name: "延迟选优",
      type: "url-test",
      tolerance: 100,
      "include-all": true,
      icon: icon("speed"),
    }},
    {{
      ...groupBaseOption,
      name: "故障转移",
      type: "fallback",
      "include-all": true,
      icon: icon("ambulance"),
    }},
{extra_groups}
    {{
      ...groupBaseOption,
      name: "广告过滤",
      type: "select",
      proxies: ["REJECT", "DIRECT"],
      icon: icon("bug"),
    }},
    {{
      ...groupBaseOption,
      name: "全局直连",
      type: "select",
      proxies: ["DIRECT", "节点选择", "延迟选优"],
      icon: icon("link"),
    }},
    selectWithNodes("漏网之鱼", ["节点选择", "延迟选优", "全局直连"], "fish"),
  ];
  config["rule-providers"] = ruleProviders;
  config["rules"] = rules;
  return config;
}}
'''


def main() -> int:
    spec = load_spec()
    id_map = {c["id"]: c for c in spec["categories"]}
    cats = [id_map[i] for i in spec["order"]]
    cache: dict[str, str] = {}
    CLASH.mkdir(parents=True, exist_ok=True)

    counts = {}
    behaviors = {}
    catalog = []
    wanted = set()
    for cat in cats:
        parts = []
        if cat.get("extras"):
            parts.append(list(cat["extras"]))
        for src in cat["sources"]:
            parts.append(collect_source(src, spec, cache))
        rules = merge_rules(parts)
        path = CLASH / f"{cat['id']}.yaml"
        behavior = behavior_for(rules)
        write_yaml(path, cat, rules, behavior)
        wanted.add(path.name)
        counts[cat["id"]] = len(rules)
        behaviors[cat["id"]] = behavior
        catalog.append(
            {
                "id": cat["id"],
                "title": cat["title"],
                "policy": cat["policy"],
                "group": cat["group"],
                "behavior": behavior,
                "count": len(rules),
                "url": f"{RAW}/clash/{cat['id']}.yaml",
            }
        )
        print(f"wrote {path.name} ({len(rules)} rules)")

    for stale in CLASH.glob("*.yaml"):
        if stale.name not in wanted:
            stale.unlink()
            print(f"removed stale {stale.name}")

    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_readme(cats, counts)
    write_script(cats, behaviors)
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

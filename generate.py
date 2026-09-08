#!/usr/bin/env python3
"""Render assets/boot.svg from config.json. Python 3.10+, no third-party deps."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config.json"
OUT = ROOT / "assets" / "boot.svg"

N_HASH = 16
CHAR_W = 8.4
MSG_X = 48
ICON_X = 26
CHECK_X = 24
LINE = 24
BOTTLE_LINE = 22


def esc(s: str) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def slug(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower()).strip("-")
    if not s:
        s = "pkg"
    if s[0].isdigit():
        s = "p-" + s
    return s


def last_anniversary(today: date, month: int, day: int) -> date:
    this_year = date(today.year, month, day)
    if today >= this_year:
        return this_year
    return date(today.year - 1, month, day)


def months_since(start: date, end: date) -> int:
    months = (end.year - start.year) * 12 + (end.month - start.month)
    if end.day < start.day:
        months -= 1
    return months


def semver(major: int, minor: int, patch: int) -> str:
    major += minor // 10
    minor %= 10
    return f"{major}.{minor}.{patch}"


def resolve_version(spec, today: date) -> str:
    if spec is None:
        return "0.1.0"
    if isinstance(spec, (int, float)):
        return str(spec)
    if isinstance(spec, str):
        return spec
    kind = spec.get("type", "age")
    if kind == "age":
        born = date.fromisoformat(spec["birthday"])
        last = last_anniversary(today, born.month, born.day)
        years = last.year - born.year
        return semver(years // 10, years % 10, months_since(last, today))
    if kind == "anniversary":
        month = int(spec["month"])
        day = int(spec["day"])
        as_of_year = int(spec.get("as_of_year", today.year))
        base = spec.get("version", "1.0.0")
        major, minor, _patch = (int(p) for p in str(base).split("."))
        last = last_anniversary(today, month, day)
        minor += last.year - as_of_year
        return semver(major, minor, months_since(last, today))
    raise ValueError(f"unknown version type: {kind}")


def hashes_for(row: dict) -> list[float]:
    t0, t1, n = row["t0"], row["t1"], N_HASH
    effect = row.get("effect")
    if effect == "bursts":
        span = t1 - t0
        rel = [
            0.04, 0.07, 0.10, 0.13,
            0.38, 0.40, 0.42, 0.45, 0.48,
            0.70, 0.72, 0.75,
            0.88, 0.92, 0.96, 1.00,
        ]
        return [t0 + span * r for r in rel]
    stall = row.get("stall")
    if stall:
        t_stall, pct_stall, t_resume = stall
        n_stall = round(n * pct_stall / 100)
        dt1 = (t_stall - t0) / max(n_stall, 1)
        out = [t0 + dt1 * (i + 1) for i in range(n_stall)]
        rest = n - n_stall
        dt2 = (t1 - t_resume) / max(rest, 1)
        out += [t_resume + dt2 * (i + 1) for i in range(rest)]
        return out
    dt = (t1 - t0) / n
    delays = [t0 + dt * (i + 1) for i in range(n)]
    if effect == "reverse":
        return list(reversed(delays))
    return delays


def pct_steps(row: dict) -> list[tuple[float, float | None, str]]:
    t0, t1 = row["t0"], row["t1"]
    effect = row.get("effect")
    if effect == "bursts":
        span = t1 - t0
        return [
            (t0 + span * 0.13, t0 + span * 0.38, " 25%"),
            (t0 + span * 0.38, t0 + span * 0.70, " 56%"),
            (t0 + span * 0.70, t0 + span * 0.88, " 75%"),
            (t0 + span * 0.88, None, "100%"),
        ]
    stall = row.get("stall")
    if stall:
        t_stall, _pct, t_resume = stall
        return [
            (t0 + 0.12, t0 + (t_stall - t0) * 0.35, "  8%"),
            (t0 + (t_stall - t0) * 0.35, t0 + (t_stall - t0) * 0.65, " 31%"),
            (t0 + (t_stall - t0) * 0.65, t_stall, " 58%"),
            (t_stall, t_resume, " 87%"),
            (t_resume, None, "100%"),
        ]
    pts = [8, 27, 49, 73, 91, 100]
    times = [t0 + (t1 - t0) * (p / 100) for p in pts]
    steps = []
    for i, p in enumerate(pts):
        hide = times[i + 1] if i + 1 < len(times) else None
        steps.append((times[i], hide, f"{p:3d}%"))
    return steps


def pad_dots(key: str, width: int = 36) -> str:
    fill = max(2, width - len(key) - 1)
    return f"{key} {'.' * fill} "


def wrap_words(words: list[str], first: str, cont: str, width: int = 72) -> list[str]:
    lines: list[str] = []
    buf = first
    for i, word in enumerate(words):
        piece = word if buf == first else " " + word
        if len(buf) + len(piece) > width and buf != first:
            lines.append(buf)
            buf = cont + word
        else:
            buf += piece
    if buf.strip():
        lines.append(buf)
    return lines or [first.rstrip()]


def wrap_install(
    names: list[str],
    prefix: str,
    cont_char: str = "\\",
    width: int = 70,
) -> list[str]:
    indent = " " * min(15, max(4, len(prefix)))
    lines: list[str] = []
    buf = prefix
    for name in names:
        piece = name if buf == prefix else " " + name
        extra = 2 if cont_char else 0
        if len(buf) + len(piece) + extra > width and buf != prefix:
            lines.append(buf + ((" " + cont_char) if cont_char else ""))
            buf = indent + name
        else:
            buf += piece
    lines.append(buf)
    return lines


INSTALLERS = {
    "brew": {
        "shell": "unix",
        "whoami_cmd": "whoami",
        "install_cmd": "brew install",
        "cont_char": "\\",
        "updating": " Updating Homebrew...",
        "catalog": "JSON API formula.jws.json",
        "fetch_prefix": " Fetching downloads for: ",
        "pkg_label": lambda n, v: f"Bottle {n} ({v})",
        "summary": lambda n: f"🍺  {n} installed",
    },
    "apt": {
        "shell": "unix",
        "whoami_cmd": "whoami",
        "install_cmd": "sudo apt install",
        "cont_char": "\\",
        "updating": " Reading package lists...",
        "catalog": "Get:1 InRelease [amd64]",
        "fetch_prefix": " The following NEW packages will be installed: ",
        "pkg_label": lambda n, v: f"Get: {n} ({v})",
        "summary": lambda n: f"{n} newly installed, 0 to remove",
    },
    "winget": {
        "shell": "powershell",
        "whoami_cmd": "$env:USERNAME",
        "install_cmd": "winget install",
        "cont_char": "`",
        "updating": " Searching sources...",
        "catalog": "Source: winget",
        "fetch_prefix": " Found: ",
        "pkg_label": lambda n, v: f"{n} [{v}]",
        "summary": lambda n: f"Successfully installed {n} packages",
    },
}


def prompt_html(shell: str) -> str:
    if shell == "powershell":
        return '<tspan class="ps">PS&gt; </tspan>'
    return '<tspan class="prompt">$ </tspan>'


def prompt_plain(shell: str) -> str:
    return "PS> " if shell == "powershell" else "$ "


def duration_for(pkg: dict) -> float:
    effect = pkg.get("effect")
    if effect == "stall":
        return 3.8
    if effect == "reverse":
        return 2.0
    if effect == "bursts":
        return 0.85
    return 1.25


def css_base(cursor_at: float) -> list[str]:
    blink = cursor_at + 0.10
    return [
        "    .term { font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace; font-size: 14px; }",
        "    .prompt { fill: #3fb950; }",
        "    .ps     { fill: #e5c07b; }",
        "    .cmd    { fill: #c9d1d9; }",
        "    .user   { fill: #58a6ff; }",
        "    .ok     { fill: #3fb950; }",
        "    .mid    { fill: #8b949e; }",
        "    .val    { fill: #58a6ff; }",
        "    .ready  { fill: #f0b429; }",
        "    .kw     { fill: #ff7b72; }",
        "    .var    { fill: #c9d1d9; }",
        "    .type   { fill: #ffa657; }",
        "    .key    { fill: #79c0ff; }",
        "    .str    { fill: #a5d6ff; }",
        "    .punc   { fill: #8b949e; }",
        "    .eq     { fill: #3fb950; }",
        "    .track  { fill: #484f58; }",
        "    .hash   { fill: #3fb950; }",
        "    .pct    { fill: #8b949e; }",
        "    .pct-end{ fill: #3fb950; }",
        "    .note   { fill: #6e7681; }",
        "    .beer   { fill: #c9d1d9; }",
        "    .spin-g { opacity: 0; }",
        "    .check  { opacity: 1; }",
        "    .bar    { opacity: 0; }",
        "    .ln     { opacity: 1; }",
        "    .sf     { fill: #58a6ff; opacity: 0; }",
        "    .s0 { animation: sp0 .48s steps(1) infinite; }",
        "    .s1 { animation: sp1 .48s steps(1) infinite; }",
        "    .s2 { animation: sp2 .48s steps(1) infinite; }",
        "    .s3 { animation: sp3 .48s steps(1) infinite; }",
        "    @keyframes appear { from { opacity: 0 } to { opacity: 1 } }",
        "    @keyframes vanish { to { opacity: 0 } }",
        "    @keyframes blink  { 50% { opacity: 0 } }",
        "    @keyframes sp0 { 0%,24% { opacity: 1 } 25%,100% { opacity: 0 } }",
        "    @keyframes sp1 { 0%,24% { opacity: 0 } 25%,49% { opacity: 1 } 50%,100% { opacity: 0 } }",
        "    @keyframes sp2 { 0%,49% { opacity: 0 } 50%,74% { opacity: 1 } 75%,100% { opacity: 0 } }",
        "    @keyframes sp3 { 0%,74% { opacity: 0 } 75%,100% { opacity: 1 } }",
        f"    .cursor {{ fill: #c9d1d9; opacity: 1; animation: appear .1s linear {cursor_at:.2f}s both, blink 1.05s step-end {blink:.2f}s infinite; }}",
        "",
    ]


def orange_ribbon(row_id: str, x: int, y: int) -> str:
    top = y - 12
    return (
        f'      <g class="note note-{row_id}" transform="translate({x} {top})">\n'
        f'        <path fill="#F58220" d="M7 1.1c-2.5 0-4.3 1.9-4.3 4.3 0 1.8.9 3.3 2.7 5.1L3.1 15h2.4l1.5-3.5L8.5 15H11l-2.3-4.5c1.8-1.8 2.7-3.3 2.7-5.1 0-2.4-1.8-4.3-4.4-4.3zm0 1.8c1.3 0 2.4 1 2.4 2.5 0 1.3-.8 2.5-2.4 4.2-1.6-1.7-2.4-2.9-2.4-4.2 0-1.5 1.1-2.5 2.4-2.5z"/>\n'
        f'      </g>\n'
    )


def spinner(row_id: str, y: int) -> str:
    frames = [("s0", "⠋"), ("s1", "⠙"), ("s2", "⠹"), ("s3", "⠸")]
    inner = "\n".join(
        f'        <text x="{ICON_X}" y="{y}" class="term sf {cls}">{ch}</text>'
        for cls, ch in frames
    )
    return f'      <g class="spin-g spin-{row_id}">\n{inner}\n      </g>'


def check(row_id: str, y: int) -> str:
    cy = y - 11
    return (
        f'      <g class="check check-{row_id}" transform="translate({CHECK_X} {cy})">\n'
        f'        <circle cx="7" cy="7" r="7" fill="#3fb950"/>\n'
        f'        <path d="M3.8 7.2 6 9.4 11.2 4.2" fill="none" stroke="#0d1117" '
        f'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>\n'
        f'      </g>'
    )


def bar_group(row: dict, bar_x: int, pct_x: int) -> str:
    i, y = row["id"], row["y"]
    tspans = "".join(
        f'<tspan class="h" style="opacity:0;animation:appear .01s linear {d:.2f}s both">#</tspan>'
        for d in hashes_for(row)
    )
    pcts = []
    for ts, th, lab in pct_steps(row):
        end = " pct-end" if lab.strip() == "100%" else ""
        if th is None:
            anim = f"appear 0s linear {ts:.2f}s both"
        else:
            anim = f"appear 0s linear {ts:.2f}s both, vanish 0s linear {th:.2f}s forwards"
        pcts.append(
            f'        <text x="{pct_x}" y="{y}" class="term pct{end} pstep" '
            f'style="opacity:0;animation:{anim}">{lab}</text>'
        )
    return (
        f'      <g class="bar bar-{i}">\n'
        f'        <text x="{bar_x}" y="{y}" class="term track">{"-" * N_HASH}</text>\n'
        f'        <text x="{bar_x}" y="{y}" class="term hash">{tspans}</text>\n'
        + "\n".join(pcts) + "\n"
        f'      </g>'
    )


def field_svg(y: int, cls: str, key: str, value) -> str:
    indent = "&#160;&#160;"
    if isinstance(value, list):
        inner = ", ".join(f'"{esc(v)}"' for v in value)
        return (
            f'    <text x="24" y="{y}" class="ln {cls}">'
            f'<tspan class="key">{indent}{esc(key)}</tspan>'
            f'<tspan class="punc">: [</tspan>'
            f'<tspan class="str">{inner}</tspan>'
            f'<tspan class="punc">],</tspan></text>'
        )
    return (
        f'    <text x="24" y="{y}" class="ln {cls}">'
        f'<tspan class="key">{indent}{esc(key)}</tspan>'
        f'<tspan class="punc">: </tspan>'
        f'<tspan class="str">"{esc(value)}"</tspan>'
        f'<tspan class="punc">,</tspan></text>'
    )


def build(cfg: dict, today: date | None = None) -> str:
    today = today or date.today()
    window = cfg.get("window", "you@github ~ /profile")
    whoami = cfg.get("whoami", "you")
    boot = cfg.get("boot") or {}
    install_cfg = cfg.get("install") or cfg.get("brew") or {}
    profile = cfg.get("profile") or {}
    kind = str(install_cfg.get("kind") or ("brew" if install_cfg.get("packages") else "none")).lower()
    if kind in {"none", "off", "false"}:
        installer = None
        packages_in = []
    else:
        if kind not in INSTALLERS:
            raise SystemExit(f"unknown install.kind {kind!r} (brew, apt, winget, none)")
        installer = INSTALLERS[kind]
        packages_in = list(install_cfg.get("packages") or [])
    shell = str(cfg.get("shell") or (installer or {}).get("shell") or "unix")
    phtml = prompt_html(shell)
    pplain = prompt_plain(shell)

    packages: list[dict] = []
    used_ids: set[str] = set()
    for raw in packages_in:
        name = str(raw["name"])
        pid = slug(name)
        n = 2
        while pid in used_ids:
            pid = f"{slug(name)}-{n}"
            n += 1
        used_ids.add(pid)
        version = resolve_version(raw.get("version"), today)
        effect = raw.get("effect")
        stall = None
        if effect == "stall":
            dur_tmp = duration_for(raw)
            # filled after t0/t1 known
            stall = True
        packages.append({
            "id": pid,
            "name": name,
            "version": version,
            "label": (installer or INSTALLERS["brew"])["pkg_label"](name, version),
            "note": raw.get("note"),
            "ribbon": bool(raw.get("ribbon")),
            "effect": effect,
            "stall_at": int(raw.get("stall_at", 87)),
            "stall": stall,
        })

    labels = [p["label"] for p in packages] or ["Bottle pkg (0.1.0)"]
    max_label = max(len(s) for s in labels)
    bar_x = int(MSG_X + max_label * CHAR_W + 16)
    pct_x = int(bar_x + N_HASH * CHAR_W + 12)
    width = max(860, pct_x + 70)

    delays: list[tuple[str, float]] = []
    body: list[str] = []
    y = 72
    t = 0.15

    def add_delay(cls: str, when: float) -> None:
        delays.append((cls, when))

    def emit_text(cls: str, when: float, html: str, gap: int = LINE) -> None:
        nonlocal y
        add_delay(cls, when)
        body.append(f'    <text x="24" y="{y}" class="ln {cls}">{html}</text>')
        y += gap

    if whoami:
        whoami_cmd = (installer or INSTALLERS["brew"])["whoami_cmd"]
        if shell == "powershell":
            whoami_cmd = cfg.get("whoami_cmd") or "$env:USERNAME"
        else:
            whoami_cmd = cfg.get("whoami_cmd") or "whoami"
        emit_text(
            "ln-whoami",
            t,
            f'{phtml}<tspan class="cmd">{esc(whoami_cmd)}</tspan>',
        )
        t += 0.35
        emit_text(
            "ln-user",
            t,
            f'<tspan class="user">{esc(whoami)}</tspan>',
        )
        t += 0.50
        y += 24

    steps = list(boot.get("steps") or [])
    if steps or boot.get("command") or boot.get("ready"):
        default_boot = ".\\boot.ps1" if shell == "powershell" else "./boot.sh"
        cmd = boot.get("command", default_boot)
        emit_text(
            "ln-boot",
            t,
            f'{phtml}<tspan class="cmd">{esc(cmd)}</tspan>',
        )
        t += 0.30
        for i, step in enumerate(steps):
            key = pad_dots(str(step.get("key", "step")))
            val = str(step.get("value", "ok"))
            emit_text(
                f"ln-boot-{i}",
                t,
                f'<tspan class="ok">[ OK ]</tspan>'
                f'<tspan class="mid">  {esc(key)}</tspan>'
                f'<tspan class="val">{esc(val)}</tspan>',
            )
            t += 0.30
        ready = boot.get("ready")
        if ready:
            emit_text(
                "ln-ready",
                t,
                '<tspan class="ok">[ OK ]</tspan>'
                '<tspan class="mid">  system ready ▸ </tspan>'
                f'<tspan class="ready">{esc(ready)}</tspan>',
            )
            t += 0.40
        y += 16

    t_pkg = None
    if packages:
        names = [p["name"] for p in packages]
        assert installer is not None
        cmd_prefix = f"{pplain}{installer['install_cmd']} "
        install_lines = wrap_install(names, cmd_prefix, installer["cont_char"])
        for i, line in enumerate(install_lines):
            if i == 0:
                rest = line[len(pplain) :]
                html = f'{phtml}<tspan class="cmd">{esc(rest)}</tspan>'
            else:
                html = f'<tspan class="cmd">{esc(line)}</tspan>'
            emit_text(f"ln-brew-{i}", t, html)
            t += 0.15
        emit_text(
            "ln-upd",
            t,
            f'<tspan class="eq">==&gt;</tspan><tspan class="mid">{esc(installer["updating"])}</tspan>',
        )
        t += 0.20

        json_id = "json"
        json_t0, json_t1 = t, t + 0.50
        json_row = {
            "id": json_id,
            "y": y,
            "t0": json_t0,
            "t1": json_t1,
            "effect": None,
            "stall": None,
        }
        add_delay("ln-json", json_t0)
        delays.append((f"spin-{json_id}", json_t0))  # handled below via rows
        body.append(f'    <g class="ln ln-json">')
        body.append(spinner(json_id, y))
        body.append(check(json_id, y))
        body.append(
            f'      <text x="{MSG_X}" y="{y}" class="cmd">{esc(installer["catalog"])}</text>'
        )
        body.append(bar_group(json_row, bar_x, pct_x))
        body.append("    </g>")
        y += BOTTLE_LINE
        t = json_t1 + 0.15

        fetch_words = [n + "," for n in names[:-1]] + names[-1:]
        fetch_lines = wrap_words(
            fetch_words,
            "==>" + installer["fetch_prefix"],
            "    ",
        )
        for i, line in enumerate(fetch_lines):
            if i == 0:
                html = (
                    '<tspan class="eq">==&gt;</tspan>'
                    f'<tspan class="mid">{esc(line[3:])}</tspan>'
                )
            else:
                html = f'<tspan class="mid">{esc(line)}</tspan>'
            emit_text(f"ln-fetch-{i}", t, html, gap=BOTTLE_LINE if i == 0 else LINE)
            t += 0.10

        t_pkg = t + 0.10
        max_t1 = t_pkg
        for p in packages:
            dur = duration_for(p)
            p["t0"] = t_pkg
            p["t1"] = t_pkg + dur
            p["y"] = y
            if p["effect"] == "stall":
                p["stall"] = (
                    t_pkg + dur * 0.42,
                    p["stall_at"],
                    p["t1"] - 0.30,
                )
            else:
                p["stall"] = None
            max_t1 = max(max_t1, p["t1"])
            add_delay(f"ln-{p['id']}", t_pkg)
            body.append(f'    <g class="ln ln-{p["id"]}">')
            body.append(spinner(p["id"], y))
            body.append(check(p["id"], y))
            body.append(
                f'      <text x="{MSG_X}" y="{y}" class="cmd">{esc(p["label"])}</text>'
            )
            body.append(bar_group(p, bar_x, pct_x))
            if p.get("ribbon"):
                body.append(orange_ribbon(p["id"], bar_x, y).rstrip("\n"))
            elif p.get("note"):
                body.append(
                    f'      <text x="{bar_x}" y="{y}" class="term note note-{p["id"]}">'
                    f'{esc(p["note"])}</text>'
                )
            body.append("    </g>")
            y += BOTTLE_LINE

        t = max_t1 + 0.25
        y += 8
        emit_text(
            "ln-sum",
            t,
            f'<tspan class="beer">{esc(installer["summary"](len(packages)))}</tspan>',
        )
        t += 0.20
        keg = install_cfg.get("keg_only") or install_cfg.get("footnote")
        if keg:
            emit_text(
                "ln-keg",
                t,
                f'<tspan class="mid">    {esc(keg)}</tspan>',
            )
            t += 0.40
        y += 16

    fields = list(profile.get("fields") or [])
    if fields:
        fname = profile.get("file", "profile.ts")
        ident = profile.get("ident", whoami or "me")
        ptype = profile.get("type", "Dev")
        if profile.get("command"):
            show = str(profile["command"])
        elif shell == "powershell":
            show = f"Get-Content {fname}"
        else:
            show = f"cat {fname}"
        emit_text(
            "ln-cat",
            t,
            f'{phtml}<tspan class="cmd">{esc(show)}</tspan>',
        )
        t += 0.30
        emit_text(
            "ln-const",
            t,
            f'<tspan class="kw">const </tspan>'
            f'<tspan class="var">{esc(ident)}</tspan>'
            f'<tspan class="punc">: </tspan>'
            f'<tspan class="type">{esc(ptype)}</tspan>'
            f'<tspan class="punc"> = {{</tspan>',
        )
        t += 0.25
        for i, field in enumerate(fields):
            cls = f"ln-f{i}"
            add_delay(cls, t)
            body.append(field_svg(y, cls, str(field["key"]), field.get("value", "")))
            y += LINE
            t += 0.25
        emit_text("ln-end", t, '<tspan class="punc">};</tspan>')
        t += 0.20

    cursor_y = y + 8
    height = cursor_y + 18
    cursor_at = t + 0.10

    css = css_base(cursor_at)
    for cls, when in delays:
        css.append(f"    .{cls} {{ animation: appear .15s ease {when:.2f}s both; }}")

    rows_meta = []
    if packages:
        rows_meta.append(
            {"id": "json", "t0": json_t0, "t1": json_t1, "note": None, "ribbon": False}
        )
        rows_meta.extend(packages)
    for row in rows_meta:
        i, t0, t1 = row["id"], row["t0"], row["t1"]
        css.append(
            f"    .spin-{i} {{ animation: appear 0s linear {t0:.2f}s both, vanish 0s linear {t1:.2f}s forwards; }}"
        )
        css.append(f"    .check-{i} {{ animation: appear .18s ease {t1:.2f}s both; }}")
        css.append(
            f"    .bar-{i} {{ animation: appear 0s linear {t0:.2f}s both, vanish .18s ease {t1:.2f}s forwards; }}"
        )
        if row.get("note") or row.get("ribbon"):
            css.append(
                f"    .note-{i} {{ animation: appear .25s ease {t1 + 0.05:.2f}s both; }}"
            )

    css.append("")
    css.append("    @media (prefers-reduced-motion: reduce) {")
    css.append("      .ln, .spin-g, .check, .bar, .note, .cursor, .sf, .h, .pstep { animation: none !important; }")
    css.append("      .spin-g, .bar { opacity: 0 !important; }")
    css.append("      .check, .ln, .note { opacity: 1 !important; }")
    css.append("      .cursor { opacity: 1 !important; }")
    css.append("    }")

    pkg_names = " ".join(p["name"] for p in packages)
    bits = [f"whoami → {whoami}"]
    if boot:
        bits.append(str(boot.get("command", "boot")))
    if packages and installer:
        bits.append(f"{installer['install_cmd']} {pkg_names}")
    if fields:
        bits.append(profile.get("file", "profile.ts"))
    aria = "Terminal: " + "; ".join(bits)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-label="{esc(aria)}">
  <defs>
    <style>
{chr(10).join(css)}
    </style>
  </defs>

  <rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="10" fill="#0d1117" stroke="#30363d" stroke-width="1.5"/>
  <line x1="1" y1="40" x2="{width - 1}" y2="40" stroke="#30363d" stroke-width="1"/>
  <circle cx="24" cy="20.5" r="6" fill="#ff5f56"/>
  <circle cx="44" cy="20.5" r="6" fill="#ffbd2e"/>
  <circle cx="64" cy="20.5" r="6" fill="#27c93f"/>
  <text x="{width // 2}" y="25" text-anchor="middle" class="term" fill="#6e7681" font-size="13">{esc(window)}</text>

  <g class="term" xml:space="preserve">
{chr(10).join(body)}
  </g>

  <rect class="cursor" x="24" y="{cursor_y}" width="9" height="4"/>
</svg>
'''


def render(config_path: Path, out_path: Path) -> None:
    cfg = json.loads(config_path.read_text())
    svg = build(cfg)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    previous = out_path.read_text() if out_path.exists() else ""
    if previous == svg:
        print(f"unchanged {out_path}")
        return
    out_path.write_text(svg)
    print(f"wrote {out_path} ({out_path.stat().st_size} bytes)")


def render_examples() -> None:
    examples = ROOT / "examples"
    if not examples.is_dir():
        return
    for path in sorted(examples.glob("*.json")):
        render(path, ROOT / "assets" / f"{path.stem}.svg")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Render a terminal SVG from config.json")
    parser.add_argument("config", nargs="?", default=str(CONFIG))
    parser.add_argument("out", nargs="?", default=None)
    parser.add_argument(
        "--examples",
        action="store_true",
        help="also render examples/*.json into assets/<name>.svg",
    )
    args = parser.parse_args()
    config_path = Path(args.config)
    if not config_path.exists():
        raise SystemExit(f"missing {config_path} — copy an example from examples/ and edit it")
    out_path = Path(args.out) if args.out else OUT
    render(config_path, out_path)
    if args.examples:
        render_examples()


if __name__ == "__main__":
    main()

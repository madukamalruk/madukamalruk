"""
Live telemetry for the profile README.

Pulls data from the GitHub GraphQL + REST APIs and renders self-hosted SVG cards,
so the README never depends on a shared public stats instance going down again.

  dist/diagnostics.svg    contribution / repo counters
  dist/languages.svg      language mix, colour-coded like a resistor
  dist/repo-<name>.svg    pinned-project cards (live stars, forks, last push)

Env:
  GH_TOKEN  token used for the API (GITHUB_TOKEN in Actions, or a PAT with
            `repo` + `read:user` to include private-repo languages)
  GH_USER   defaults to madukamalruk

    python scripts/telemetry.py --out dist
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import math
import os
import sys
import urllib.request
from pathlib import Path

USER = os.environ.get("GH_USER", "madukamalruk")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")

FEATURED = [
    "Micromouse-V2.0",
    "uom-maze-solver-2025",
    "robo-mouse-v5-pcb",
    "Neo-Mouse-PCB",
    "jac-personal-planner",
    "AI-Hackathon-2026-V1",
]
# notebooks / generated markup dwarf real source code in byte counts
LANG_EXCLUDE = {"Jupyter Notebook", "HTML", "CSS", "TeX", "Makefile", "CMake", "Batchfile"}

TZ = dt.timezone(dt.timedelta(hours=5, minutes=30), "SLST")
MONO = "'JetBrains Mono','SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace"

BG = "#0b1426"
PANEL = "#060b16"
GRID = "#13223f"
LINE = "#1f3358"
CYAN = "#3ee8ff"
AMBER = "#ffb52e"
GREEN = "#3dff8b"
RED = "#ff4d5e"
TEXT = "#e6eefc"
DIM = "#5f7aa8"


# ---------------------------------------------------------------- API ----
def _req(url: str, body: dict | None = None):
    headers = {"User-Agent": "profile-telemetry", "Accept": "application/vnd.github+json"}
    if TOKEN:
        headers["Authorization"] = f"bearer {TOKEN}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=40) as res:
        return json.loads(res.read())


def gql(query: str, **variables):
    out = _req("https://api.github.com/graphql", {"query": query, "variables": variables})
    if out.get("errors"):
        raise RuntimeError(json.dumps(out["errors"], indent=2))
    return out["data"]


def fetch():
    base = gql(
        """query($login:String!){
          user(login:$login){
            name createdAt
            followers{totalCount}
            public: repositories(ownerAffiliations:OWNER, privacy:PUBLIC, isFork:false, first:100){
              totalCount
              nodes{ name description url stargazerCount forkCount pushedAt
                     primaryLanguage{name color} }
            }
            owned: repositories(ownerAffiliations:OWNER, isFork:false, first:100){
              nodes{ languages(first:12, orderBy:{field:SIZE, direction:DESC}){
                       edges{ size node{ name color } } } }
            }
            contributed: repositoriesContributedTo(first:1, contributionTypes:[COMMIT,PULL_REQUEST,ISSUE]){ totalCount }
          }
        }""",
        login=USER,
    )["user"]

    now = dt.datetime.now(dt.timezone.utc)
    first_year = int(base["createdAt"][:4])
    years = {}
    for y in range(first_year, now.year + 1):
        start = f"{y}-01-01T00:00:00Z"
        end = now.strftime("%Y-%m-%dT%H:%M:%SZ") if y == now.year else f"{y}-12-31T23:59:59Z"
        years[y] = gql(
            """query($login:String!,$from:DateTime!,$to:DateTime!){
              user(login:$login){ contributionsCollection(from:$from,to:$to){
                totalCommitContributions totalPullRequestContributions totalIssueContributions
                totalPullRequestReviewContributions restrictedContributionsCount
                contributionCalendar{ totalContributions weeks{ contributionDays{ date contributionCount } } }
              } } }""",
            login=USER, **{"from": start, "to": end},
        )["user"]["contributionsCollection"]

    return base, years


# ----------------------------------------------------------- helpers ----
def esc(s) -> str:
    return html.escape(str(s), quote=True)


def fmt(n: int) -> str:
    return f"{n / 1000:.1f}k" if n >= 10000 else f"{n:,}"


def stamp() -> str:
    return dt.datetime.now(TZ).strftime("%Y-%m-%d %H:%M SLST")


def ago(iso: str) -> str:
    then = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    d = (dt.datetime.now(dt.timezone.utc) - then).days
    if d <= 0:
        return "today"
    if d == 1:
        return "yesterday"
    if d < 30:
        return f"{d}d ago"
    if d < 365:
        return f"{d // 30}mo ago"
    return f"{d // 365}y ago"


def wrap(text: str, width: int, lines: int) -> list[str]:
    words, out, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) > width:
            out.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}" if cur else w
    if cur:
        out.append(cur)
    if len(out) > lines:
        out = out[:lines]
        out[-1] = out[-1][: width - 1].rstrip() + "…"
    return out


def frame(w: int, h: int, title: str, ref: str, body: str, label: str, sync: bool = True) -> str:
    sync_line = (f'<text x="{w - 18}" y="{h - 12}" font-size="9" fill="{DIM}" text-anchor="end">SYNC {esc(stamp())}</text>'
                 if sync else "")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{esc(label)}">
<title>{esc(label)}</title>
<style>
  text {{ font-family: {MONO}; }}
  .blink {{ animation: b 1.4s steps(1) infinite; }}
  @keyframes b {{ 50% {{ opacity: .15 }} }}
  .grow {{ transform-box: fill-box; transform-origin: left; animation: grow 1.2s cubic-bezier(.2,.8,.2,1) both; }}
  @keyframes grow {{ from {{ transform: scaleX(0) }} }}
  .rise {{ transform-box: fill-box; transform-origin: bottom; animation: rise .9s cubic-bezier(.2,.8,.2,1) both; }}
  @keyframes rise {{ from {{ transform: scaleY(0) }} }}
  .draw {{ stroke-dasharray: 4000; animation: draw 2.6s ease-out both; }}
  @keyframes draw {{ from {{ stroke-dashoffset: 4000 }} to {{ stroke-dashoffset: 0 }} }}
  .fade {{ animation: fade .8s ease-out both; }}
  @keyframes fade {{ from {{ opacity: 0 }} }}
</style>
<defs>
  <pattern id="g" width="20" height="20" patternUnits="userSpaceOnUse"><path d="M20 0H0V20" fill="none" stroke="{GRID}"/></pattern>
  <filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>
<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="10" fill="{BG}" stroke="{LINE}" stroke-width="2"/>
<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="10" fill="url(#g)" opacity=".7"/>
<circle class="blink" cx="20" cy="22" r="4" fill="{GREEN}"/>
<text x="32" y="26" font-size="13" font-weight="700" fill="{TEXT}" letter-spacing="2">{esc(title)}</text>
<text x="{w - 18}" y="26" font-size="10" fill="{DIM}" text-anchor="end">{esc(ref)}</text>
<line x1="16" y1="38" x2="{w - 16}" y2="38" stroke="{LINE}" stroke-width="1.5"/>
{body}
{sync_line}
</svg>"""


# ------------------------------------------------------------- cards ----
def all_days(years) -> list[tuple[str, int]]:
    days = []
    for y in sorted(years):
        for wk in years[y]["contributionCalendar"]["weeks"]:
            for d in wk["contributionDays"]:
                days.append((d["date"], d["contributionCount"]))
    today = dt.datetime.now(TZ).date().isoformat()
    return sorted({d: c for d, c in days if d <= today}.items())


def card_diag(base, years, days) -> str:
    w, h = 490, 290
    now = dt.datetime.now(TZ).year
    cur = years[now]
    total_all = sum(v["contributionCalendar"]["totalContributions"] for v in years.values())
    stars = sum(r["stargazerCount"] for r in base["public"]["nodes"])
    rows = [
        ("COMMITS", cur["totalCommitContributions"], f"{now}", GREEN),
        ("PULL REQUESTS", cur["totalPullRequestContributions"], f"{now}", CYAN),
        ("ISSUES", cur["totalIssueContributions"], f"{now}", CYAN),
        ("CODE REVIEWS", cur["totalPullRequestReviewContributions"], f"{now}", CYAN),
        ("PUBLIC REPOS", base["public"]["totalCount"], "owned", AMBER),
        ("STARS EARNED", stars, "public", AMBER),
        ("CONTRIBUTED TO", base["contributed"]["totalCount"], "repos", AMBER),
        ("FOLLOWERS", base["followers"]["totalCount"], "", TEXT),
    ]
    peak = max([v for _, v, _, _ in rows] + [1])
    out = [
        f'<text x="22" y="66" font-size="9" fill="{DIM}">TOTAL CONTRIBUTIONS · SINCE {base["createdAt"][:4]}</text>',
        f'<text x="22" y="104" font-size="38" font-weight="800" fill="{GREEN}" filter="url(#glow)" class="fade">{fmt(total_all)}</text>',
        f'<text x="22" y="126" font-size="10" fill="{DIM}">{fmt(cur["contributionCalendar"]["totalContributions"])} in {now} · {fmt(cur["restrictedContributionsCount"])} private</text>',
    ]
    # analog gauge: share of days active this year
    year_days = [c for d, c in days if d.startswith(str(now))]
    ratio = sum(1 for c in year_days if c) / max(len(year_days), 1)
    gx, gy, gr = 112, 214, 64
    arc_bg = f"M{gx - gr} {gy} A{gr} {gr} 0 0 1 {gx + gr} {gy}"
    ang = math.pi * (1 - ratio)
    ex, ey = gx + gr * math.cos(ang), gy - gr * math.sin(ang)
    out.append(f'<path d="{arc_bg}" fill="none" stroke="{LINE}" stroke-width="10" stroke-linecap="round"/>')
    out.append(f'<path class="draw" d="M{gx - gr} {gy} A{gr} {gr} 0 0 1 {ex:.1f} {ey:.1f}" fill="none" stroke="{CYAN}" stroke-width="10" stroke-linecap="round"/>')
    for k in range(11):
        a = math.pi * (1 - k / 10)
        x1, y1 = gx + (gr - 16) * math.cos(a), gy - (gr - 16) * math.sin(a)
        x2, y2 = gx + (gr - 10) * math.cos(a), gy - (gr - 10) * math.sin(a)
        out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{DIM}" stroke-width="1.5"/>')
    nx, ny = gx + (gr - 18) * math.cos(ang), gy - (gr - 18) * math.sin(ang)
    out.append(f'<line x1="{gx}" y1="{gy}" x2="{nx:.1f}" y2="{ny:.1f}" stroke="{AMBER}" stroke-width="3" stroke-linecap="round"/>')
    out.append(f'<circle cx="{gx}" cy="{gy}" r="5" fill="{AMBER}"/>')
    out.append(f'<text x="{gx}" y="{gy + 22}" font-size="16" font-weight="700" fill="{TEXT}" text-anchor="middle">{ratio * 100:.0f}%</text>')
    out.append(f'<text x="{gx}" y="{gy + 36}" font-size="8" fill="{DIM}" text-anchor="middle">DAYS ACTIVE · {now}</text>')

    for i, (k, v, sub, c) in enumerate(rows):
        y = 64 + i * 25
        out.append(f'<text x="230" y="{y}" font-size="10" fill="{DIM}">{k}</text>')
        out.append(f'<text x="470" y="{y}" font-size="13" font-weight="700" fill="{c}" text-anchor="end">{fmt(v)}</text>')
        bw = 0 if v == 0 else max(4, 240 * math.log1p(v) / math.log1p(peak))
        out.append(f'<rect x="230" y="{y + 5}" width="240" height="4" rx="2" fill="{PANEL}"/>')
        out.append(f'<rect class="grow" x="230" y="{y + 5}" width="{bw:.1f}" height="4" rx="2" fill="{c}" opacity=".85" style="animation-delay:{i * .08:.2f}s"/>')
    return frame(w, h, "SYSTEM DIAGNOSTICS", "REF·MM-T2", "\n".join(out), "GitHub statistics for " + USER)


def card_langs(base) -> str:
    w, h = 490, 290
    totals: dict[str, list] = {}
    for repo in base["owned"]["nodes"]:
        for e in repo["languages"]["edges"]:
            name = e["node"]["name"]
            if name in LANG_EXCLUDE:
                continue
            t = totals.setdefault(name, [0, e["node"]["color"] or "#8b949e"])
            t[0] += e["size"]
    ranked = sorted(totals.items(), key=lambda kv: -kv[1][0])
    grand = sum(v[0] for _, v in ranked) or 1
    top = ranked[:8]

    out = []
    # resistor whose colour bands are the top four languages
    rx, ry = 70, 58
    out.append(f'<line x1="22" y1="{ry + 22}" x2="{rx}" y2="{ry + 22}" stroke="#9aa6bd" stroke-width="4"/>')
    out.append(f'<line x1="{rx + 300}" y1="{ry + 22}" x2="{w - 22}" y2="{ry + 22}" stroke="#9aa6bd" stroke-width="4"/>')
    out.append(f'<rect x="{rx}" y="{ry}" width="300" height="44" rx="20" fill="#d8c7a0"/>')
    out.append(f'<rect x="{rx + 8}" y="{ry + 4}" width="284" height="8" rx="4" fill="#fff" opacity=".25"/>')
    for i, (name, (_, color)) in enumerate(top[:4]):
        bx = rx + 50 + i * 46 + (40 if i == 3 else 0)
        out.append(f'<rect class="rise" x="{bx}" y="{ry}" width="18" height="44" fill="{color}" style="animation-delay:{i * .12:.2f}s"/>')
    out.append(f'<text x="{w / 2}" y="{ry + 64}" font-size="9" fill="{DIM}" text-anchor="middle">BANDS = TOP-4 LANGUAGES BY BYTES · {len(ranked)} LANGUAGES TOTAL</text>')

    # stacked bar
    sx, sy, sw = 22, 142, w - 44
    acc = 0.0
    for i, (name, (size, color)) in enumerate(ranked):
        seg = sw * size / grand
        if seg < 0.6:
            continue
        out.append(f'<rect class="grow" x="{sx + acc:.1f}" y="{sy}" width="{seg:.1f}" height="10" fill="{color}" style="animation-delay:{i * .06:.2f}s"/>')
        acc += seg
    for i, (name, (size, color)) in enumerate(top):
        col, row = i % 2, i // 2
        x = 22 + col * 232
        y = 178 + row * 24
        pct = 100 * size / grand
        out.append(f'<rect x="{x}" y="{y - 9}" width="10" height="10" rx="2" fill="{color}"/>')
        out.append(f'<text x="{x + 18}" y="{y}" font-size="11" fill="{TEXT}">{esc(name)}</text>')
        out.append(f'<text x="{x + 210}" y="{y}" font-size="11" fill="{DIM}" text-anchor="end">{pct:.1f}%</text>')
    return frame(w, h, "LANGUAGE SPECTRUM", "REF·MM-T3", "\n".join(out), "Most used languages")


def card_repo(repo) -> str:
    w, h = 490, 150
    lang = repo["primaryLanguage"] or {"name": "Hardware / KiCad", "color": "#d9c64a"}
    desc = repo["description"] or "PCB design files — schematics, layout and fabrication outputs."
    lines = wrap(desc, 62, 3)
    out = [f'<text x="22" y="{60 + i * 16}" font-size="11" fill="#9fb3d9">{esc(l)}</text>' for i, l in enumerate(lines)]
    out.append(f'<circle cx="28" cy="126" r="5" fill="{lang["color"] or "#8b949e"}"/>')
    out.append(f'<text x="40" y="130" font-size="11" fill="{TEXT}">{esc(lang["name"])}</text>')
    out.append(f'<text x="210" y="130" font-size="11" fill="{AMBER}">★ {repo["stargazerCount"]}</text>')
    out.append(f'<text x="262" y="130" font-size="11" fill="{DIM}">⑂ {repo["forkCount"]}</text>')
    out.append(f'<text x="310" y="130" font-size="10" fill="{DIM}">push {ago(repo["pushedAt"])}</text>')
    # tiny QFP chip in the corner
    cx, cy = w - 54, 84
    out.append(f'<rect x="{cx - 14}" y="{cy - 14}" width="28" height="28" rx="2" fill="#111" stroke="#444"/>')
    for k in range(4):
        o = -9 + k * 6
        out += [f'<rect x="{cx + o}" y="{cy - 19}" width="3" height="5" fill="#d9c64a"/>',
                f'<rect x="{cx + o}" y="{cy + 14}" width="3" height="5" fill="#d9c64a"/>',
                f'<rect x="{cx - 19}" y="{cy + o}" width="5" height="3" fill="#d9c64a"/>',
                f'<rect x="{cx + 14}" y="{cy + o}" width="5" height="3" fill="#d9c64a"/>']
    out.append(f'<circle cx="{cx - 8}" cy="{cy - 8}" r="2" fill="#333"/>')
    body = "\n".join(out)
    return frame(w, h, repo["name"], "REPO", body, f"{repo['name']} repository", sync=False)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="dist")
    args = ap.parse_args()
    if not TOKEN:
        sys.exit("GH_TOKEN is not set")

    base, years = fetch()
    days = all_days(years)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    cards = {
        "diagnostics.svg": card_diag(base, years, days),
        "languages.svg": card_langs(base),
    }
    by_name = {r["name"]: r for r in base["public"]["nodes"]}
    for name in FEATURED:
        if name in by_name:
            cards[f"repo-{name}.svg"] = card_repo(by_name[name])
    for fn, svg in cards.items():
        (out / fn).write_text(svg, encoding="utf-8")
    print(f"wrote {len(cards)} cards to {out}/")


if __name__ == "__main__":
    main()

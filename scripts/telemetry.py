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

BG = "#0A0D14"        # card surface (obsidian)
PANEL = "#06070A"     # tiles
LINE = "#1C2330"
CYAN = "#00E5FF"
AMBER = "#FFB52E"
GREEN = "#3DD68C"
RED = "#E5484D"
TEXT = "#E6EDF5"
DIM = "#5A6E85"       # muted slate for secondary labels
HAIR = 'stroke="#FFFFFF" stroke-opacity=".08" stroke-width="1"'   # 1px hairline border

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
    sync_line = (f'<text x="{w - 16}" y="{h - 12}" font-size="9" fill="{DIM}" text-anchor="end">'
                 f'updated {esc(stamp())}</text>' if sync else "")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{esc(label)}">
<title>{esc(label)}</title>
<style>
  text {{ font-family: {MONO}; }}
  .grow {{ transform-box: fill-box; transform-origin: left; animation: grow 1.1s cubic-bezier(.2,.8,.2,1) both; }}
  @keyframes grow {{ from {{ transform: scaleX(0) }} }}
  .draw {{ stroke-dasharray: 1200; animation: draw 1.6s ease-out both; }}
  @keyframes draw {{ from {{ stroke-dashoffset: 1200 }} to {{ stroke-dashoffset: 0 }} }}
  .fade {{ animation: fade .7s ease-out both; }}
  @keyframes fade {{ from {{ opacity: 0 }} }}
</style>
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="8" fill="{BG}" {HAIR}/>
<rect x="16" y="18" width="6" height="6" rx="1" fill="{CYAN}"/>
<text x="30" y="24.5" font-size="11" font-weight="600" fill="{TEXT}" letter-spacing="2.5">{esc(title)}</text>
<text x="{w - 16}" y="24.5" font-size="9" fill="{DIM}" text-anchor="end" letter-spacing="1">{esc(ref)}</text>
<line x1="16" y1="38.5" x2="{w - 16}" y2="38.5" {HAIR}/>
{body}
{sync_line}
</svg>"""


# ------------------------------------------------------------- data ----
def all_days(years) -> list[tuple[str, int]]:
    days = []
    for y in sorted(years):
        for wk in years[y]["contributionCalendar"]["weeks"]:
            for d in wk["contributionDays"]:
                days.append((d["date"], d["contributionCount"]))
    today = dt.datetime.now(TZ).date().isoformat()
    return sorted({d: c for d, c in days if d <= today}.items())


def streaks(days):
    longest = run = 0
    for _, c in days:
        run = run + 1 if c else 0
        longest = max(longest, run)
    seq = list(days)
    if seq and seq[-1][1] == 0:  # today not committed yet: streak still alive
        seq = seq[:-1]
    current = 0
    for _, c in reversed(seq):
        if not c:
            break
        current += 1
    return current, longest


def lang_totals(base):
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
    return [(name, size / grand, color) for name, (size, color) in ranked]


def diversity(langs) -> float:
    """Normalised Shannon index: 0 = one language, 1 = perfectly even mix."""
    if len(langs) < 2:
        return 0.0
    h = -sum(p * math.log(p) for _, p, _ in langs if p > 0)
    return h / math.log(len(langs))


def readable(hex_color: str) -> str:
    """Lift very dark GitHub language colours so traces stay visible on obsidian."""
    c = hex_color.lstrip("#")
    if len(c) != 6:
        return CYAN
    r_, g_, b_ = (int(c[i:i + 2], 16) for i in (0, 2, 4))
    lum = (0.2126 * r_ + 0.7152 * g_ + 0.0722 * b_) / 255
    if lum >= 0.35:
        return "#" + c
    mix = lambda v: int(v + (255 - v) * 0.45)
    return f"#{mix(r_):02x}{mix(g_):02x}{mix(b_):02x}"


# ------------------------------------------------------------- cards ----
def tile(x, y, w, h, label) -> str:
    return (f'<rect x="{x + .5}" y="{y + .5}" width="{w}" height="{h}" rx="6" fill="{PANEL}" {HAIR}/>'
            f'<text x="{x + 14}" y="{y + 20}" font-size="9" fill="{DIM}" letter-spacing="1.5">{esc(label)}</text>')


def card_diag(base, years, days) -> str:
    w, h = 490, 290
    year = dt.datetime.now(TZ).year
    cur = years[year]
    total_all = sum(v["contributionCalendar"]["totalContributions"] for v in years.values())
    this_year = cur["contributionCalendar"]["totalContributions"]
    commits = cur["totalCommitContributions"]
    prs = cur["totalPullRequestContributions"]
    stars = sum(r["stargazerCount"] for r in base["public"]["nodes"])
    repos = base["public"]["totalCount"]
    cur_streak, best_streak = streaks(days)
    langs = lang_totals(base)
    idx = diversity(langs)

    tw, th, gap = 224, 100, 10
    xs, ys = (16, 16 + tw + gap), (52, 52 + th + gap)
    out = []

    # A · total contributions (hero metric)
    x, y = xs[0], ys[0]
    out.append(tile(x, y, tw, th, "TOTAL CONTRIBUTIONS"))
    out.append(f'<text x="{x + 14}" y="{y + 64}" font-size="36" font-weight="700" fill="{TEXT}" class="fade">{fmt(total_all)}</text>')
    out.append(f'<text x="{x + 14}" y="{y + 86}" font-size="10" fill="{CYAN}">+{fmt(this_year)} in {year}</text>')
    out.append(f'<text x="{x + tw - 14}" y="{y + 86}" font-size="9" fill="{DIM}" text-anchor="end">since {base["createdAt"][:4]}</text>')

    # B · commits + streak ring
    x, y = xs[1], ys[0]
    out.append(tile(x, y, tw, th, f"COMMITS · {year}"))
    out.append(f'<text x="{x + 14}" y="{y + 64}" font-size="30" font-weight="700" fill="{TEXT}" class="fade">{fmt(commits)}</text>')
    sub = f"best streak {best_streak}d" + (f" · {prs} PRs" if prs else "")
    out.append(f'<text x="{x + 14}" y="{y + 86}" font-size="9" fill="{DIM}">{esc(sub)}</text>')
    cx, cy, rr = x + tw - 44, y + 52, 26
    circ = 2 * math.pi * rr
    frac = min(cur_streak / best_streak, 1) if best_streak else 0
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{rr}" fill="none" stroke="#FFFFFF" stroke-opacity=".08" stroke-width="4"/>')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{rr}" fill="none" stroke="{CYAN}" stroke-width="4" stroke-linecap="round" '
               f'stroke-dasharray="{circ * frac:.1f} {circ:.1f}" transform="rotate(-90 {cx} {cy})"/>')
    out.append(f'<text x="{cx}" y="{cy + 4}" font-size="14" font-weight="700" fill="{TEXT}" text-anchor="middle">{cur_streak}d</text>')
    out.append(f'<text x="{cx}" y="{cy + 40}" font-size="8" fill="{DIM}" text-anchor="middle" letter-spacing="1">STREAK</text>')

    # C · repositories + stars
    x, y = xs[0], ys[1]
    out.append(tile(x, y, tw, th, "SHIPPED"))
    half = tw // 2
    out.append(f'<text x="{x + 14}" y="{y + 64}" font-size="30" font-weight="700" fill="{TEXT}" class="fade">{repos}</text>')
    out.append(f'<text x="{x + 14}" y="{y + 86}" font-size="9" fill="{DIM}">public repos</text>')
    out.append(f'<line x1="{x + half + .5}" y1="{y + 36}" x2="{x + half + .5}" y2="{y + 88}" {HAIR}/>')
    out.append(f'<text x="{x + half + 14}" y="{y + 64}" font-size="30" font-weight="700" fill="{AMBER}" class="fade">{stars}</text>')
    out.append(f'<text x="{x + half + 14}" y="{y + 86}" font-size="9" fill="{DIM}">stars earned</text>')

    # D · stack diversity
    x, y = xs[1], ys[1]
    out.append(tile(x, y, tw, th, "STACK DIVERSITY"))
    out.append(f'<text x="{x + 14}" y="{y + 64}" font-size="30" font-weight="700" fill="{TEXT}" class="fade">{idx:.2f}</text>')
    out.append(f'<text x="{x + tw - 14}" y="{y + 64}" font-size="10" fill="{DIM}" text-anchor="end">{len(langs)} languages</text>')
    lit = round(idx * 10)
    for k in range(10):
        on = k < lit
        out.append(f'<rect x="{x + 14 + k * 20}" y="{y + 80}" width="16" height="4" rx="1" '
                   f'fill="{CYAN if on else "#FFFFFF"}" fill-opacity="{1 if on else .08}"/>')

    out.append(f'<text x="16" y="{h - 12}" font-size="9" fill="{DIM}">github.com/{USER}</text>')
    return frame(w, h, "TELEMETRY", "MM-T1", "\n".join(out), "GitHub statistics for " + USER)


def card_langs(base) -> str:
    """Logic-analyser view: one channel per language, pulse width = share of code."""
    w, h = 490, 290
    langs = lang_totals(base)
    top = langs[:6]
    full = max(10, math.ceil(top[0][1] * 100 / 10) * 10) if top else 100   # full-scale in %
    x0, x1 = 150, 420
    span = x1 - x0
    out = []

    # time ruler
    ry = 56
    out.append(f'<line x1="{x0}" y1="{ry + .5}" x2="{x1}" y2="{ry + .5}" {HAIR}/>')
    steps = 4
    for k in range(steps + 1):
        tx = x0 + span * k / steps
        out.append(f'<line x1="{tx:.1f}" y1="{ry - 3}" x2="{tx:.1f}" y2="{ry + 3}" stroke="{DIM}" stroke-width="1"/>')
        out.append(f'<line x1="{tx:.1f}" y1="{ry + 8}" x2="{tx:.1f}" y2="{h - 34}" stroke="#FFFFFF" stroke-opacity=".04" stroke-dasharray="2 4"/>')
        out.append(f'<text x="{tx:.1f}" y="{ry - 7}" font-size="8" fill="{DIM}" text-anchor="middle">{full * k // steps}%</text>')
    out.append(f'<path d="M{x0 - 4} {ry - 12} h8 l-4 6 z" fill="{CYAN}"/>')   # trigger marker

    row_h = 30
    for i, (name, share, color) in enumerate(top):
        y = 80 + i * row_h
        lo, hi = y + 9, y - 7
        col = readable(color)
        pw = max(2.0, span * share * 100 / full)
        out.append(f'<text x="16" y="{y + 5}" font-size="9" fill="{DIM}">CH{i + 1}</text>')
        out.append(f'<text x="46" y="{y + 5}" font-size="11" fill="{TEXT}">{esc(name[:12])}</text>')
        out.append(f'<rect class="grow" x="{x0}" y="{hi}" width="{pw:.1f}" height="{lo - hi}" fill="{col}" fill-opacity=".12" '
                   f'style="animation-delay:{i * .08:.2f}s"/>')
        d = f"M{x0 - 8} {lo} H{x0} V{hi} H{x0 + pw:.1f} V{lo} H{x1}"
        out.append(f'<path class="draw" d="{d}" fill="none" stroke="{col}" stroke-width="1.6" '
                   f'stroke-linejoin="miter" style="animation-delay:{i * .08:.2f}s"/>')
        out.append(f'<text x="{w - 16}" y="{y + 5}" font-size="11" fill="{TEXT}" text-anchor="end">{share * 100:.1f}%</text>')

    out.append(f'<text x="16" y="{h - 12}" font-size="9" fill="{DIM}">{len(langs)} languages · share of bytes</text>')
    return frame(w, h, "LANGUAGE ANALYZER", "MM-T2", "\n".join(out), "Most used languages")


def card_repo(repo) -> str:
    w, h = 490, 150
    lang = repo["primaryLanguage"] or {"name": "Hardware / KiCad", "color": "#C9A227"}
    desc = repo["description"] or "PCB design files — schematics, layout and fabrication outputs."
    lines = wrap(desc, 62, 3)
    out = [f'<text x="22" y="{60 + i * 16}" font-size="11" fill="#9AA9BC">{esc(l)}</text>' for i, l in enumerate(lines)]
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
        out += [f'<rect x="{cx + o}" y="{cy - 19}" width="3" height="5" fill="#C9A227"/>',
                f'<rect x="{cx + o}" y="{cy + 14}" width="3" height="5" fill="#C9A227"/>',
                f'<rect x="{cx - 19}" y="{cy + o}" width="5" height="3" fill="#C9A227"/>',
                f'<rect x="{cx + 14}" y="{cy + o}" width="5" height="3" fill="#C9A227"/>']
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

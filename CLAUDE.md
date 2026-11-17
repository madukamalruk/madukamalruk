# madukamalruk (GitHub profile README)

Public GitHub profile repo for Maduka Malruk: a datasheet-style `README.md` with self-built animated SVG art and self-hosted live stat cards. Status: **maintenance mode**. Full requirements: `docs/prd.md`. Current plan & progress: `docs/plan.md`. Decisions: `docs/decisions.md`.

## Stack
- Language / runtime: Python 3 (standard library only, no dependencies)
- Content: GitHub-flavoured Markdown + inline HTML, Mermaid, hand-built SVG (CSS/SMIL animation)
- CI: GitHub Actions (`.github/workflows/profile.yml`), `Platane/snk`, `crazy-max/ghaction-github-pages`
- Testing: none (verify by rebuilding and viewing the README)
- Hosting: GitHub profile page; generated cards live on the `output` branch

## Commands
- Install: nothing to install
- Rebuild banner + footer art: `python scripts/build_banner.py` (writes `assets/madukz-space.svg`, `assets/footer.svg`)
- Build stat/project cards locally: `GH_TOKEN=$GH_TOKEN python scripts/telemetry.py --out dist` (needs network; token from env, never inline)
- Syntax check: `python -m py_compile scripts/build_banner.py scripts/telemetry.py`
- Preview locally: launch config `readme-preview` in `../.claude/launch.json` (serves this folder on port 8765)
- CI: runs every 3 h, on push to `main`, or manually (`workflow_dispatch`)

## Layout
```
README.md                  # the profile page itself
assets/                    # committed SVG art (banner, footer, trace divider)
scripts/build_banner.py    # source of madukz-space.svg + footer.svg
scripts/telemetry.py       # renders dist/*.svg cards from the GitHub API
.github/workflows/         # profile.yml: telemetry + snake -> `output` branch
dist/                      # gitignored build output
docs/                      # prd.md, plan.md, decisions.md
```

## Code style
- SVGs must render inside GitHub's `<img>` sandbox: no JS, no external fonts, CSS/SMIL animation only.
- Palette: obsidian `#06070A`/`#0A0D14`, cyan `#00E5FF`, amber/copper/gold accents. Keep README chips `0A0D14` + `00E5FF`.
- Scripts stay stdlib-only; place shapes on the 4px grid used in `build_banner.py`.
- Comments: explain *why*, not *what*.

## Architecture rules
- `assets/madukz-space.svg` and `assets/footer.svg` are generated: change `scripts/build_banner.py`, then rebuild. Never hand-edit the SVG.
- README live images point at `raw.githubusercontent.com/madukamalruk/madukamalruk/output/...`; the workflow is the only writer of `output`.
- Featured project cards = `FEATURED` list in `scripts/telemetry.py`; keep it in sync with the README Build Log.

## Always
- Work from `docs/plan.md`, one step at a time; tick the box only after its verification passes.
- After changing `build_banner.py`, rebuild and check `git diff assets/` shows only the intended change.
- Run the syntax check before saying a script change is done.

## Never
- Commit secrets; tokens come from `$GH_TOKEN` / Actions secrets (`METRICS_TOKEN`). Real values in `.env` (gitignored).
- Push to `output` by hand, or delete `backup/readme-before-redesign`.
- Add a dependency or a third-party stats service without saying why (self-hosting was deliberate).
- Put private details in the README; this repo is public.

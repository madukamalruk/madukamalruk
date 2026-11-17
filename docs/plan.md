# Plan: madukamalruk profile README

_Last updated: 2026-11-18 · Mode: maintenance_

## Done so far (from git history)
- 2026-02: first README with badges, trophies, activity graphs and a snake workflow.
- Iterations: animated SVG terminal, walking-cat animation, neon-cyan header/footer.
- Redesign: MADUKZ SPACE lab banner (`build_banner.py`), self-hosted stats (`telemetry.py`), one `profile.yml` workflow.
- v2: precision-datasheet redesign; README cards point at the `output` branch.
- 2026-11-18: datasheet-style README (numbered sections, chips, trace divider, results table); typing header restored; `AI-Hackathon-2026-V1` replaced by `unipathlk-v1`; private details removed.
- 2026-11-18: onboarded to the Claude workflow (this file, `CLAUDE.md`, PRD, decisions, `.gitignore`).

## Next up
- [ ] **Align the banner script with the committed SVG.** In `scripts/build_banner.py:480`, change the rect at x=772,y=336 to `fill="#0B0D11"` with no stroke.
  - Verify: run `python scripts/build_banner.py`, then `git status` shows `assets/` unchanged (byte-identical).
- [ ] **Remove the dead `v2` push trigger** in `.github/workflows/profile.yml` (`branches: [main]`).
  - Verify: the YAML parses; the next push to `main` runs the workflow green and `output` refreshes.
- [ ] **Delete the stale `dist/mermaid.html`** (untracked; preview of an old diagram).
  - Verify: `dist/` is empty locally and `git status` is clean.
- [ ] **Content updates as projects land.** For each new project: add the repo to `FEATURED` in `scripts/telemetry.py`, add a Build Log cell in README, and add any result to the Results table.
  - Verify: after pushing to `main`, the workflow is green, `repo-<name>.svg` exists on `output`, and the card renders on the profile.

## Later / maybe
- [ ] Self-host the streak stats and typing header (see PRD open questions).

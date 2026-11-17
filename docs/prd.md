# madukamalruk profile README: PRD

_Status: Reverse-engineered, 2026-11-18 · Mode: maintenance_

## 1. Problem
Visitors to github.com/madukamalruk (recruiters, competition teams, fellow students) need to see quickly who Maduka is, what Maduka builds (micromouse robots, PCBs, firmware, software) and how to get in touch. Shared public stats services had gone down before, which left broken images on the profile.

## 2. Users
- Primary: people visiting the GitHub profile.
- Secondary: Maduka, who updates the content.

## 3. Goals
- G1: a distinctive, on-brand profile in the same palette as madukamalruk.com.lk.
- G2: live stats and project cards that don't depend on third-party stat instances.
- G3: content that is easy to update (projects, results).

## 4. Non-goals
- Not a portfolio website (that is madukamalruk.com.lk).
- No JavaScript or interactive content (GitHub's sandbox blocks it).

## 5. Features as built
| ID | Feature | Where | Acceptance criteria |
|----|---------|-------|---------------------|
| F1 | Animated lab hero banner + PCB footer | `scripts/build_banner.py` → `assets/` | Renders animated on the GitHub profile with no JS or external fonts |
| F2 | Typing header (external `readme-typing-svg`) | README | Shows the rotating lines |
| F3 | Sections: About, Stack, Build Log, Results, Telemetry, Contact | README | All render; trace dividers between sections |
| F4 | Self-hosted stats + language cards | `scripts/telemetry.py` → `output` branch | `diagnostics.svg`, `languages.svg` refresh every 3 h |
| F5 | Live project cards for 6 featured repos | `FEATURED` in `telemetry.py` | One `repo-<name>.svg` per Build Log entry |
| F6 | Contribution snake (light/dark) | workflow, `Platane/snk` | Both variants on `output` |
| F7 | Collapsible Mermaid pipeline diagram | README | Renders on GitHub |

## 6. User flows
1. Visitor opens the profile → banner → About → Stack → Build Log cards (link to repos) → Results → Telemetry → Contact.
2. Maintainer edits README / scripts → push to `main` → workflow rebuilds cards into `output`.

## 7. Constraints
- GitHub README sandbox: images only, no JS; SVG animation via CSS/SMIL.
- Public repo: only public, intended personal details.
- Scripts are stdlib-only Python 3.

## 8. Data, auth & security
- Data: public GitHub profile/repo stats only.
- Auth: `GITHUB_TOKEN` in Actions; optional `METRICS_TOKEN` PAT (scopes `repo`, `read:user`) so private repos count in language stats.
- No secrets in the repo (checked 2026-11-18, clean).

## 9. Integrations
- GitHub GraphQL + REST API; `readme-typing-svg.demolab.com`; `streak-stats.demolab.com`; shields.io badges.

## 10. Success metrics
- Profile renders with no broken images; `output` cards are less than 3 h old.

## 11. Known gaps / open questions
- [ ] The committed `madukz-space.svg` differs from the script output by one rect (decision: the committed SVG wins; see plan).
- [ ] Streak stats and typing header still use external demolab services (single point of failure). TBD — question for user: should these be self-hosted later?
- [ ] No automated tests (acceptable for this repo).

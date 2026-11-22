# Product Engineer Skills

Agent skills that measure and improve how people get through your product. They count the clicks on your happy path, turn flows into tests with a UX budget, plan feature adoption, instrument analytics, and design and read A/B tests — working in your real codebase, with Claude Code, Codex, or any agent that reads `SKILL.md`.

> **Formerly `claude-design-system-prompt`.** Claude now handles visual design natively with `/design`, so this repository moved on to what comes after the mockup: getting features used. The previous prompt and skills remain available at the [`v1-design-prompt`](https://github.com/Trystan-SA/product-engineer-skills/tree/v1-design-prompt) tag.

## Install

**Claude Code**

```
/plugin install product-engineer --marketplace Trystan-SA/product-engineer-skills
```

On Claude Code versions older than 2.1.275, add the marketplace first:

```
/plugin marketplace add Trystan-SA/product-engineer-skills
/plugin install product-engineer@product-engineer-skills
```

Skills load on their own when a request matches, or on demand as `/product-engineer:<skill>`. To share it with your team, run `claude plugin marketplace add Trystan-SA/product-engineer-skills --scope project` and commit `.claude/settings.json`.

**Codex**

```bash
codex plugin marketplace add Trystan-SA/product-engineer-skills
codex plugin add product-engineer@product-engineer-skills
```

Or run `/plugins` inside Codex and install it from the list.

**Other agents** (Cursor, OpenCode, Gemini CLI and more) with the open-source [`skills` CLI](https://github.com/vercel-labs/skills):

```bash
npx skills add Trystan-SA/product-engineer-skills
```

## What you can ask

| Ask | Skill | You get |
|---|---|---|
| "We should build bulk invoicing" | `feature-brief` | Problem, job story, one success metric with a target, click budget, kill criteria |
| "How many clicks does it take to send an invoice?" | `happy-path-audit` | Step table traced through the code, click and field counts, KLM time estimate, ranked reductions |
| "What happens if the payment fails here?" | `unhappy-paths` | Error, empty, loading, permission and session states for every step, dead ends fixed |
| "Make sure signup never gets longer" | `flow-test` | Playwright tests that fail when the flow exceeds its click and field budget |
| "Nobody uses the export feature" | `adoption-plan` | Funnel from exposure to retention, entry points mapped to moments of need, diagnosis |
| "Add tracking for the new onboarding" | `instrument-feature` | Tracking plan wired into your existing analytics SDK, verified to fire once |
| "Can we A/B test the new pricing page?" | `ab-test-design` | Hypothesis, metrics, sample size and duration, variant behind your feature flags |
| "Did the test win?" | `experiment-readout` | Validity checks, lift with confidence intervals, a ship / iterate / roll back call |
| "Pull tokens out of our CSS" | `design-system-extract` | Tokens file in your stack's format, with the inconsistencies found |
| "Is our design system actually used?" | `design-system-adoption` | Adoption % per category and area, duplicate components, migration plan with lint ratchet |
| "Check this flow for accessibility" | `accessibility-audit` | WCAG 2.2 AA review with automated and manual passes, fixes in code |
| "Review this PR for UX" | `ux-review` | Before/after flow cost, missing states, accessibility, design-system drift, copy, tracking |

## How the skills work together

Skills that work on a feature share a folder, so each one builds on what the others found:

```
docs/product/<feature>/
├── brief.md            feature-brief         goal, metric, budget
├── flow-audit.md       happy-path-audit      steps, counts, reductions
├── unhappy-paths.md    unhappy-paths         state matrix, fixes
├── adoption-plan.md    adoption-plan         funnel, entry points
├── tracking-plan.md    instrument-feature    events, funnels
└── experiment.md       ab-test-design        spec, then experiment-readout's results
```

A typical feature goes `feature-brief` → `happy-path-audit` → `unhappy-paths` → `flow-test` → `instrument-feature` → `adoption-plan` → `ab-test-design` → `experiment-readout`, with `ux-review` on every PR that touches the UI. Each skill also works on its own. If your project keeps product docs somewhere else, the skills use that location.

## Principles

- **Count, don't guess.** Every number is labeled as measured (from running the app, a test or data), traced (from reading the code) or estimated (with the reason).
- **Work in the real code.** Skills reuse your analytics wrapper, feature-flag tool, E2E framework and design system. They never add a dependency without asking.
- **Outcomes over outputs.** Value moments, not page views; one primary metric decided before the data arrives.
- **Make improvements stick.** Click budgets in CI, lint ratchets for design tokens, pre-registered experiment analyses.

## Repository layout

```
skills/<name>/SKILL.md           one folder per skill (+ scripts/ when a skill bundles code)
.claude-plugin/plugin.json       Claude Code plugin manifest
.claude-plugin/marketplace.json  Claude Code marketplace
plugin.json                      portable manifest, read by Codex
.agents/plugins/marketplace.json Codex marketplace
tools/check_skills.py            portability checks run in CI
tests/                           tests for the bundled scripts
```

## Contributing

Issues and pull requests are welcome, especially real-world cases where a skill gave a wrong count or missed a state. Conventions:

- **Frontmatter** has `name` (equal to the folder name) and `description` only, so skills load in Claude Code, Codex and claude.ai. The description says what the skill does, then "Use when …".
- **Agent-neutral bodies.** No tool names specific to one agent. Where parallel work helps, write "if you can run subagents, run these in parallel; otherwise run them one after another".
- **Bundled scripts** use the Python standard library only and come with tests in `tests/`.
- **Checks.** `python3 tools/check_skills.py`, `python3 -m unittest discover -s tests` and `claude plugin validate . --strict` must pass; CI runs them, then installs the plugin in Codex and checks that every skill is listed.
- **Releases** bump `version` in both `plugin.json` files. Installed copies update only when it changes.

## License

MIT — see [LICENSE](LICENSE).

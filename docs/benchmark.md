# Benchmark: does `agent_help()` context reduce API hallucination?

**Status: not yet run.** This page documents the methodology and the harness
(`scripts/benchmark.py`). No numbers are published until a real run has been
executed and recorded here — claims in the README about hallucination and
token efficiency remain unevidenced until then.

## The question

When a coding agent writes Python against an API it has not seen (a new
library, a recent release, a project-private module), does injecting
`agent_help(target)` output into the prompt reduce failures compared with the
same prompt without it?

The failure modes scored are the two documented in [Why it matters](why.md):

- **What exists** — hallucinated attributes and methods, measured as
  `AttributeError` at runtime.
- **How to use it** — wrong signatures or call shapes, measured as `TypeError`
  at runtime.

## Method

For each task (one target library plus a natural-language coding prompt) and
each condition, the harness asks the model for a single runnable script and
executes it against the installed library:

| Condition | Prompt |
| --- | --- |
| `baseline` | The task prompt only. |
| `agent_help` | The task prompt plus `agent_help(target)` output labeled as reference documentation for the installed version. |

Every generated script runs in a fresh subprocess against the same
environment. Outcomes:

| Outcome | Meaning |
| --- | --- |
| `ok` | Script exits 0. |
| `attributeerror` | Runtime `AttributeError` — most directly indicates a hallucinated API. |
| `typeerror` | Runtime `TypeError` — wrong signature or call shape. |
| `nameerror`, `importerror` | Reference or import failures. |
| `other_error`, `timeout`, `no_code`, `api_error` | Everything else; reported but not counted as API hallucination. |

Headline metric: the `ok` rate per condition, plus the split between
`attributeerror` and `typeerror`. Results are recorded below with the date,
model, sample count, and library versions.

## Running it

The harness calls the Anthropic API (needs `ANTHROPIC_API_KEY` or an
`ant auth login` profile) and requires the target libraries to be installed.
It is deliberately not part of CI.

```bash
uv run --with anthropic --with icalendar --with feedparser \
    python scripts/benchmark.py --samples 5 --out .localonly/benchmark-results.json
```

Custom task sets are JSON files of `{module, target, task}` entries passed via
`--tasks`. Choose targets the model plausibly has weak training coverage of:
small libraries, recent releases, or project-private code — for well-known
stable APIs the model may succeed in both conditions and the benchmark
measures nothing.

## Threats to validity

- **Target familiarity.** A model that already knows a library reduces the
  gap; a model that misremembers a *changed* API may fail both conditions.
  Unfamiliar targets are the population of interest.
- **Task wording.** The injected documentation is the only intended
  difference; prompts are otherwise identical.
- **Execution-only scoring.** A script can exit 0 and still be semantically
  wrong; `ok` is an upper bound on correctness, not a proof of it.
- **Sample size.** Per-task differences at small sample counts are noise;
  read the aggregate.

## Results

_None yet._

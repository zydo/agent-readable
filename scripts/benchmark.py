"""Benchmark: does `agent_help()` context reduce API-hallucination failures?

Compares two conditions on identical code-generation tasks against unfamiliar
libraries:

- ``baseline``: a natural-language task prompt only.
- ``agent_help``: the same prompt with `agent_help(target)` output injected as
  reference documentation.

Each generated script is executed against the installed library and scored by
outcome: clean exit, AttributeError (hallucinated API), TypeError (wrong
signature/usage), other error, timeout, or no code returned.

Not wired into CI: it calls a paid API and needs the target libraries
installed. See docs/benchmark.md for methodology and current status.

Usage:

    uv run --with anthropic --with <target-libraries> \
        python scripts/benchmark.py [--tasks tasks.json] \
        [--samples 3] [--out results.json]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import anthropic

from agent_readable import agent_help

MODEL = "claude-opus-5"
RUN_TIMEOUT_S = 30

BASELINE_PROMPT = """You are writing Python code using the `{module}` library.

Task: {task}

Reply with exactly one Python code block containing a complete, runnable
script. No explanations, no example usage outside the block.
"""

TREATMENT_PROMPT = """You are writing Python code using the `{module}` library.

Reference documentation for `{target}`, generated from the installed version:

{doc}

Task: {task}

Reply with exactly one Python code block containing a complete, runnable
script. No explanations, no example usage outside the block.
"""


@dataclass(frozen=True)
class Task:
    """One code-generation task against one importable target."""

    module: str
    target: str
    task: str


@dataclass
class SampleResult:
    condition: str
    module: str
    sample: int
    outcome: str
    detail: str = ""


# Tasks deliberately favor small, unfamiliar libraries so the model cannot
# answer from training data. Add entries via --tasks <file> with the same
# shape; the listed libraries must be installed in the run environment.
DEFAULT_TASKS = (
    Task(
        module="icalendar",
        target="icalendar:Calendar",
        task="Parse the ICS string 'BEGIN:VCALENDAR\\r\\nEND:VCALENDAR\\r\\n' "
        "and print the calendar's PRODID property (or 'none' if absent).",
    ),
    Task(
        module="feedparser",
        target="feedparser",
        task='Parse the Atom feed string \'<feed xmlns="http://www.w3.org/2005/Atom">'
        "<title>t</title></feed>' and print the feed title.",
    ),
)


def generate(client: anthropic.Anthropic, prompt: str) -> str:
    """Call the model and return its text, or raise RuntimeError on refusal."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError(f"model refused ({response.stop_details})")
    return "".join(block.text for block in response.content if block.type == "text")


def extract_code(response_text: str) -> str | None:
    """Return the first fenced code block, or None when the reply has none."""
    for match in re.finditer(r"```(?:python)?\s*\n(.*?)```", response_text, re.DOTALL):
        return match.group(1)
    return None


def classify(code: str) -> SampleResult:
    """Execute one generated script and classify the outcome."""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:  # noqa: SIM115 - executed before deletion below
        f.write(code)
        path = f.name
    try:
        proc = subprocess.run(
            [sys.executable, path],
            capture_output=True,
            text=True,
            timeout=RUN_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        return SampleResult("", "", 0, "timeout")
    finally:
        Path(path).unlink(missing_ok=True)

    if proc.returncode == 0:
        return SampleResult("", "", 0, "ok")
    stderr_tail = proc.stderr.strip().splitlines()[-1] if proc.stderr else ""
    for exc in ("AttributeError", "TypeError", "ImportError", "NameError"):
        if re.search(rf"\b{exc}\b", stderr_tail):
            return SampleResult("", "", 0, exc.lower(), stderr_tail[:200])
    return SampleResult("", "", 0, "other_error", stderr_tail[:200])


def run_task(
    client: anthropic.Anthropic,
    task: Task,
    samples: int,
    doc: str,
) -> list[SampleResult]:
    """Run one task under both conditions for `samples` repetitions each."""
    results: list[SampleResult] = []
    prompts = {
        "baseline": BASELINE_PROMPT.format(module=task.module, task=task.task),
        "agent_help": TREATMENT_PROMPT.format(
            module=task.module, doc=doc, target=task.target, task=task.task
        ),
    }
    for condition, prompt in prompts.items():
        for i in range(samples):
            result = SampleResult(condition, task.module, i, "no_code")
            try:
                code = extract_code(generate(client, prompt))
                if code:
                    result = classify(code)
            except RuntimeError as exc:
                result = SampleResult(condition, task.module, i, "api_error", str(exc))
            result.condition = condition
            result.module = task.module
            result.sample = i
            results.append(result)
            print(
                f"  {condition:>10} #{i} {task.module}: {result.outcome}"
                f"{' — ' + result.detail if result.detail else ''}",
                file=sys.stderr,
            )
    return results


def summarize(results: list[SampleResult]) -> str:
    """Render the per-condition outcome table."""
    by_condition: dict[str, dict[str, int]] = {}
    for r in results:
        counts = by_condition.setdefault(r.condition, {})
        counts[r.outcome] = counts.get(r.outcome, 0) + 1

    outcomes = sorted({r.outcome for r in results})
    conditions = list(by_condition)
    header = f"{'outcome':<15}" + "".join(f"{c:>12}" for c in conditions)
    rows = [
        f"{outcome:<15}"
        + "".join(f"{by_condition[c].get(outcome, 0):>12}" for c in conditions)
        for outcome in outcomes
    ]
    total = len(results) // max(len(conditions), 1)
    footer = f"{'ok rate':<15}" + "".join(
        f"{by_condition[c].get('ok', 0) / total:>12.0%}" if total else "          0%"
        for c in conditions
    )
    return "\n".join([header, *rows, footer])


def load_tasks(path: str | None) -> tuple[Task, ...]:
    if path is None:
        return DEFAULT_TASKS
    raw: Any = json.loads(Path(path).read_text())
    return tuple(Task(**entry) for entry in raw)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tasks", help="JSON file of {module, target, task} entries")
    parser.add_argument(
        "--samples", type=int, default=3, help="repetitions per condition"
    )
    parser.add_argument("--out", help="write full results JSON here")
    args = parser.parse_args()

    client = anthropic.Anthropic()
    tasks = load_tasks(args.tasks)
    all_results: list[SampleResult] = []
    for task in tasks:
        print(f"== {task.module} ({task.target}) ==", file=sys.stderr)
        doc = agent_help(_import_target(task.target))
        all_results.extend(run_task(client, task, args.samples, doc))

    print(summarize(all_results))
    if args.out:
        payload = json.dumps([asdict(r) for r in all_results], indent=2)
        Path(args.out).write_text(payload)
        print(f"\nFull results written to {args.out}", file=sys.stderr)


def _import_target(dotted: str) -> Any:
    """Resolve a CLI-style target path to a live object."""
    from agent_readable.__main__ import _resolve

    return _resolve(dotted)


if __name__ == "__main__":
    main()

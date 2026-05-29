"""
Example: Duck-typed agent-readable class.

No mixin, no inheritance — just define ``__agent_help__()`` as a classmethod.
The standalone ``agent_help()`` function detects it automatically.

Run this file to see both outputs:
    python examples/duck_type.py
"""

import os

from agent_readable import agent_help


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, max_tokens: int, refill_rate: float): ...

    def acquire(self, _tokens: int = 1) -> bool:
        """Try to acquire tokens. Returns False if rate-limited."""
        return True

    def wait(self, tokens: int = 1) -> None:
        """Block until tokens are available."""

    @classmethod
    def __agent_help__(cls) -> str:
        return (
            "# RateLimiter\n"
            "\n"
            "## Constructor\n"
            "\n"
            "```python\n"
            "RateLimiter(max_tokens: int, refill_rate: float)\n"
            "```\n"
            "\n"
            "## Do\n"
            "\n"
            "- Use `acquire()` for non-blocking checks.\n"
            "- Use `wait()` when you must proceed regardless of rate.\n"
            "- Set `refill_rate` to tokens/second.\n"
            "\n"
            "## Do not\n"
            "\n"
            "- Do not call `acquire()` in a tight loop without sleeping.\n"
            "- Do not assume `acquire()` always returns True.\n"
        )


if __name__ == "__main__":
    print("=== help(RateLimiter) — no usage guidance ===")
    print()
    os.environ["PAGER"] = "cat"
    help(RateLimiter)  # NOSONAR

    print()
    print("=" * 72)
    print()
    print("=== agent_help(RateLimiter) — structured, agent-friendly ===")
    print()
    print(agent_help(RateLimiter))

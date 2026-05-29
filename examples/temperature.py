"""
Example: Designing a class from scratch with AgentReadableMixin.

Shows how __agent_notes__() accumulates through inheritance:
Sensor provides base rules, CalibratedSensor adds calibration-specific rules.

Run this file to see both outputs:
    python examples/temperature.py
"""

import os

from agent_readable import AgentReadableMixin, agent_help


class Sensor(AgentReadableMixin):
    """
    Reads a value from a hardware sensor.

    Agent usage:
        Run ``agent_help(Sensor)`` before using this class in generated code.
    """

    def __init__(self, pin: int, *, unit: str = "C"):
        self.pin = pin
        self.unit = unit

    def read(self) -> float:
        """Read the current sensor value."""
        return 0.0

    def calibrate(self, offset: float):
        """Apply a calibration offset."""
        self._offset = offset

    @classmethod
    def __agent_notes__(cls) -> str:
        return """
## Do

- Call `calibrate()` once during setup, before `read()`.
- Handle negative values — sensors may report below zero.

## Do not

- Do not call `read()` before `calibrate()` on first use.
"""


class CalibratedSensor(Sensor):
    """
    A sensor with factory calibration applied.

    Agent usage:
        Run ``agent_help(CalibratedSensor)`` before using this class in generated code.
    """

    def reset(self):
        """Reset to factory calibration."""

    @classmethod
    def __agent_notes__(cls) -> str:
        return """
## Do

- Call `reset()` if readings drift unexpectedly.

## Do not

- Do not call `calibrate()` — use `reset()` instead. Factory calibration
  is pre-applied and `calibrate()` would double-adjust.
"""


if __name__ == "__main__":
    print("=== help(CalibratedSensor) — verbose, not agent-friendly ===")
    print()
    os.environ["PAGER"] = "cat"
    help(CalibratedSensor)  # NOSONAR

    print()
    print("=" * 72)
    print()
    print("=== agent_help(CalibratedSensor) — notes from both classes ===")
    print()
    print(agent_help(CalibratedSensor))

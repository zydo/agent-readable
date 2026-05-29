from importlib.metadata import version

from ._protocol import AgentReadable, AgentReadableMixin, agent_help

__version__ = version("agent-readable")

__all__ = ["AgentReadable", "AgentReadableMixin", "__version__", "agent_help"]

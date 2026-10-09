from dataclasses import dataclass


@dataclass
class MonitoringState:
    """Hold the user's monitoring preference for the current session."""

    paused: bool = False
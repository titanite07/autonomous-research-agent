"""Core package for research coordination"""

# Lazy imports to avoid circular dependencies
def __getattr__(name):
    if name == "ResearchCoordinator":
        from .coordinator import ResearchCoordinator
        return ResearchCoordinator
    elif name == "ResearchState":
        from .coordinator import ResearchState
        return ResearchState
    elif name == "citation":
        from . import citation
        return citation
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["ResearchCoordinator", "ResearchState", "citation"]

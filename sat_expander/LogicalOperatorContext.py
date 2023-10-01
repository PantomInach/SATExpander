from dataclasses import dataclass
from typing import Dict, TypeVar

T = TypeVar("T")

@dataclass
class LogicalOperatorContext:
    vars: Dict[str, T]

    def expandContext(self, **kwargs) -> "LogicalOperatorContext":
        intersection = set(self.vars.keys()).intersection(set(kwargs.keys()))
        if intersection:
            raise ValueError(f"The arguments to add overlapp with the given arguments. Overlapp: {intersection}")
        return LogicalOperatorContext(vars={**self.vars, **kwargs})

    @staticmethod
    def empty() -> "LogicalOperatorContext":
        return LogicalOperatorContext(vars=dict())

    def getArgument(self, argument: str) -> T:
        item = self.vars.get(argument)
        if item is None:
            raise ValueError(
                f"The argument '{argument}' doesn't exist in the LogicalOperatorContext variables."
            )
        return item

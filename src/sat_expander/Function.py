from src.sat_expander.QuantorContext import QuantorContext

from typing import List, Tuple, Dict, TypeVar, Set, Iterable
from warnings import warn

T = TypeVar('T')  # Type of the arguments for the function


class Function:
    def __init__(self, name: str, arguemts_len: int, domain: Iterable[T], start_variable: int):
        domain = tuple(domain)
        self.was_evaluated: bool = False
        self.name: str = name
        self.arguments_len: int = arguemts_len
        self.domain: Set[T] = set(domain)
        if len(self.domain) != len(domain):
            duplicates = []
            uniques = []
            for x in domain:
                if x not in uniques:
                    uniques.append(x)
                else:
                    duplicates.append(x)
            warn(
                f"The domain of function '{name}' contains duplicate values. Duplicates: {duplicates}")

        try:
            self.relation: Dict[T, int] = {
                tuple(x): i
                for i, x in enumerate(self.domain, start=start_variable)
            }
        except TypeError as te:
            raise RuntimeError(
                "The single values in the domain of a function must be iterable.", str(te))
        self.range: Tuple[int, int] = (
            start_variable, start_variable - 1 + len(domain)
        )

    def in_range(self, value: int | None) -> bool:
        if value is None:
            return False
        return self.range[0] <= value <= self.range[1]

    def evaluate(self, arguments: Tuple[str, ...], context: QuantorContext) -> int:
        args: List[T] = []
        for arg in arguments:
            arg_value = context.getArgument(arg)
            args.append(arg_value)
        args = tuple(args)
        if args not in self.domain:
            raise ValueError(
                f"The input '{args}' of arguments '{arguments}' is not in the domain of function '{self.name}'."
            )
        self.was_evaluated = True
        return self.relation[args]

    def set_equivalent(self, t1: T, t2: T):
        if self.was_evaluated:
            raise RuntimeError(
                "Changing variables after evaluating function can lead to invalid results.")
        if self.relation.get(t1) and self.relation.get(t2):
            self.relation[t2] = self.relation[t1]

    def set_commutative(self):
        """
        Makes the input to the function communitive. E.g. f(x,y) = f(y,x)
        """
        if self.was_evaluated:
            raise RuntimeError(
                "Changing variables after evaluating function can lead to invalid results.")
        remains: List[T] = list(self.domain)
        while remains:
            t = remains.pop(0)
            exclude = (
                x for x in remains if self._tuple_contain_same_elements(x, t))
            for x in exclude:
                self.relation[x] = self.relation[t]
                remains.remove(x)

    @staticmethod
    def _tuple_contain_same_elements(t1: Tuple[T], t2: Tuple[T]) -> bool:
        if len(t1) != len(t2):
            return False
        for x in t1:
            if x not in t2:
                return False
        return True

    @staticmethod
    def to_tuple_iter(iter: Iterable[T]) -> Iterable[Tuple[T]]:
        return map(lambda x: (x, ), iter)


class Constant(Function):
    def __init__(self, name: str, start_variable: int):
        self.was_evaluated: bool = False
        self.name: str = name
        self.arguments_len: int = 0
        self.domain: Set[T] = set()
        self.relation: Dict[T, int] = {(): start_variable}
        self.range: Tuple[int, int] = (start_variable, start_variable + 1)
        self.value = start_variable

    def evaluate(self, *args) -> int:
        return self.value

    def set_equivalent(self, *args):
        warn(
            f"Calling 'set_equivalent' on the Constant '{self.name}' has no effect."
        )
        pass

    def set_commutative(self):
        warn(
            f"Calling 'set_commutative' on the Constant '{self.name}' has no effect."
        )
        pass


class FunctionFactory:
    def __init__(self):
        self.variable_counter = 1
        self.functions: List[Function] = []

    def _assert_unique_name(self, name: str):
        if name in map(lambda f: f.name, self.functions):
            raise ValueError(
                f"The function with the name '{name}' is already defined."
            )

    def build(self, name: str, arguments_len: int, domain: Iterable[T]) -> Function:
        self._assert_unique_name(name)
        func = Function(name, arguments_len, domain, self.variable_counter)
        self.variable_counter += func.range[1] - func.range[0] + 1
        self.functions.append(func)
        return func

    def add_constant(self, name: str) -> Constant:
        self._assert_unique_name(name)
        const = Constant(name, self.variable_counter)
        self.functions.append(const)
        self.variable_counter += 1
        return const

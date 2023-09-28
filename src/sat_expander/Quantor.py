from src.sat_expander.Function import Function, FunctionFactory
from src.sat_expander.QuantorContext import QuantorContext

from enum import Enum
from typing import Dict, Tuple, Iterable, TypeVar, List, Optional

T = TypeVar('T')  # Type of the arguments for the function
OptionQuantor = Optional["Quantor"]
CNFLine = Tuple[int, ...]
CNF = Tuple[CNFLine, ...]


class QuantorType(Enum):
    ALL = 0
    EXISTS = 1
    EXPRESSION = 2


class Quantor():
    def __init__(self, type: QuantorType, variables: Tuple[str, ...], values: Iterable, subquantor: OptionQuantor = None):
        self.quantor_type: QuantorType = type
        self.variables: None | Tuple[str] = variables
        self.values: None | Tuple = None if values is None else tuple(values)
        self.subquantor: None | Quantor = subquantor

    def evaluate(self, context: QuantorContext):
        raise NotImplementedError(
            "Evaluate will not be implemented for base class.")

    def add_subquantor(self, subquantor: "Quantor") -> "Quantor":
        if self.quantor_type == QuantorType.EXISTS and subquantor.quantor_type == QuantorType.ALL:
            raise RuntimeError(
                "Can't put an All Quantor after an Exists Quantor. Not a valid CNF.")
        self.subquantor = subquantor
        return self

    def chain(self, subquantor: "Quantor") -> "Quantor":
        if self.subquantor is None:
            self.add_subquantor(subquantor)
        elif self.subquantor.quantor_type == QuantorType.EXPRESSION:
            raise RuntimeError("Can't chain a quantor to a static expression.")
        else:
            self.subquantor.chain(subquantor)
        return self


class AllQuantor(Quantor):
    def __init__(self, variables: Tuple[str, ...], it: Iterable):
        """
        For all variables in it ...
        """
        super().__init__(QuantorType.ALL, variables, it)

    def evaluate(self, context: QuantorContext | None = None) -> CNF:
        if context is None:
            context = QuantorContext.empty()
        res: List[Tuple[int]] = []
        for values in self.values:
            try:
                len(values)
            except TypeError as te:
                raise RuntimeError(
                    f"The values '{values}' are not iterable. Consider using 'Function.to_tuple_iter(domain)' as the domain in the definition of the AllQantor."
                )
            if len(values) != len(self.variables):
                raise RuntimeError(
                    f"The length of values '{values}' for the variables '{self.variables}' don't have a matching length."
                )
            current_context = context.expandContext(
                **dict(zip(self.variables, values))
            )
            res.extend(self.subquantor.evaluate(current_context))
        return tuple(res)


class ExistsQuantor(Quantor):
    def __init__(self, variables: Tuple[str, ...], it: Iterable):
        """
        There exists a variable in it ...
        """
        super().__init__(QuantorType.EXISTS, variables, it)

    def evaluate(self, context: QuantorContext | None = None) -> CNF:
        if context is None:
            context = QuantorContext.empty()
        res: List[int] = []
        for values in self.values:
            if len(values) != len(self.variables):
                raise RuntimeError(
                    f"The length of values '{values}' for the variables '{self.variables}' don't have a matching length."
                )
            current_context = context.expandContext(
                **dict(zip(self.variables, values))
            )
            previous_cnf: CNF = self.subquantor.evaluate(current_context)
            if len(previous_cnf) != 1:
                raise RuntimeError(
                    "Exists quantor can only evaluate CNFs containing one line. Passed CNF:", previous_cnf)
            res.extend(previous_cnf[0])
        return (tuple(res), )


class ExpressionQuantor(Quantor):
    def __init__(self, functions: Tuple[Function, ...] | FunctionFactory, expressions: Iterable[str]):
        """
        Keyword arguments:
        expressions -- contains function calls with the arguments in the form
            of 'f(x,y)'. Here 'f' is the function name and 'x', 'y' the
            arguments which will be substitued from the QuantorContex.
        """
        self.functions: Tuple[Function] = tuple(functions) if not isinstance(
            functions, FunctionFactory) else tuple(functions.functions)
        self.expressions: Dict[Function, Tuple[str, ...], int] = tuple(map(
            lambda exp: self.parse_expression2(exp),
            expressions
        ))
        super().__init__(QuantorType.EXPRESSION, None, None)

    def add_subquantor(self, subquantor: Quantor) -> Quantor:
        raise NotImplementedError(
            "Operation 'addSubquantor' not supported for expression quantor.")

    def evaluate(self, context: QuantorContext) -> CNF:
        return (tuple(
            exp[2] * exp[0].evaluate(exp[1], context)
            for exp in self.expressions
        ),)

    def parse_expression(self, expression: str) -> Tuple[Function, Tuple[str, ...], int]:
        sign = 1
        expression = expression.replace(" ", "")
        if not expression.endswith(')') or '(' not in expression or ')' in expression[:-1]:
            raise ValueError(
                f"Can't parse expression '{expression}'. It needs to follow the form 'f(x,y)'")
        func_name, arguments, *overflow = expression.split('(')
        if overflow:
            raise ValueError(
                f"Can't parse expression '{expression}'. It needs to follow the form 'f(x,y)'")
        args: Tuple[str] = tuple(arguments[:-1].split(","))
        if func_name.startswith("-"):
            func_name = func_name[1:]
            sign = -1
        func = next((x for x in self.functions if x.name == func_name), None)
        if func is None:
            raise ValueError(
                f"The function '{func_name}' from expression '{expression}' is not given to the ExpressionQuantor.")
        if func.arguments_len != len(args):
            raise ValueError(
                f"The function '{func_name}' needs '{func.arguments_len}' arguments but {len(args)} arguments were given from expression '{expression}'.")
        return (func, args, sign)
        # )

    def parse_expression2(self, expression: str) -> Tuple[Function, Tuple[str, ...], int]:
        sign = 1
        expression = expression.replace(" ", "")
        if ('(' in expression) ^ (')' in expression):
            raise ValueError(
                f"Can't parse expression '{expression}'. It needs to follow the form 'f(x,y)' or 'x'.")
        if ")" in expression and not expression.endswith(")"):
            raise ValueError(
                f"Can't parse expression '{expression}'. It needs to follow the form 'f(x,y)' or 'x'.")
        if "(" in expression:
            if expression.index("(") > expression.index(")"):
                raise ValueError(
                    f"Can't parse expression '{expression}'. It needs to follow the form 'f(x,y)' or 'x'.")
        if len(tuple(s for s in expression if s == "(")) > 1 or len(tuple(s for s in expression if s == ")")) > 1:
            raise ValueError(
                f"Can't parse expression '{expression}'. It needs to follow the form 'f(x,y)' or 'x'.")
        if "(" not in expression:
            func_name, arguments, *overflow = expression, None, *[]
        else:
            func_name, arguments, *overflow = expression.split('(')
        if overflow:
            raise ValueError(
                f"Can't parse expression '{expression}'. It needs to follow the form 'f(x,y)'.")
        args: Tuple[str] = () if arguments is None else tuple(arguments[:-1].split(","))
        if func_name.startswith("-"):
            func_name = func_name[1:]
            sign = -1
        func = next((x for x in self.functions if x.name == func_name), None)
        if func is None:
            raise ValueError(
                f"The function '{func_name}' from expression '{expression}' is not given to the ExpressionQuantor.")
        if func.arguments_len != len(args):
            raise ValueError(
                f"The function '{func_name}' needs '{func.arguments_len}' arguments but {len(args)} arguments were given from expression '{expression}'.")
        return (func, args, sign)
        # ))

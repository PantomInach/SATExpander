from sat_expander.Functions import Function, FunctionFactory
from sat_expander.LogicalOperatorContext import LogicalOperatorContext
from sat_expander.ExclusionPredicates import ExclusionPredicate
from sat_expander.CNF import CNF

from enum import Enum
from typing import Dict, Tuple, Iterable, TypeVar, List, Optional

T = TypeVar("T")  # Type of the arguments for the function
OptionLogicalOperator = Optional["LogicalOperator"]


class LogicalOperatorType(Enum):
    ALL = 0
    EXISTS = 1
    EXPRESSION = 2


class LogicalOperator:
    def __init__(
        self,
        type: LogicalOperatorType,
        variables: Tuple[str, ...],
        values: Iterable,
        suboperator: OptionLogicalOperator = None,
        exclude_predicate: ExclusionPredicate | None = None,
    ):
        """
        Keyword arguments:
        exclude_predicate -- Depending on the current context given by the
            'LogicalOperatorContext' and value to be considered the predicate
            should decide if the value should be used in the CNF.
        """
        self.operator_type: LogicalOperatorType = type
        self.variables: None | Tuple[str, ...] = variables
        self.values: Tuple = tuple(values)
        self.suboperator: None | LogicalOperator = suboperator
        self.exclude_predicate: ExclusionPredicate | None = exclude_predicate

    def evaluate(
        self,
        context: LogicalOperatorContext,
    ):
        raise NotImplementedError("Evaluate will not be implemented for base class.")

    def add_suboperator(self, suboperator: "LogicalOperator") -> "LogicalOperator":
        if (
            self.operator_type == LogicalOperatorType.EXISTS
            and suboperator.operator_type == LogicalOperatorType.ALL
        ):
            raise RuntimeError(
                "Can't put an And LogicalOperator after an Or LogicalOperator. Not a valid CNF."
            )
        self.suboperator = suboperator
        return self

    def chain(self, suboperator: "LogicalOperator") -> "LogicalOperator":
        if self.suboperator is None:
            self.add_suboperator(suboperator)
        elif self.suboperator.operator_type == LogicalOperatorType.EXPRESSION:
            raise RuntimeError("Can't chain a operator to a static expression.")
        else:
            self.suboperator.chain(suboperator)
        return self


class AndOperator(LogicalOperator):
    def __init__(
        self,
        variables: Tuple[str, ...],
        it: Iterable,
        exclude_predicate: ExclusionPredicate | None = None,
    ):
        """
        For all variables in it ...
        """
        super().__init__(
            LogicalOperatorType.ALL, variables, it, exclude_predicate=exclude_predicate
        )

    def evaluate(
        self,
        context: LogicalOperatorContext | None = None,
    ) -> CNF:
        if context is None:
            context = LogicalOperatorContext.empty()
        res: List[Tuple[int]] = []
        for values in self.values:
            try:
                len(values)
            except TypeError:
                raise RuntimeError(
                    f"The values '{values}' are not iterable. Consider using 'Function.to_tuple_iter(domain)' as the domain in the definition of the AllQantor."
                )
            if len(values) != len(self.variables):
                raise RuntimeError(
                    f"The length of values '{values}' for the variables '{self.variables}' don't have a matching length."
                )
            current_context = context.expandContext(**dict(zip(self.variables, values)))
            if self.exclude_predicate is not None and not self.exclude_predicate(
                current_context, values
            ):
                continue
            res.extend(self.suboperator.evaluate(current_context))
        return tuple(res)


class OrOperator(LogicalOperator):
    def __init__(
        self,
        variables: Tuple[str, ...],
        it: Iterable,
        exclusion_predicate: ExclusionPredicate | None = None,
    ):
        """
        There exists a variable in it ...
        """
        super().__init__(
            LogicalOperatorType.EXISTS,
            variables,
            it,
            exclude_predicate=exclusion_predicate,
        )

    def evaluate(
        self,
        context: LogicalOperatorContext | None = None,
    ) -> CNF:
        if context is None:
            context = LogicalOperatorContext.empty()
        res: List[int] = []
        for values in self.values:
            if len(values) != len(self.variables):
                raise RuntimeError(
                    f"The length of values '{values}' for the variables '{self.variables}' don't have a matching length."
                )
            current_context = context.expandContext(**dict(zip(self.variables, values)))
            if self.exclude_predicate is not None and not self.exclude_predicate(
                current_context, values
            ):
                continue
            previous_cnf: CNF = self.suboperator.evaluate(current_context)
            if len(previous_cnf) != 1:
                raise RuntimeError(
                    "Or Opeator  can only evaluate CNFs containing one line. Passed CNF:",
                    previous_cnf,
                )
            res.extend(previous_cnf[0])
        return (tuple(res),)


class ExpressionOperator(LogicalOperator):
    def __init__(
        self,
        functions: Tuple[Function, ...] | FunctionFactory,
        expressions: Iterable[str],
    ):
        """
        Keyword arguments:
        expressions -- contains function calls with the arguments in the form
            of 'f(x,y)'. Here 'f' is the function name and 'x', 'y' the
            arguments which will be substitued from the LogicalOperatorContext.
        """
        self.functions: Tuple[Function] = (
            tuple(functions)
            if not isinstance(functions, FunctionFactory)
            else tuple(functions.functions)
        )
        self.expressions: Dict[Function, Tuple[str, ...], int] = tuple(
            map(lambda exp: self.parse_expression(exp), expressions)
        )
        super().__init__(
            LogicalOperatorType.EXPRESSION, None, (), exclude_predicate=None
        )

    def add_suboperator(self, suboperator: LogicalOperator) -> LogicalOperator:
        raise NotImplementedError(
            "Operation 'add_suboperator' not supported for expression operator."
        )

    def evaluate(
        self,
        context: LogicalOperatorContext,
    ) -> CNF:
        return (
            tuple(
                exp[2] * exp[0].evaluate(exp[1], context) for exp in self.expressions
            ),
        )

    def parse_expression(
        self, expression: str
    ) -> Tuple[Function, Tuple[str, ...], int]:
        sign = 1
        expression = expression.replace(" ", "")
        if ("(" in expression) ^ (")" in expression):
            raise ValueError(
                f"Can't parse expression '{expression}'. It needs to follow the form 'f(x,y)' or 'x'."
            )
        if ")" in expression and not expression.endswith(")"):
            raise ValueError(
                f"Can't parse expression '{expression}'. It needs to follow the form 'f(x,y)' or 'x'."
            )
        if "(" in expression:
            if expression.index("(") > expression.index(")"):
                raise ValueError(
                    f"Can't parse expression '{expression}'. It needs to follow the form 'f(x,y)' or 'x'."
                )
        if (
            len(tuple(s for s in expression if s == "(")) > 1
            or len(tuple(s for s in expression if s == ")")) > 1
        ):
            raise ValueError(
                f"Can't parse expression '{expression}'. It needs to follow the form 'f(x,y)' or 'x'."
            )
        if "(" not in expression:
            func_name, arguments, *overflow = expression, None, *[]
        else:
            func_name, arguments, *overflow = expression.split("(")
        if overflow:
            raise ValueError(
                f"Can't parse expression '{expression}'. It needs to follow the form 'f(x,y)'."
            )
        args: Tuple[str] = () if arguments is None else tuple(arguments[:-1].split(","))
        if func_name.startswith("-"):
            func_name = func_name[1:]
            sign = -1
        func = next((x for x in self.functions if x.name == func_name), None)
        if func is None:
            raise ValueError(
                f"The function '{func_name}' from expression '{expression}' is not given to the ExpressionOpeator."
            )
        if func.arguments_len != len(args):
            raise ValueError(
                f"The function '{func_name}' needs '{func.arguments_len}' arguments but {len(args)} arguments were given from expression '{expression}'."
            )
        return (func, args, sign)
        # ))

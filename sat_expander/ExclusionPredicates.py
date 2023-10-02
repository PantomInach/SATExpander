from sat_expander.LogicalOperatorContext import LogicalOperatorContext

from warnings import warn
from typing import Callable, Tuple
from enum import Enum

ExclusionPredicate = Callable[[LogicalOperatorContext, Tuple], bool]


class VarNotFoundResponse(Enum):
    ERROR = 0
    WARN = 1
    IGNORE = 2


def check_variables_in_context(*vars: Tuple[str], var_not_found_response: VarNotFoundResponse = VarNotFoundResponse.WARN):
    def decorator(predicate):
        def wrappe(context: LogicalOperatorContext, *args):
            if _handle_vars_not_found(context, *vars, var_not_found_response=var_not_found_response):
                return True
            return predicate(context, *args)
        return wrappe
    return decorator


def _handle_vars_not_found(
    context: LogicalOperatorContext,
    *vars: str,
    var_not_found_response: VarNotFoundResponse
) -> bool:
    vars_not_found = tuple(
        var
        for var in vars
        if var not in context.vars.keys()
    )
    if vars_not_found:
        match var_not_found_response:
            case VarNotFoundResponse.WARN:
                warn(
                    f"Variable '{vars_not_found}' is not in the context '{context.vars}'. Returning 'True'."
                )
            case VarNotFoundResponse.ERROR:
                raise RuntimeError(
                    f"Variable '{vars_not_found}' is not in the context '{context.vars}'. Returning 'True'."
                )
            case _:
                pass
        return True
    return False

def exclude_variable(
    var: str,
    var_not_found_response: VarNotFoundResponse = VarNotFoundResponse.WARN
) -> ExclusionPredicate:
    """
    Generates exclusion predicate for excluding values which match a certain
    variable in the context. For example,
    And[x in V] Or[y in V\\{x}] ...
    """
    @check_variables_in_context(var, var_not_found_response=var_not_found_response)
    def predicate(context: LogicalOperatorContext, value: Tuple) -> bool:
        if value == (context.vars[var], ):
            return False
        return True
    return predicate


def exclude_var_tuple(
    *vars: Tuple[str, ...],
    var_not_found_response: VarNotFoundResponse = VarNotFoundResponse.WARN
) -> ExclusionPredicate:
    """
    Generates exlusion predicate for a tuple of variables.
    For example,
    And[x in V] And[y in U] Or[z in VxU \\ {(x, y)}] ...
    """
    @check_variables_in_context(*vars, var_not_found_response=var_not_found_response)
    def predicate(context: LogicalOperatorContext, value: Tuple) -> bool:
        return value != tuple(context.vars[var] for var in vars)
    return predicate

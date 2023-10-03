from sat_expander.LogicalOperator import AndOperator, OrOperator
from sat_expander.LogicalOperator import ExpressionOperator
from sat_expander.Functions import FunctionFactory, to_tuple_iter
from sat_expander.ExclusionPredicates import check_variables_in_context
from sat_expander.CNF import cnf_to_dimacs
from itertools import product

A = tuple(range(4))
V = tuple(range(1, 5))
U = tuple(range(1, 7, 2))
B = product(V, U)
C = ("also", "valid", "function", "input")

factory = FunctionFactory()
factory.build("s", arguments_len=2, domain=product(A, C))  # Build function s
# Build function r
factory.build("r", arguments_len=1, domain=to_tuple_iter(V))
factory.build("w", 2, product(U, C))  # Build function w
factory.add_constant("t")  # Build constant t

assert tuple(to_tuple_iter(range(1, 4))) == ((1, ), (2, ), (3, ))

expression = ExpressionOperator(factory, ("s(x,y)", "r(u)", "w(v, y)", "t"))

and_op1 = AndOperator(("x", ), to_tuple_iter(A))
and_op2 = AndOperator(("u", "v"), B)


"""
Predicate to exclude all variables which are equal to the value of 'x'.
'sat_expander.ExclusionPredicates.check_variables_in_context' ensures that the
variable 'x' is in the context.
"""


@check_variables_in_context("x")
def predicate(context, value):
    return value != context.vars["x"]


or_op = OrOperator(("y", ), to_tuple_iter(C), exclusion_predicate=predicate)

and_op1.chain(and_op2).chain(or_op).chain(expression)
cnf = and_op1.evaluate()

print(cnf_to_dimacs(cnf))

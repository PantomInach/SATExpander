# SATExpander
When working with complex SAT formulations, one formulates them often in with big 'AND' and 'OR' clauses, which are variable dependent. This program provides an easy way to transform these formulations into 'cnf' files, which are supported by most SAT solvers.

## Installation
Clone the repository with `git clone https://github.com/PantomInach/SATExpander.git` and install it with `pip install ./SatExpander`.

## How To
To build a CNF for a SAT formulation, we define its building blocks with `AllOperator`, `OrOperator` and `ExpresseionOperator`.
We will show you how to use this tool to encode the following CNF.
$$\bigwedge_{x \in A} \quad \bigwedge_{(u, v) \in B} \quad \bigvee_{y \in C \setminus \{x\}} s_{x,y} \vee r_{u} \vee w_{v, y} \vee t $$
Here are $A, C$ some sets of individual arguments and $B = V \times U$ is a set containing a tuple of to arguments.

### Function
Functions describe the building blocks of literals.
These can be constants such as `t` or functions such as `s_{x,y}`.
Each function assigns for every value in the domain a unique integer in the SAT formulation.
Constants are just special cases of functions taking in no arguments.

We can describe the functions `s_{x,y}, r_u, w_{v,x}` with the code in the following way.
```python
from sat_expander.Functions import FunctionFactory, to_tuple_iter
from itertools import product

A = tuple(range(4))
V = tuple(range(1, 5))
U = tuple(range(1, 7, 2))
B = product(V, U)
C = ("also", "valid", "function", "input")

factory = FunctionFactory()
factory.build("s", arguments_len=2, domain=product(A, C))  # Build function s
factory.build("r", arguments_len=1, domain=to_tuple_iter(V))  # Build function r
factory.build("w", 2, product(U, C))  # Build function w
factory.add_constant("t")  # Build constant t
```
**Note** that when specifying domains consisting of non-iterable values they need to be enclosed in an iterable format.
For this purpose use the provided function `sat_expander.Functions.to_tuple_iter`.
```python
from sat_expander.Functions import to_tuple_iter
assert tuple(to_tuple_iter(range(1, 4))) == ((1, ), (2, ), (3, ))
```

### Expression Operator
An `ExpressionOperator` describes the part of the SAT formulation that contains all literals. Every part of the expression must be provided as a separate string and all must be packed in a tuple or iterable package.
```python
from sat_expander.LogicalOperator import ExpressionOperator
expression = ExpressionOperator(factory, ("s(x, y)", "r(u)", "w(v, y)", "t"))
```
Every formulation can only have on `ExpressionOperator` and is also ended by it.

### And and Or Operator
The `AndOperator` and `OrOperator` lets us model the And and Or operator. As an input the variables provided as a tuple of strings and a set of values must be provided. 
```python
from sat_expander.LogicalOperator import AndOperator
and_op1 = AndOperator(("x", ), A)
and_op2 = AndOperator(("u", "v"), B)
```
Every operator takes the values of the given set and assigns its values to the variables. The current assignment of values is passed in a `sat_expander.LogicalOperatorContext.LogicalOperatorContext` in a dict to the next operator to be evaluated. All elements of the given set are iterated and the resulting lines of the CNF are collected.

For the last OR operator, we need to exclude the value `x` given by the context from the set `C`. We can give the `OrOperator` a predicate for excluding values.
```python
from sat_expander.LogicalOperator import OrOperator
from sat_expander.ExclusionPredicates import check_variables_in_context

@check_variables_in_context("x")
def predicate(context, value):
    return value != context.vars["x"]

or_op = OrOperator(("y", ), to_tuple_iter(C), exclusion_predicate=predicate)
```
A builder for this predicate is provided via `sat_expander.ExclusionPredicates.exclude_variable`.

Predicates can use all variables in the context given by the operator before and variables introduced in the current operator. The `AndOperator` can also use a `exclusion_predicate`. When constructing an own predicate, it is recommended to always use the `check_variables_in_context` decorator.

### Chaining and Evaluation
At last, we need to chain the introduced operator. Take the first operator and chain the following operator like below.
```python
and_op1.chain(and_op2).chain(or_op).chain(expression)
cnf = and_op1.evaluate()
```
You can't chain any operator onto an `ExpressionOperator` and after an `OrOperator` only `OrOperator` and `ExpressionOperator` can be chained. Any operator can follow an `AndOperator`. This ensures that the resulting SAT formulation is in a conjunctive normal form (CNF).

The `evaluate` function generates the CNF represented by a tuple of tuple of integers. Each interger represents a variable. If an integer is negative, then the variable is negated. Each line of the CNF is a tuple of integers representing the variables.

### Converting to DIMACS
Most SAT solver take an file in [DIMACS format](https://ifm97.github.io/assignments/SAT-solver.pdf) as input. With the `sat_expander.CNF.cnf_to_dimacs` function the CNF of `cnf = and_op1.evaluate()` can be converted to a string satisfying the DIMACS format.
```python
from sat_expander.CNF import cnf_to_dimacs
with open("output.cnf", "w") as f:
    f.write(cnf_to_dimacs(cnf))
```
This would store the CNF in the DIMACS format as the file `output.cnf`.

### Joining CNFs
If your CNF is more complex and consists of more separated parts, then use the same `FunctionFactory`. Then the CNFs can be joined with the `sat_expander.CNF.join_cnfs` function.
```python
from sat_expander.CNF import join_cnfs
cnf1 = ...
cnf2 = ...
join_cnfs(cnf1, cnf2)
```
This function simply calls the `+` operator for tuple. The following code is equivalent.
```python
cnf1 = ...
cnf2 = ...
cnf1 + cnf2
```

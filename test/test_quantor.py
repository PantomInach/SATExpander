from src.sat_expander.LogicalOperatorContext import LogicalOperatorContext
from src.sat_expander.LogicalOperator import ExpressionOperator, LogicalOperator, AndOperator, OrOperator, LogicalOperatorType
from src.sat_expander.Functions import Function

from typing import Tuple

import unittest


class TestOperatorContext(unittest.TestCase):
    def test_operator_context_expand(self):
        context = LogicalOperatorContext(dict())
        context2 = context.expandContext(a=1)
        context3 = context2.expandContext(b=2, c=2)
        self.assertEqual(context.vars, dict())
        self.assertEqual(context2.vars, {"a": 1})
        self.assertEqual(context3.vars, {"a": 1, "b": 2, "c": 2})
        self.assertEqual(LogicalOperatorContext.empty().vars, dict())
        with self.assertRaises(ValueError) as _:
            context3.expandContext(a=1)

    def test_operator_context_get(self):
        context = LogicalOperatorContext({"a": 1})
        self.assertEqual(context.getArgument("a"), 1)
        context = LogicalOperatorContext({"a": (1, 2, 3)})
        self.assertEqual(context.getArgument("a"), (1, 2, 3))
        context = LogicalOperatorContext({"abc": 1})
        self.assertEqual(context.getArgument("abc"), 1)
        with self.assertRaises(ValueError) as _:
            context.getArgument("Something")


class TestExpressionOperator(unittest.TestCase):
    def test_expression_operator_parse(self):
        functions = list(
            map(lambda i: DummyFunction(f"func{i}", i), range(1, 4))
        )
        functions.append(DummyFunction("f", 0))
        functions = tuple(functions)
        expressions = ("  func1(  a)", "func2   (b,c)", " func3(d,e,    f  )  ")
        expr_operator = ExpressionOperator(functions, expressions)
        self.assertEqual(expr_operator.expressions, (
            (functions[0], ("a",), 1),
            (functions[1], ("b", "c"), 1),
            (functions[2], ("d", "e", "f"), 1)
        ))
        expressions = ("  func1(  a)", "func2   (b,b)")
        expr_operator = ExpressionOperator(functions, expressions)
        self.assertEqual(expr_operator.expressions, (
            (functions[0], ("a",), 1),
            (functions[1], ("b", "b"), 1),
        ))
        expressions = ("-func1(a)", )
        expr_operator = ExpressionOperator(functions, expressions)
        self.assertEqual(expr_operator.expressions, (
            (functions[0], ("a",), -1),
        ))
        expressions = ("-func1(a)", )
        expr_operator = ExpressionOperator(functions, expressions)
        self.assertEqual(expr_operator.expressions, (
            (functions[0], ("a",), -1),
        ))
        expressions = ("f", )
        expr_operator = ExpressionOperator(functions, expressions)
        self.assertEqual(expr_operator.expressions, (
            (functions[-1], (), 1),
        ))
        expressions = (" -  f ", )
        expr_operator = ExpressionOperator(functions, expressions)
        self.assertEqual(expr_operator.expressions, (
            (functions[-1], (), -1),
        ))

        expressions = (
            "  func1(  a)a", "func2   (b,c)", "func3(d,e,    f  )  "
        )
        with self.assertRaises(ValueError) as _:
            ExpressionOperator(functions, expressions)
        expressions = (
            "  func1(  a)", "func2   b,c)", "func3(d,e,    f  )  "
        )
        with self.assertRaises(ValueError) as _:
            ExpressionOperator(functions, expressions)
        expressions = (
            "  func1(  a)", "func2   (b,c)", "func3(d,e),    f  )  "
        )
        with self.assertRaises(ValueError) as _:
            ExpressionOperator(functions, expressions)
        expressions = (
            "  func1(  a()", "func2   (b,c)", "func3(d,e,    f  )  "
        )
        with self.assertRaises(ValueError) as _:
            ExpressionOperator(functions, expressions)
        expressions = (
            "  func9(  a)", "func2   (b,c)", "func3(d,e,    f  )  "
        )
        with self.assertRaises(ValueError) as _:
            ExpressionOperator(functions, expressions)
        expressions = (
            "  func(  a, a)", "func2   (b,c)", "func3(d,e,    f  )  "
        )
        with self.assertRaises(ValueError) as _:
            ExpressionOperator(functions, expressions)
        # )

    def test_expression_operator_addSuboperator(self):
        functions = (DummyFunction("func1", 1),)
        expressions = ("func1(a)", )
        expr_quant = ExpressionOperator(functions, expressions)
        with self.assertRaises(NotImplementedError) as _:
            expr_quant.add_suboperator(None)

    def test_expression_operator_evaluate(self):
        expression_operator = DummyExpressionOperator(3, 0)
        self.assertEqual(
            expression_operator.evaluate(None),
            (("1|1", "2|1|2", "3|1|2|3"), )
        )

        expression_operator = DummyExpressionOperator(0, 2)
        self.assertEqual(expression_operator.evaluate(None), (("1|", "2|"),))

        expression_operator = DummyExpressionOperator(1, 1)
        self.assertEqual(expression_operator.evaluate(None), (("1|1", "2|"),))


class TestExistsOperator(unittest.TestCase):
    def test_or_operator_evaluate(self):
        values = ((0, 0), (0, 1), (1, 0), (1, 1))
        context = LogicalOperatorContext({"c": 1, "d": 2, "e": 3})
        expression = DummySimpleOperatorEvaluation()
        exists = OrOperator(("a", "b"), values)
        exists.add_suboperator(expression)
        out = exists.evaluate(context)
        expected_res = ((
            "c" + ": " + str(1),
            "d" + ": " + str(2),
            "e" + ": " + str(3),
            "a" + ": " + str(0),
            "b" + ": " + str(0),

            "c" + ": " + str(1),
            "d" + ": " + str(2),
            "e" + ": " + str(3),
            "a" + ": " + str(0),
            "b" + ": " + str(1),

            "c" + ": " + str(1),
            "d" + ": " + str(2),
            "e" + ": " + str(3),
            "a" + ": " + str(1),
            "b" + ": " + str(0),

            "c" + ": " + str(1),
            "d" + ": " + str(2),
            "e" + ": " + str(3),
            "a" + ": " + str(1),
            "b" + ": " + str(1),
        ), )
        self.assertEqual(out, expected_res)

        values = ((0, 0), )
        context = LogicalOperatorContext(dict())
        expression = DummySimpleOperatorEvaluation()
        exists = OrOperator(("a", ), values)
        exists.add_suboperator(expression)
        with self.assertRaises(RuntimeError) as _:
            exists.evaluate(context)

        values = ((0, ), )
        context = LogicalOperatorContext(dict())
        expression = DummyFixedOperatorEvaluation(((1,), (1,)))
        exists = OrOperator(("a", ), values)
        exists.add_suboperator(expression)
        with self.assertRaises(RuntimeError) as _:
            exists.evaluate(context)


class TestAllOperator(unittest.TestCase):
    def test_and_operator_evaluate(self):
        values = ((0, 0), (0, 1), (1, 0), (1, 1))
        context = LogicalOperatorContext({"c": 1})
        expression = DummySimpleOperatorEvaluation()
        and_operator = AndOperator(("a", "b"), values)
        and_operator.add_suboperator(expression)
        output = and_operator.evaluate(context)
        expected_res = (
            ("c: 1", "a: 0", "b: 0"),
            ("c: 1", "a: 0", "b: 1"),
            ("c: 1", "a: 1", "b: 0"),
            ("c: 1", "a: 1", "b: 1"),
        )
        self.assertEqual(output, expected_res)

        values = ((0, 0), )
        context = LogicalOperatorContext(dict())
        and_operator = AndOperator(("a", ), values)
        and_operator.add_suboperator(expression)
        with self.assertRaises(RuntimeError) as _:
            and_operator.evaluate(context)


class TestOperator(unittest.TestCase):
    def test_operator_add_suboperator(self):
        operator1 = LogicalOperator(LogicalOperatorType.ALL, None, None)
        operator2 = LogicalOperator(LogicalOperatorType.ALL, None, None)
        operator1.add_suboperator(operator2)
        self.assertEqual(operator1.suboperator, operator2)
        operator3 = LogicalOperator(LogicalOperatorType.ALL, None, None)
        operator4 = LogicalOperator(LogicalOperatorType.EXISTS, None, None)
        operator3.add_suboperator(operator4)
        self.assertEqual(operator3.suboperator, operator4)
        operator5 = LogicalOperator(LogicalOperatorType.ALL, None, None)
        operator6 = DummyExpressionOperator(0, 0)
        operator5.add_suboperator(operator6)
        self.assertEqual(operator5.suboperator, operator6)
        operator7 = LogicalOperator(LogicalOperatorType.EXISTS, None, None)
        operator8 = LogicalOperator(LogicalOperatorType.ALL, None, None)
        with self.assertRaises(RuntimeError) as _:
            operator7.add_suboperator(operator8)
        operator9 = LogicalOperator(LogicalOperatorType.EXISTS, None, None)
        operator10 = LogicalOperator(LogicalOperatorType.EXISTS, None, None)
        operator9.add_suboperator(operator10)
        self.assertEqual(operator9.suboperator, operator10)
        operator11 = LogicalOperator(LogicalOperatorType.EXISTS, None, None)
        operator12 = DummyExpressionOperator(0, 0)
        operator11.add_suboperator(operator12)
        self.assertEqual(operator11.suboperator, operator12)

    def test_operator_chain(self):
        operator1 = LogicalOperator(LogicalOperatorType.ALL, None, None)
        operator2 = LogicalOperator(LogicalOperatorType.ALL, None, None)
        operator3 = LogicalOperator(LogicalOperatorType.EXISTS, None, None)
        operator4 = LogicalOperator(LogicalOperatorType.EXISTS, None, None)
        operator5 = DummyExpressionOperator(0, 0)
        operator1.chain(operator2).chain(operator3).chain(operator4).chain(operator5)
        self.assertEqual(operator1.suboperator, operator2)
        self.assertEqual(operator2.suboperator, operator3)
        self.assertEqual(operator3.suboperator, operator4)
        self.assertEqual(operator4.suboperator, operator5)
        with self.assertRaises(RuntimeError) as _:
            operator1.chain(LogicalOperator(LogicalOperatorType.EXPRESSION, None, None))
        with self.assertRaises(RuntimeError) as _:
            operator2.chain(LogicalOperator(LogicalOperatorType.ALL, None, None))
        with self.assertRaises(RuntimeError) as _:
            operator3.chain(LogicalOperator(LogicalOperatorType.EXISTS, None, None))
        operator6 = LogicalOperator(LogicalOperatorType.ALL, None, None)
        operator7 = LogicalOperator(LogicalOperatorType.ALL, None, None)
        operator8 = LogicalOperator(LogicalOperatorType.EXISTS, None, None)
        operator9 = LogicalOperator(LogicalOperatorType.EXISTS, None, None)
        operator6.chain(operator8).chain(operator9)
        with self.assertRaises(RuntimeError) as _:
            operator6.chain(operator7)


class DummyFunction(Function):
    def __init__(self, name: str, length: int, evaluation=0):
        self.name = name
        self.arguments_len = length
        self.evaluation = evaluation

    def evaluate(self, args: Tuple[str], context: LogicalOperatorContext) -> int:
        return str(self.evaluation) + "|" + "|".join(args)


class DummyConstant(Function):
    def __init__(self, name: str):
        self.name = name
        self.arguments_len = 0
        self.evaluation = name
    
    def evaluate(self, args: Tuple[str, ...], context: LogicalOperatorContext) -> int:
        return self.name + "|" + "|".join(args)


class DummyExpressionOperator(ExpressionOperator):
    def __init__(self, number_of_functions, number_of_constants):
        self.operator_type = LogicalOperatorType.EXPRESSION
        funcs = list(
            (
                DummyFunction(f"func{i}", i, evaluation=i),
                tuple(str(j) for j in range(1, i + 1)),
                1
            )
            for i in range(1, number_of_functions + 1)
        )
        consts = list(
            (
                DummyConstant(str(i)),
                (),
                1
            )
            for i in range(number_of_functions + 1, number_of_constants + number_of_functions + 1)
        )
        self.expressions = tuple(funcs + consts)


class DummySimpleOperatorEvaluation(LogicalOperator):
    def __init__(self):
        self.operator_type = LogicalOperatorType.EXPRESSION

    def evaluate(self, context: LogicalOperatorContext):
        return (tuple(str(k) + ": " + str(v) for k, v in context.vars.items()), )


class DummyFixedOperatorEvaluation(LogicalOperator):
    def __init__(self, evaluation_result):
        self.evaluation_result = evaluation_result
        self.operator_type = LogicalOperatorType.EXPRESSION

    def evaluate(self, _):
        return self.evaluation_result

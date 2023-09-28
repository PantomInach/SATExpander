from src.sat_expander.QuantorContext import QuantorContext
from src.sat_expander.Quantor import ExpressionQuantor, Quantor, AllQuantor, ExistsQuantor, QuantorType
from src.sat_expander.Function import Function

from typing import Tuple

import unittest


class TestQuantorContext(unittest.TestCase):
    def test_quantor_context_expand(self):
        context = QuantorContext(dict())
        context2 = context.expandContext(a=1)
        context3 = context2.expandContext(b=2, c=2)
        self.assertEqual(context.vars, dict())
        self.assertEqual(context2.vars, {"a": 1})
        self.assertEqual(context3.vars, {"a": 1, "b": 2, "c": 2})
        self.assertEqual(QuantorContext.empty().vars, dict())
        with self.assertRaises(ValueError) as _:
            context3.expandContext(a=1)

    def test_quantor_context_get(self):
        context = QuantorContext({"a": 1})
        self.assertEqual(context.getArgument("a"), 1)
        context = QuantorContext({"a": (1, 2, 3)})
        self.assertEqual(context.getArgument("a"), (1, 2, 3))
        context = QuantorContext({"abc": 1})
        self.assertEqual(context.getArgument("abc"), 1)
        with self.assertRaises(ValueError) as _:
            context.getArgument("Something")


class TestExpressionQuantor(unittest.TestCase):
    def test_expression_quantor_parse(self):
        functions = list(
            map(lambda i: DummyFunction(f"func{i}", i), range(1, 4))
        )
        functions.append(DummyFunction("f", 0))
        functions = tuple(functions)
        expressions = ("  func1(  a)", "func2   (b,c)", " func3(d,e,    f  )  ")
        expr_quant = ExpressionQuantor(functions, expressions)
        self.assertEqual(expr_quant.expressions, (
            (functions[0], ("a",), 1),
            (functions[1], ("b", "c"), 1),
            (functions[2], ("d", "e", "f"), 1)
        ))
        expressions = ("  func1(  a)", "func2   (b,b)")
        expr_quant = ExpressionQuantor(functions, expressions)
        self.assertEqual(expr_quant.expressions, (
            (functions[0], ("a",), 1),
            (functions[1], ("b", "b"), 1),
        ))
        expressions = ("-func1(a)", )
        expr_quant = ExpressionQuantor(functions, expressions)
        self.assertEqual(expr_quant.expressions, (
            (functions[0], ("a",), -1),
        ))
        expressions = ("-func1(a)", )
        expr_quant = ExpressionQuantor(functions, expressions)
        self.assertEqual(expr_quant.expressions, (
            (functions[0], ("a",), -1),
        ))
        expressions = ("f", )
        expr_quant = ExpressionQuantor(functions, expressions)
        self.assertEqual(expr_quant.expressions, (
            (functions[-1], (), 1),
        ))
        expressions = (" -  f ", )
        expr_quant = ExpressionQuantor(functions, expressions)
        self.assertEqual(expr_quant.expressions, (
            (functions[-1], (), -1),
        ))

        expressions = (
            "  func1(  a)a", "func2   (b,c)", "func3(d,e,    f  )  "
        )
        with self.assertRaises(ValueError) as _:
            ExpressionQuantor(functions, expressions)
        expressions = (
            "  func1(  a)", "func2   b,c)", "func3(d,e,    f  )  "
        )
        with self.assertRaises(ValueError) as _:
            ExpressionQuantor(functions, expressions)
        expressions = (
            "  func1(  a)", "func2   (b,c)", "func3(d,e),    f  )  "
        )
        with self.assertRaises(ValueError) as _:
            ExpressionQuantor(functions, expressions)
        expressions = (
            "  func1(  a()", "func2   (b,c)", "func3(d,e,    f  )  "
        )
        with self.assertRaises(ValueError) as _:
            ExpressionQuantor(functions, expressions)
        expressions = (
            "  func9(  a)", "func2   (b,c)", "func3(d,e,    f  )  "
        )
        with self.assertRaises(ValueError) as _:
            ExpressionQuantor(functions, expressions)
        expressions = (
            "  func(  a, a)", "func2   (b,c)", "func3(d,e,    f  )  "
        )
        with self.assertRaises(ValueError) as _:
            ExpressionQuantor(functions, expressions)
        # )

    def test_expression_quantor_addSubquantor(self):
        functions = (DummyFunction("func1", 1),)
        expressions = ("func1(a)", )
        expr_quant = ExpressionQuantor(functions, expressions)
        with self.assertRaises(NotImplementedError) as _:
            expr_quant.add_subquantor(None)

    def test_expression_quantor_evaluate(self):
        expression_quantor = DummyExpressionQuantor(3, 0)
        self.assertEqual(
            expression_quantor.evaluate(None),
            (("1|1", "2|1|2", "3|1|2|3"), )
        )

        expression_quantor = DummyExpressionQuantor(0, 2)
        self.assertEqual(expression_quantor.evaluate(None), (("1|", "2|"),))

        expression_quantor = DummyExpressionQuantor(1, 1)
        self.assertEqual(expression_quantor.evaluate(None), (("1|1", "2|"),))


class TestExistsQuantor(unittest.TestCase):
    def test_existst_quantor_evaluate(self):
        values = ((0, 0), (0, 1), (1, 0), (1, 1))
        context = QuantorContext({"c": 1, "d": 2, "e": 3})
        expression = DummySimpleQuantorEvaluation()
        exists = ExistsQuantor(("a", "b"), values)
        exists.add_subquantor(expression)
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
        context = QuantorContext(dict())
        expression = DummySimpleQuantorEvaluation()
        exists = ExistsQuantor(("a", ), values)
        exists.add_subquantor(expression)
        with self.assertRaises(RuntimeError) as _:
            exists.evaluate(context)

        values = ((0, ), )
        context = QuantorContext(dict())
        expression = DummyFixedQuantorEvaluation(((1,), (1,)))
        exists = ExistsQuantor(("a", ), values)
        exists.add_subquantor(expression)
        with self.assertRaises(RuntimeError) as _:
            exists.evaluate(context)


class TestAllQuantor(unittest.TestCase):
    def test_all_quantor_evaluate(self):
        values = ((0, 0), (0, 1), (1, 0), (1, 1))
        context = QuantorContext({"c": 1})
        expression = DummySimpleQuantorEvaluation()
        all_quant = AllQuantor(("a", "b"), values)
        all_quant.add_subquantor(expression)
        output = all_quant.evaluate(context)
        expected_res = (
            ("c: 1", "a: 0", "b: 0"),
            ("c: 1", "a: 0", "b: 1"),
            ("c: 1", "a: 1", "b: 0"),
            ("c: 1", "a: 1", "b: 1"),
        )
        self.assertEqual(output, expected_res)

        values = ((0, 0), )
        context = QuantorContext(dict())
        all_quant = AllQuantor(("a", ), values)
        all_quant.add_subquantor(expression)
        with self.assertRaises(RuntimeError) as _:
            all_quant.evaluate(context)


class TestQuantor(unittest.TestCase):
    def test_quantor_add_subquantor(self):
        quant1 = Quantor(QuantorType.ALL, None, None)
        quant2 = Quantor(QuantorType.ALL, None, None)
        quant1.add_subquantor(quant2)
        self.assertEqual(quant1.subquantor, quant2)
        quant3 = Quantor(QuantorType.ALL, None, None)
        quant4 = Quantor(QuantorType.EXISTS, None, None)
        quant3.add_subquantor(quant4)
        self.assertEqual(quant3.subquantor, quant4)
        quant5 = Quantor(QuantorType.ALL, None, None)
        quant6 = DummyExpressionQuantor(0, 0)
        quant5.add_subquantor(quant6)
        self.assertEqual(quant5.subquantor, quant6)
        quant7 = Quantor(QuantorType.EXISTS, None, None)
        quant8 = Quantor(QuantorType.ALL, None, None)
        with self.assertRaises(RuntimeError) as _:
            quant7.add_subquantor(quant8)
        quant9 = Quantor(QuantorType.EXISTS, None, None)
        quant10 = Quantor(QuantorType.EXISTS, None, None)
        quant9.add_subquantor(quant10)
        self.assertEqual(quant9.subquantor, quant10)
        quant11 = Quantor(QuantorType.EXISTS, None, None)
        quant12 = DummyExpressionQuantor(0, 0)
        quant11.add_subquantor(quant12)
        self.assertEqual(quant11.subquantor, quant12)

    def test_quantor_chain(self):
        quant1 = Quantor(QuantorType.ALL, None, None)
        quant2 = Quantor(QuantorType.ALL, None, None)
        quant3 = Quantor(QuantorType.EXISTS, None, None)
        quant4 = Quantor(QuantorType.EXISTS, None, None)
        quant5 = DummyExpressionQuantor(0, 0)
        quant1.chain(quant2).chain(quant3).chain(quant4).chain(quant5)
        self.assertEqual(quant1.subquantor, quant2)
        self.assertEqual(quant2.subquantor, quant3)
        self.assertEqual(quant3.subquantor, quant4)
        self.assertEqual(quant4.subquantor, quant5)
        with self.assertRaises(RuntimeError) as _:
            quant1.chain(Quantor(QuantorType.EXPRESSION, None, None))
        with self.assertRaises(RuntimeError) as _:
            quant2.chain(Quantor(QuantorType.ALL, None, None))
        with self.assertRaises(RuntimeError) as _:
            quant3.chain(Quantor(QuantorType.EXISTS, None, None))
        quant6 = Quantor(QuantorType.ALL, None, None)
        quant7 = Quantor(QuantorType.ALL, None, None)
        quant8 = Quantor(QuantorType.EXISTS, None, None)
        quant9 = Quantor(QuantorType.EXISTS, None, None)
        quant6.chain(quant8).chain(quant9)
        with self.assertRaises(RuntimeError) as _:
            quant6.chain(quant7)


class DummyFunction(Function):
    def __init__(self, name: str, length: int, evaluation=0):
        self.name = name
        self.arguments_len = length
        self.evaluation = evaluation

    def evaluate(self, args: Tuple[str], context: QuantorContext) -> int:
        return str(self.evaluation) + "|" + "|".join(args)


class DummyConstant(Function):
    def __init__(self, name: str):
        self.name = name
        self.arguments_len = 0
        self.evaluation = name
    
    def evaluate(self, args: Tuple[str, ...], context: QuantorContext) -> int:
        return self.name + "|" + "|".join(args)


class DummyExpressionQuantor(ExpressionQuantor):
    def __init__(self, number_of_functions, number_of_constants):
        self.quantor_type = QuantorType.EXPRESSION
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


class DummySimpleQuantorEvaluation(Quantor):
    def __init__(self):
        self.quantor_type = QuantorType.EXPRESSION

    def evaluate(self, context: QuantorContext):
        return (tuple(str(k) + ": " + str(v) for k, v in context.vars.items()), )


class DummyFixedQuantorEvaluation(Quantor):
    def __init__(self, evaluation_result):
        self.evaluation_result = evaluation_result
        self.quantor_type = QuantorType.EXPRESSION

    def evaluate(self, _):
        return self.evaluation_result

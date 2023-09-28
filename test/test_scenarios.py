from src.sat_expander.Functions import FunctionFactory, Function
from src.sat_expander.LogicalOperator import AndOperator, OrOperator, ExpressionOperator

from itertools import product

import unittest


class TestScenarios(unittest.TestCase):
    def test_scenario1(self):
        base_set = set(range(1, 4))
        domain = tuple(product(base_set, repeat=2))
        factory = FunctionFactory()
        func: Function = factory.build("f", 2, domain)
        quant = AndOperator(("x", ), Function.to_tuple_iter(base_set)).chain(
            OrOperator(("y", ), Function.to_tuple_iter(base_set))
        ).chain(
            ExpressionOperator(factory, ("f(x, y)",))
        )
        f = func.relation
        expected_res = (
            (f[(1, 1)], f[(1, 2)], f[(1, 3)]),
            (f[(2, 1)], f[(2, 2)], f[(2, 3)]),
            (f[(3, 1)], f[(3, 2)], f[(3, 3)])
        )
        self.assertEqual(quant.evaluate(), expected_res)

    def test_scenario2(self):
        base_set1 = set(range(1, 4))
        base_set2 = ("aa", "bb", "cc")
        domain1 = tuple(product(base_set1, base_set2))
        domain2 = base_set1
        factory = FunctionFactory()
        func1 = factory.build("ff", 2, domain1)
        func2 = factory.build("gg", 1, Function.to_tuple_iter(domain2))
        quant = AndOperator(("x", "y"), zip(base_set1, base_set2)).chain(
            AndOperator(("z"), Function.to_tuple_iter(base_set1))
        ).chain(
            ExpressionOperator(factory, ("-ff(z,y)", "gg(x)"))
        )
        f = func1.relation
        g = func2.relation
        expected_result = (
            (-f[(1, "aa")], g[(1, )]),
            (-f[(2, "aa")], g[(1, )]),
            (-f[(3, "aa")], g[(1, )]),
            (-f[(1, "bb")], g[(2, )]),
            (-f[(2, "bb")], g[(2, )]),
            (-f[(3, "bb")], g[(2, )]),
            (-f[(1, "cc")], g[(3, )]),
            (-f[(2, "cc")], g[(3, )]),
            (-f[(3, "cc")], g[(3, )]),
        )
        self.assertEqual(quant.evaluate(), expected_result)

    def test_scenario3(self):
        base_set1 = set(range(1, 4))
        base_set2 = ("aa", "bb", "cc")
        domain1 = tuple(product(base_set1, base_set2))
        factory = FunctionFactory()
        func1 = factory.build("ff", 2, domain1)
        quant = AndOperator(("x", "y"), zip(base_set1, base_set2)).chain(
            AndOperator(("z",), Function.to_tuple_iter(base_set1))
        ).chain(
            ExpressionOperator(factory, ("-ff(z,y)", "ff(x,y)"))
        )
        f = func1.relation
        expected_result = (
            (-f[(1, "aa")], f[(1, "aa")]),
            (-f[(2, "aa")], f[(1, "aa")]),
            (-f[(3, "aa")], f[(1, "aa")]),
            (-f[(1, "bb")], f[(2, "bb")]),
            (-f[(2, "bb")], f[(2, "bb")]),
            (-f[(3, "bb")], f[(2, "bb")]),
            (-f[(1, "cc")], f[(3, "cc")]),
            (-f[(2, "cc")], f[(3, "cc")]),
            (-f[(3, "cc")], f[(3, "cc")]),
        )
        self.assertEqual(quant.evaluate(), expected_result)

    def test_scenario4(self):
        factory = FunctionFactory()
        factory.add_constant("n")
        base_set = tuple(Function.to_tuple_iter(("hi", "bye")))
        func = factory.build("f", 1, base_set)
        quant = AndOperator(("x",), base_set).chain(
            ExpressionOperator(factory, ("-n", "f(x)"))
        )
        f = func.relation
        expected_result = (
            (-1, f[("hi",)]),
            (-1, f[("bye",)]),
        )
        self.assertEqual(quant.evaluate(), expected_result)
        quant2 = OrOperator(("y",), base_set).chain(
            ExpressionOperator(factory, ("n", "-f(y)"))
        )
        expected_result = (
            (1, -f[("hi",)], 1, -f[("bye",)]),
        )
        self.assertEqual(quant2.evaluate(), expected_result)

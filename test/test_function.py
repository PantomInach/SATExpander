import unittest

from src.sat_expander.LogicalOperatorContext import LogicalOperatorContext
from src.sat_expander.Functions import Function, FunctionFactory


class TestFunction(unittest.TestCase):
    def test_function_construction(self):
        with self.assertRaises(RuntimeError) as _:
            Function("test_func", 1, range(10), start_variable=1)
        with self.assertRaises(RuntimeError) as _:
            Function("test_func", 2, range(10), start_variable=1)
        func = Function("test_func", 1, ((1,), (2,), (3,)), start_variable=1)
        self.assertEqual(func.domain, {(1,), (2,), (3,)})
        self.assertEqual(func.range, (1, 3))
        self.assertEqual(func.relation, {(1,): 1, (2,): 2, (3,): 3})

    def test_function_to_tuple_iter(self):
        self.assertEqual(
            tuple(Function.to_tuple_iter(range(4))),
            ((0, ), (1,), (2,), (3,))
        )

    def test_function_evaluate(self):
        domain = ((0, ), (1,), (2,), (3,))
        func = Function("test_func", 1, domain, start_variable=2)
        context = LogicalOperatorContext.empty().expandContext(a=1, b=2, c=3)
        self.assertEqual(func.evaluate(("a", ), context), 3)
        self.assertEqual(func.evaluate(("b", ), context), 4)
        self.assertEqual(func.evaluate(("c", ), context), 5)
        with self.assertRaises(ValueError) as _:
            func.evaluate(("a", "b"), context)

        domain = ((0, 0), (1, 0), (2, 0), (3, 1))
        func = Function("test_func", 2, domain, start_variable=0)
        context = LogicalOperatorContext.empty().expandContext(a=1, b=2, c=3, d=0)
        self.assertEqual(
            func.evaluate(("a", "d"), context),
            func.relation[(1, 0)]
        )
        self.assertEqual(
            func.evaluate(("d", "d"), context),
            func.relation[(0, 0)]
        )
        self.assertEqual(
            func.evaluate(("c", "a"), context),
            func.relation[(3, 1)]
        )
        with self.assertRaises(ValueError) as _:
            func.evaluate(("c",), context)
        with self.assertRaises(ValueError) as _:
            func.evaluate(("c", "a", "d"), context)
        with self.assertRaises(ValueError) as _:
            func.evaluate(("c", "t"), context)

    def test_function_communitive(self):
        domain = ((0, 1), (1, 0), (2, 3), (3, 1))
        func = Function("test_func", 2, domain, start_variable=2)
        func.set_commutative()
        f = func.relation
        self.assertEqual(f[(0, 1)], f[(1, 0)])
        self.assertNotEqual(f[(2, 3)], f[(3, 1)])

    def test_function_tuple_same(self):
        t1 = (1, 2, 3)
        t2 = (3, 2, 1)
        self.assertTrue(Function._tuple_contain_same_elements(t1, t2))
        t3 = (1, 2)
        self.assertFalse(Function._tuple_contain_same_elements(t1, t3))
        t4 = (2, 2, 3)
        self.assertFalse(Function._tuple_contain_same_elements(t1, t4))

    def test_function_factory(self):
        factory = FunctionFactory()
        domain = ((1,), (2,), (3,))
        func1 = factory.build("func1", 1, domain)
        self.assertEqual(factory.variable_counter, 4)
        self.assertEqual(func1.relation, {(1,): 1, (2,): 2, (3,): 3})
        func2 = factory.build("func2", 1, domain)
        self.assertEqual(factory.variable_counter, 7)
        self.assertEqual(func2.relation, {(1,): 4, (2,): 5, (3,): 6})
        with self.assertRaises(ValueError) as _:
            factory.build("func1", 1, domain)

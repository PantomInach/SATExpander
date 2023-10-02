from sat_expander.ExclusionPredicates import exclude_variable, exclude_var_tuple, _handle_vars_not_found, VarNotFoundResponse

import unittest


class TestExclusionPredicates(unittest.TestCase):
    def test_handle_vars_not_founf(self):
        context = DummyContext({"a": 1, "b": 2})
        with self.assertWarns(Warning):
            _handle_vars_not_found(context, "x", var_not_found_response=VarNotFoundResponse.WARN)
        with self.assertRaises(Exception):
            _handle_vars_not_found(context, "x", var_not_found_response=VarNotFoundResponse.ERROR)
        _handle_vars_not_found(context, "x", var_not_found_response=VarNotFoundResponse.IGNORE)

    def test_exclude_variable_predicate(self):
        values = ((1, ), (2, ), (3, ), (4, ))
        context = DummyContext({"x": 1, "a": 2, "b": 3})
        predicate = exclude_variable("x", var_not_found_response=VarNotFoundResponse.ERROR)
        self.assertEqual(values[1:], tuple(x for x in values if predicate(context, x)))
        predicate = exclude_variable("y", var_not_found_response=VarNotFoundResponse.IGNORE)
        self.assertEqual(values, tuple(x for x in values if predicate(context, x)))

    def test_exclude_var_tuple_predicate(self):
        values = ((1, 1), (2, 2), (3, 3), (4, 4))
        context = DummyContext({"x": 1, "y": 1, "a": 2})
        predicate = exclude_var_tuple("x", "y", var_not_found_response=VarNotFoundResponse.ERROR)
        self.assertEqual(values[1:], tuple(x for x in values if predicate(context, x)))
        context = DummyContext({"x": 1, "y": 2, "a": 2})
        self.assertEqual(values, tuple(x for x in values if predicate(context, x)))

class DummyContext():
    def __init__(self, vars):
        self.vars = vars

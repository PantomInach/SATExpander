from sat_expander.CNF import join_cnfs, cnf_to_dimacs

import unittest


class TestCNF(unittest.TestCase):
    def test_cnf_join(self):
        cnf1 = ((-1, 2, 3), (4, 5, 6))
        cnf2 = ((-7, 8, 9), (10, 11, 12))
        expected_result = ((-1, 2, 3), (4, 5, 6), (-7, 8, 9), (10, 11, 12))
        self.assertEqual(join_cnfs(cnf1, cnf2), expected_result)

    def test_cnf_to_dimacs(self):
        cnf = ((-1, 2, 3), (-2, 3, 4), (-3, 4, 5), (1, 3, -5))
        expected_result = """p cnf 5 4
-1 2 3 0
-2 3 4 0
-3 4 5 0
1 3 -5 0
"""
        self.assertEqual(cnf_to_dimacs(cnf, header=""), expected_result)

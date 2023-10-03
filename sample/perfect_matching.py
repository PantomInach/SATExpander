"""
Here we want to construct a SAT formulation to decide if a graph has a perfect
matching.
A perfect matching of a graph consists of edges such that non of these edges
share an incident vertexand every vertex is incident to one of these edges.

The graph G=(V,E) consists of a vertex set consisting of integers and an edge
set consisting of pairs of vertices.
For example: G=((1, 2, 3, 4), ((1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)))
"""
from sat_expander.LogicalOperator import OrOperator, AndOperator, ExpressionOperator
from sat_expander.Functions import FunctionFactory, to_tuple_iter
from sat_expander.ExclusionPredicates import check_variables_in_context
from sat_expander.CNF import cnf_to_dimacs

from typing import Tuple


def create_sat_formulation(V: Tuple[int, ...], E: Tuple[Tuple[int, int], ...]) -> str:
    """
    First we define the function 'p(u,v)' which describes if the edeg
    consisting of the vertices u, v is in the perfect matching.
    """
    factory = FunctionFactory()
    factory.build("p", 2, E)

    @check_variables_in_context("v")
    def vertex_in_edge(context, value: Tuple[int, int]) -> bool:
        # Checks if edge is incident to vertex v
        return context.vars["v"] in value

    """
    For each vertex v, there should be an edge uw such that either u=v or w=v
    and uw is in the perfect matching.
    """
    each_vertex_in_matching = AndOperator(("v", ), to_tuple_iter(V)).chain(
        OrOperator(("u", "w"), E, vertex_in_edge)
    ).chain(
        ExpressionOperator(factory, ("p(u, w)", ))
    )

    """
    Next we want to ensure that, for each vertex, any two incident edges aren't
    both in the perfect matching.

    We also need the additional predicate:
    v needs to be incident to the edge e' and e' != e
    """
    @check_variables_in_context("v", "u", "w")
    def vertex_in_edge_and_edges_not_same(context, edge: Tuple[int, int]) -> bool:
        return context.vars["v"] in edge and set(edge) != set((context.vars["u"], context.vars["w"]))

    vertex_dont_share_two_edges_in_matching = AndOperator(("v", ), to_tuple_iter(V)).chain(
        AndOperator(("u", "w"), E, vertex_in_edge)
    ).chain(
        AndOperator(("r", "s"), E, vertex_in_edge_and_edges_not_same)
    ).chain(
        ExpressionOperator(factory, ("-p(u,w)", "-p(r,s)"))
    )

    cnf1 = each_vertex_in_matching.evaluate()
    cnf2 = vertex_dont_share_two_edges_in_matching.evaluate()
    return cnf_to_dimacs(cnf1 + cnf2)


if __name__ == "__main__":
    V = (1, 2, 3, 4)
    E = ((1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4))
    print(create_sat_formulation(V, E))

"""
integration_order_influence.py - By Vincent Derkinderen and Samuel Kolb (KU Leuven DTAI, 2020)
Show the influence of the integration order by providing the result after integrating only one variable.
This can be used to, for example, show that in a star-like interaction graph, integrating out the middle variable first
is more expensive than first integrating out the variables on the side.

Provided code contains the following problem:
\\int 1 (\\prod_{i=1,..,4} [x_0 <= x_i]) (\\prod_{i=0,...,,4} [0 <= x_i <= 1]) dx
The interaction  graph of this problem is star-shaped. Integrating out middle (x0) first yields larger
intermediate results than first integrating out the sides (x1,...,x4).
"""
import graphviz
from pywmi.engines.pyxadd.engine import ToXaddWalker
from pywmi.engines.pyxadd.operation import Multiplication
from pywmi.engines.pyxadd.algebra import PyXaddAlgebra
from _pywmi.problems import *
from _pywmi.vtree.bottomup_elimination import bottomup_balanced_minfill as bamif
from _pywmi.xsdd import MeasuredFXSDD


def problem_from_graph(graph):
    """ Create a problem from the given interaction graph. For each interaction (i,j), 0 <= i <= j <= 1 is added. """
    n = graph.vcount()
    domain = Domain.make([], [f"x{i}" for i in range(n)], real_bounds=(0, 1))
    X = domain.get_symbols()
    support = smt.And(*((X[e.source] <= X[e.target]) for e in graph.es))
    return Density(domain, support & domain.get_bounds(), smt.Real(1))


def integrate_one_var(first_var):
    algebra = PyXaddAlgebra(reduce_strategy=PyXaddAlgebra.FULL_REDUCE)
    density = problem_from_graph(tpg_star(5))
    # Construct Theory in XADD format
    theory_xadd = ToXaddWalker(True, algebra.pool).walk_smt(density.support)
    weight_xadd = ToXaddWalker(False, algebra.pool).walk_smt(density.weight)
    combined = algebra.pool.apply(Multiplication, theory_xadd, weight_xadd)
    # Integrate out variable
    result = algebra.integrate(density.domain, combined, [first_var])
    # Show results
    xadd = algebra.pool.diagram(result)
    xadd.show(True)


def get_sdd():
    algebra = PyXaddAlgebra(reduce_strategy=PyXaddAlgebra.FULL_REDUCE)
    density = problem_from_graph(tpg_star(5))
    mfxsdd = MeasuredFXSDD(density.domain, density.support, smt.Real(1),
                           algebra=algebra, vtree_strategy=bamif, ordered=False)
    res = mfxsdd.compute_volume(add_bounds=False)  # should be part of density already
    print(res)
    graphviz.Source(mfxsdd.sdd_to_dot()).render(view=True)


integrate_one_var(first_var='x0')
#integrate_one_var(first_var='x1')
#get_sdd()



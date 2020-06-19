"""
BaMi_optimal.py - compares BaMiC with BaMiF and includes the (according to us) optimal integration strategies.
"""
import sys
import matplotlib.pyplot as plt
from pywmi.engines.xsdd.literals import LiteralInfo

from _pywmi.vtree.bottomup_elimination import bottomup_balanced_minfill as bamif
from _pywmi.vtree.topdown_balanced_mincut import topdown_balanced_mincut_hg as bamic
from _pywmi.vtree.int_tree import *
from _pywmi.vtree.topdown_mincut import conversion_tables
from _pywmi.experiment import *
from _pywmi.problems import *

from pywmi.engines.pyxadd.algebra import PyXaddAlgebra

full_reduce = True
reduce_strategy = PyXaddAlgebra.FULL_REDUCE if full_reduce else PyXaddAlgebra.ONLY_INIT_INTEGRATION_REDUCE
all_strats = [bamic,
              bamif]
xadd = lambda: PyXaddAlgebra(reduce_strategy=reduce_strategy)

# %%

tpg_star_gen = lambda n: make_from_graph(tpg_star(n))
tpg_3ary_gen = lambda n: make_from_graph(tpg_3ary_tree(n))
tpg_path_gen = lambda n: make_from_graph(tpg_path(n))

# %%

size_range = list(range(3, 41))
env_timeout.set(50)
ordered = False
algebra = xadd
verbose = False

sys.setrecursionlimit(10**6)

# %%

def splitpath_int_vtree_gen(literal_info: LiteralInfo):
    """ Creates an integration order in a split path form x0 - x1 - x2 - x3 - ... """
    logic2cont, cont2logic = conversion_tables(literal_info)
    cont_vars = sorted(list(cont2logic.keys()), key=lambda n: int(n[1:]))
    assert len(cont_vars) >= 3
    middle_index = math.floor(len(cont_vars)/2)

    # Create left line
    left_int_tree = IntTreeVar(cont_vars[0])
    for cont in cont_vars[1:middle_index]:
        left_int_tree = IntTreeLine(cont, left_int_tree)

    # Create right line
    right_int_tree = IntTreeVar(cont_vars[-1])
    for cont in reversed(cont_vars[middle_index+1:-1]):
        right_int_tree = IntTreeLine(cont, right_int_tree)

    # Middle split
    int_tree = IntTreeSplit(cont_vars[middle_index], left_int_tree, right_int_tree)
    return int_tree.create_vtree(logic2cont.keys(), logic2cont)


def star_int_vtree_gen(literal_info: LiteralInfo):
    """ Creates an integration order for problems with a star primal (star, xor, mutex). """
    logic2cont, cont2logic = conversion_tables(literal_info)
    middle_var, _ = max(cont2logic.items(), key=lambda x: len(x[1]))
    other_vars_int_trees = [IntTreeVar(v) for v in cont2logic.keys() if v != middle_var]
    if len(other_vars_int_trees) != 0:
        int_tree = IntTreeParallel(middle_var, other_vars_int_trees)
    else:
        int_tree = IntTreeVar(middle_var)
    return int_tree.create_vtree(logic2cont.keys(), logic2cont)


def dual_int_vtree_gen(literal_info: LiteralInfo):
    """ Creates an integration order for the dual problem. """
    logic2cont, cont2logic = conversion_tables(literal_info)
    cont_pairs = [list(pair) for pair in logic2cont.values() if len(pair) == 2]
    int_pairs = [IntTreeLine(x[0], IntTreeVar(x[1])) for x in cont_pairs]
    int_tree = IntTreeParallel(None, int_pairs)
    return int_tree.create_vtree(logic2cont.keys(), logic2cont)

# %%


# DUAL
all_strats.append(dual_int_vtree_gen)
dual_exp = CompareStrategies(
    algebra=algebra,
    problem_generator=dual,
    size=size_range,
    vtree_strategy=all_strats,
    verbose=verbose,
    ordered=ordered,
)
print("Finished dual_exp")
all_strats.pop()

# XOR
all_strats.append(star_int_vtree_gen)
xor_exp = CompareStrategies(
    algebra=algebra,
    problem_generator=xor,
    size=size_range,
    vtree_strategy=all_strats,
    verbose=verbose,
    ordered=ordered,
)
print("Finished xor_exp")
all_strats.pop()

# MUTEX
all_strats.append(star_int_vtree_gen)
mutex_exp = CompareStrategies(
    algebra=algebra,
    problem_generator=mutual_exclusive,
    size=size_range,
    vtree_strategy=all_strats,
    verbose=verbose,
    ordered=ordered,
)
print("Finished mutex_exp")
all_strats.pop()

# STAR
all_strats.append(star_int_vtree_gen)
tpg_star_exp = CompareStrategies(
    algebra=algebra,
    problem_generator=tpg_star_gen,
    size=size_range,
    vtree_strategy=all_strats,
    verbose=verbose,
    ordered=ordered,
)
print("Finished star_exp")
all_strats.pop()

# 3ARY
all_strats.append(bamif)    # TODO: Optimal strategy
tpg_3ary_exp = CompareStrategies(
    algebra=algebra,
    problem_generator=tpg_3ary_gen,
    size=size_range,
    vtree_strategy=all_strats,
    verbose=verbose,
    ordered=ordered,
)
print("Finished 3ary_exp")
all_strats.pop()

# PATH
all_strats.append(splitpath_int_vtree_gen)
tpg_path_exp = CompareStrategies(
    algebra=algebra,
    problem_generator=tpg_path_gen,
    size=size_range,
    vtree_strategy=all_strats,
    verbose=verbose,
    ordered=ordered,
)
print("Finished path_exp")
all_strats.pop()

# %% md

# Graph

# %%

all_data = [
    ('dual', dual_exp),
    ('xor', xor_exp),
    ('mutex', mutex_exp),
    ('pg-star', tpg_star_exp),
    ('pg-3ary', tpg_3ary_exp),
    ('pg-path', tpg_path_exp)
]

vtree_heuristics = [
    #('implicit-balanced', 'black', '+'),
    #('implicit-leftlinear', 'green', 'o'),
    #('implicit-rightlinear', 'purple', 's'),
    ('balanced-mincut', 'red', '.'),
    ('balanced-minfill', 'blue', ','),
    ('optimal', 'green', 'x')
]

# %%

from matplotlib.ticker import MaxNLocator

fig, axes = plt.subplots(2, 3)
fig.set_size_inches(9, 6)
fig.subplots_adjust(bottom=0.14, wspace=0.3, hspace=0.3)

for i, (name, exp) in enumerate(all_data):
    i1 = i // 3
    i2 = i % 3
    ax = axes[i1][i2]

    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    for (strat_name, color, marker), (_, times) in zip(vtree_heuristics, exp.all_experiments()):
        # vtree_times = list(times.get_all_results('vtree_time'))
        total_times = list(times.get_all_results('total_time'))

        sizes = times.values[:len(total_times)]
        ax.plot(sizes, total_times, color=color, marker=marker, linestyle='-', label=strat_name)
        # ax.plot(sizes, vtree_times, color=color, marker='o', linestyle='--')

    if i1 != 1:
        ax.set_xlabel(None)
    else:
        ax.set_xlabel("Problem size (n)")

    if i2 == 0:
        ax.set_ylabel("Time (s)")
    else:
        ax.set_ylabel(None)

    ax.set_title(f"{name}(n)")

# Bug: fig.legend not included in pdf
ax.legend(loc='lower center', ncol=2,
          bbox_to_anchor=(0.5, -0.04), bbox_transform=fig.transFigure)

# %%
filename = 'bami_comparison'
if ordered:
    filename += '-ordered'
if algebra == xadd:
    filename += '-xadd'
    filename += '-full' if full_reduce else '-init'
fig.savefig(filename + '.pdf', bbox_inches='tight')

# %%



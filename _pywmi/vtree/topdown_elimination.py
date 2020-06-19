import random
from typing import Dict

from pywmi.engines.xsdd.literals import LiteralInfo
from pywmi.engines.xsdd.vtrees.vtree import Vtree, balanced

from .primal import create_interaction_graph_from_literals
from .int_tree import IntTreeVar, IntTreeLine, IntTreeSplit, IntTreeParallel, IntTree
from .topdown_mincut import conversion_tables


def _sort_to_ordering(ordering: list, orderset: set, cut_off_index: int):
    """
    Sort elements in orderset by appearance in ordering, excl. any appearing later than index cut_off_index.
    The output is of type: ordering_index, element
    :param ordering: A list of ordered elements
    :param orderset: A list of elements to sort in order of appearance in ordering
    :param cut_off_index: The index from which to start. Any element before this index is excluded from the result.
    :return: Each element in orderset that appears in ordering after cut_off_index, returned in order of appearance
    in ordering as type: ordering_index, element
    """
    assert len(ordering) >= cut_off_index
    for index in range(cut_off_index + 1, len(ordering)):
        if ordering[index] in orderset:
            yield index, ordering[index]


def topdown_minfill(literals: LiteralInfo) -> Vtree:
    """
    Create a vtree by using a top-down min-fill approach.
    :param literals: The context to create a vtree for.
    :return: A vtree based on a top-down min-fill ordering.
    """
    logic2cont, cont2logic = conversion_tables(literals)

    # Create ordering
    primal = create_interaction_graph_from_literals(cont2logic.keys(), logic2cont.values(), True, False)
    primal.compute_fills()
    ordering = []
    neighbor_sets = []
    while primal.nb_fills() > 0:
        minfills = primal.get_minfills()
        selected_var = minfills[random.randint(0, len(minfills) - 1)]
        ordering.append(selected_var)
        neighbor_sets.append(primal.connected_to[selected_var])
        primal.remove_and_process_node(selected_var)
    ordering.reverse()

    if len(ordering) == 0:
        return balanced(literals)

    # Create induced graph
    primal = create_interaction_graph_from_literals(cont2logic.keys(), logic2cont.values(), True, False)
    for neighbors in neighbor_sets:  # for each var
        primal.add_edges(neighbors)

    # Construct pseudo tree by depth first traversing the induced graph
    int_trees: Dict[any, IntTree] = dict()

    def _construct_int_tree(var, index):
        """ Construct int_tree depth-first """
        if int_trees.get(var, None) is not None:  # Because then already covered
            return None

        neighbors = primal.connected_to[var]
        children = list(_sort_to_ordering(ordering, neighbors, index))
        if len(children) == 0:
            int_tree = IntTreeVar(var)
            int_trees[var] = int_tree
            return int_tree
        else:
            trees = [_construct_int_tree(child_var, child_index) for (child_index, child_var) in children]
            trees = [tree for tree in trees if tree is not None]
            assert len(trees) >= 1

            if len(trees) == 1:
                int_tree = IntTreeLine(var, trees[0])
                int_trees[var] = int_tree
                return int_tree
            elif len(trees) == 2:
                int_tree = IntTreeSplit(var, trees[0], trees[1])
                int_trees[var] = int_tree
                return int_tree
            else:
                int_tree = IntTreeParallel(var, trees)
                int_trees[var] = int_tree
                return int_tree

    indices = []
    for index, var in enumerate(ordering):
        if int_trees.get(var, None) is None:
            indices.append(index)
            _construct_int_tree(var, index)

    if len(indices) == 1:
        int_tree = int_trees[ordering[0]]
    else:
        int_tree = IntTreeParallel(var=None, trees=[int_trees[ordering[var_index]] for var_index in indices])
    return int_tree.create_vtree(logic2cont.keys(), logic2cont)


def topdown_minfill_shuffle(literals: LiteralInfo) -> Vtree:
    """
    Create a vtree by using a top-down min-fill approach, shuffling the input order.
    :param literals: The context to create a vtree for.
    :return: A vtree based on a top-down min-fill ordering, shuffling the input order
    """
    logic2cont, cont2logic = conversion_tables(literals)
    # Randomize
    continuous_vars = list(cont2logic.keys())
    random.shuffle(continuous_vars)
    co_occurrences = list(logic2cont.values())
    random.shuffle(co_occurrences)

    # Create ordering
    primal = create_interaction_graph_from_literals(cont2logic.keys(), logic2cont.values(), True, False)
    primal.compute_fills()
    ordering = []
    neighbor_sets = []
    while primal.nb_fills() > 0:
        minfills = primal.get_minfills()
        selected_var = minfills[random.randint(0, len(minfills) - 1)]
        ordering.append(selected_var)
        neighbor_sets.append(primal.connected_to[selected_var])
        primal.remove_and_process_node(selected_var)
    ordering.reverse()

    if len(ordering) == 0:
        return balanced(literals)

    # Create induced graph
    primal = create_interaction_graph_from_literals(cont2logic.keys(), logic2cont.values(), True, False)
    for neighbors in neighbor_sets:  # for each var
        primal.add_edges(neighbors)

    # Construct pseudo tree by depth first traversing the induced graph
    assert len(ordering) > 0
    int_trees: Dict[any, IntTree] = dict()

    def _construct_int_tree(var, index):
        """ Construct int_tree depth-first """
        if int_trees.get(var, None) is not None:  # Because then already covered
            return None

        neighbors = primal.connected_to[var]
        children = list(_sort_to_ordering(ordering, neighbors, index))
        if len(children) == 0:
            int_tree = IntTreeVar(var)
            int_trees[var] = int_tree
            return int_tree
        else:
            trees = [_construct_int_tree(child_var, child_index) for (child_index, child_var) in children]
            trees = [tree for tree in trees if tree is not None]
            assert len(trees) >= 1

            if len(trees) == 1:
                int_tree = IntTreeLine(var, trees[0])
                int_trees[var] = int_tree
                return int_tree
            elif len(trees) == 2:
                int_tree = IntTreeSplit(var, trees[0], trees[1])
                int_trees[var] = int_tree
                return int_tree
            else:
                int_tree = IntTreeParallel(var, trees)
                int_trees[var] = int_tree
                return int_tree

    indices = []
    for index, var in enumerate(ordering):
        if int_trees.get(var, None) is None:
            indices.append(index)
            _construct_int_tree(var, index)

    if len(indices) == 1:
        int_tree = int_trees[ordering[0]]
    else:
        int_tree = IntTreeParallel(var=None, trees=[int_trees[ordering[var_index]] for var_index in indices])

    # Randomize some more
    logic_variables = list(logic2cont.keys())
    random.shuffle(logic_variables)

    return int_tree.create_vtree(logic2cont.keys(), logic2cont)

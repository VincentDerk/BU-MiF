"""
bottomup_elimination.py - Contains several heuristics to compute a vtree based on a literal context (LiteralInfo).
"""
import random

#from pywmi.engines.xsdd.vtrees.vtree import *
from pywmi.engines.xsdd.literals import LiteralInfo
from pywmi.engines.xsdd.vtrees.vtree import Vtree, balanced

from .int_tree import IntTreeFactory, IntTreeVar, IntTreeLine
from .primal import create_interaction_graph_from_literals
from .topdown_mincut import conversion_tables


def bottomup_balanced_minfill(literals: LiteralInfo) -> Vtree:
    """
    Create a vtree by using a balanced min-fill approach, improving the balance of the integration order in the vtree.
    :param literals: The context to create a vtree for.
    :return: A vtree based on a balanced min-fill ordering.
    """
    logic2cont, cont2logic = conversion_tables(literals)
    primal = create_interaction_graph_from_literals(cont2logic.keys(), logic2cont.values(), True, False)
    int_factory = IntTreeFactory(primal)

    primal.compute_fills()
    while primal.nb_fills() > 0:
        minfills = primal.get_minfills()
        minfills = int_factory.get_least_depth_increase(minfills)  # balanced
        minfills = primal.get_lowest_future_minfill(minfills)  # balanced
        selected_var = minfills[0]
        int_factory.add_node(selected_var)
        primal.remove_and_process_node(selected_var)

    # Construct vtree
    int_tree = int_factory.get_int_tree()
    if int_tree is not None:
        return int_tree.create_vtree(set(logic2cont.keys()), logic2cont)
    else:
        return balanced(literals)


def bottomup_balanced_minfill_shuffle(literals: LiteralInfo) -> Vtree:
    """
    Create a vtree by using a balanced min-fill approach, shuffling the input order of the literals using the seed.
    The balanced part improves the balance of the integration order in the vtree.
    :param literals: The context to create a vtree for.
    :return: A vtree based on a balanced min-fill ordering.
    """
    logic2cont, cont2logic = conversion_tables(literals)
    # Randomize
    continuous_vars = list(cont2logic.keys())
    random.shuffle(continuous_vars)
    co_occurrences = list(logic2cont.values())
    random.shuffle(co_occurrences)

    # Construct int_tree
    primal = create_interaction_graph_from_literals(continuous_vars, co_occurrences, True, False)
    int_factory = IntTreeFactory(primal)
    primal.compute_fills()
    while primal.nb_fills() > 0:
        minfills = primal.get_minfills()
        minfills = int_factory.get_least_depth_increase(minfills)  # balance
        minfills = primal.get_lowest_future_minfill(minfills)  # balance
        int_factory.add_node(minfills[0])
        primal.remove_and_process_node(minfills[0])

    # Randomize some more
    logic_variables = list(logic2cont.keys())
    random.shuffle(logic_variables)

    # Construct vtree
    int_tree = int_factory.get_int_tree()
    if int_tree is not None:
        return int_tree.create_vtree(set(logic_variables), logic2cont)
    else:
        return balanced(literals)


def bottomup_minfill(literals: LiteralInfo) -> Vtree:
    """
    Create a vtree by using a min-fill approach to first construct an integration tree (not necessarily a line).
    :param literals: The context to create a vtree for.
    :return: A vtree based on a min-fill ordering.
    """
    logic2cont, cont2logic = conversion_tables(literals)
    primal = create_interaction_graph_from_literals(cont2logic.keys(), logic2cont.values(), True, False)
    int_factory = IntTreeFactory(primal)

    primal.compute_fills()
    while primal.nb_fills() > 0:
        minfills = primal.get_minfills()
        #minfills = int_factory.get_least_depth_increase(minfills)
        #minfills = primal.get_lowest_future_minfill(minfills)
        var_index = random.randint(0, len(minfills)-1)  # required to simulate min-fill
        int_factory.add_node(minfills[var_index])
        primal.remove_and_process_node(minfills[var_index])
    return int_factory.get_int_tree().create_vtree(logic2cont.keys(), logic2cont)


def bottomup_minfill_shuffle(seed, literals: LiteralInfo) -> Vtree:
    """
    Create a vtree by using a min-fill approach but shuffling the input order of the literals using the given seed.
    :param seed: The seed to use for the shuffling of the literals (random.seed(seed))
    :param literals: The context to create a vtree for.
    :return: A vtree based on a min-fill ordering.
    """
    random.seed(a=seed)
    logic2cont, cont2logic = conversion_tables(literals)
    continuous_vars = list(cont2logic.keys())
    random.shuffle(continuous_vars)
    co_occurrences = list(logic2cont.values())
    random.shuffle(co_occurrences)
    primal = create_interaction_graph_from_literals(continuous_vars, co_occurrences, True, False)
    int_factory = IntTreeFactory(primal)

    primal.compute_fills()
    while primal.nb_fills() > 0:
        minfills = primal.get_minfills()
        #minfills = int_factory.get_least_depth_increase(minfills)
        #minfills = primal.get_lowest_future_minfill(minfills)
        var_index = random.randint(0, len(minfills)-1)
        int_factory.add_node(minfills[var_index])
        primal.remove_and_process_node(minfills[var_index])
    logic_variables = list(logic2cont.keys())
    random.shuffle(logic_variables)
    result = int_factory.get_int_tree().create_vtree(set(logic_variables), logic2cont)
    return result


def bottomup_minfill_line_shuffle(seed, literals: LiteralInfo) -> Vtree:
    """
    Create a vtree by using a min-fill approach to first construct a variable ordering (a line).
    The vtree construction will shuffle the literal input order using the given seed.
    :param seed: The seed to use for the random input (random.seed(seed))
    :param literals: The context to create a vtree for.
    :return: A vtree with a line variable integration ordering.
    """
    random.seed(a=seed)
    logic2cont, cont2logic = conversion_tables(literals)
    continuous_vars = list(cont2logic.keys())
    random.shuffle(continuous_vars)
    co_occurrences = list(logic2cont.values())
    random.shuffle(co_occurrences)
    primal = create_interaction_graph_from_literals(continuous_vars, co_occurrences, True, False)

    primal.compute_fills()
    minfills = primal.get_minfills()
    int_tree = IntTreeVar(minfills[0])
    while primal.nb_fills() > 0:
        minfills = primal.get_minfills()
        #minfills = int_factory.get_least_depth_increase(minfills)
        #minfills = primal.get_lowest_future_minfill(minfills)
        var_index = random.randint(0, len(minfills)-1)
        int_tree = IntTreeLine(minfills[var_index], int_tree)
        primal.remove_and_process_node(minfills[var_index])

    logic_variables = list(logic2cont.keys())
    random.shuffle(logic_variables)
    result = int_tree.create_vtree(set(logic_variables), logic2cont)
    return result


def bottomup_mindegree(literals: LiteralInfo, balanced=True) -> Vtree:
    """
    Create a vtree by using a min-degree approach.
    :param literals: The context to create a vtree for.
    :param balanced: When true, from all mindegree nodes, the one that least increases the integration tree depth is
    prioritised.
    :return: A vtree based on a balanced min-degree ordering.
    """
    logic2cont, cont2logic = conversion_tables(literals)
    primal = create_interaction_graph_from_literals(cont2logic.keys(), logic2cont.values(), False, True)
    int_factory = IntTreeFactory(primal)

    primal.compute_degrees()
    while primal.nb_degrees() > 0:
        mindegrees = primal.get_mindegrees()
        if balanced:
            mindegrees = int_factory.get_least_depth_increase(mindegrees)  # balanced
        int_factory.add_node(mindegrees[0])
        primal.remove_node(mindegrees[0])
    return int_factory.get_int_tree().create_vtree(logic2cont.keys(), logic2cont)


def bottomup_min_induced_width(literals: LiteralInfo, balanced=True) -> Vtree:
    """
    Create a vtree by using a min-induced-width approach.
    :param literals: The context to create a vtree for.
    :param balanced: When true, from all min-induced-width nodes, the one that least increases the integration tree
    depth is prioritised.
    :return: A vtree based on a balanced min-induced-width ordering.
    """
    logic2cont, cont2logic = conversion_tables(literals)
    primal = create_interaction_graph_from_literals(cont2logic.keys(), logic2cont.values(), False, True)
    int_factory = IntTreeFactory(primal)

    primal.compute_degrees()
    while primal.nb_degrees() > 0:
        mindegrees = primal.get_mindegrees()
        if balanced:
            mindegrees = int_factory.get_least_depth_increase(mindegrees)  # balanced
        int_factory.add_node(mindegrees[0])
        primal.remove_and_process_node(mindegrees[0])
    return int_factory.get_int_tree().create_vtree(logic2cont.keys(), logic2cont)

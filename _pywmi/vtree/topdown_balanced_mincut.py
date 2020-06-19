import math

from pywmi.engines.xsdd.literals import LiteralInfo
from pywmi.engines.xsdd.vtrees.vtree import Vtree, VtreeVar, VtreeSplit

from ..vtree import pyhypergraph
from ..vtree.topdown_mincut import conversion_tables, HyperEdgeContainer


def topdown_balanced_mincut_hg(literals: LiteralInfo, swap_part=0):
    logic2cont, cont2logic = conversion_tables(literals)
    logic2num, num2logic = literals.numbered, literals.inv_numbered

    #print("logic2cont %s" % logic2cont)

    def build_tree(logic_variables, continuous_variables, prev_overlap=set()):
        if len(logic_variables) == 1:
            a, = logic_variables
            return VtreeVar(a)
        elif len(logic_variables) == 2:
            a, b = logic_variables
            return VtreeSplit(VtreeVar(a), VtreeVar(b))

        # Collect hyperedges, connected and unconnected logic variables.
        edge_capacity = HyperEdgeContainer(0)
        connected = set()

        for cvar in (continuous_variables - prev_overlap):
            lvars = cont2logic[cvar] & logic_variables
            if len(lvars) > 1:
                edge_capacity[lvars] += 1
                connected |= lvars

        # print("splitting connected %s" % connected)
        # Perform cut to get left and right partition
        if len(connected) != 0:
            hg = pyhypergraph.HyperGraph(map(logic2num.get, connected))
            for i, (edge, capacity) in enumerate(edge_capacity):
                hg.add_edge(capacity, set(map(logic2num.get, edge)))
            left, right = hg.cut()

            if len(left) > len(right):
                left, right = right, left  # prefer right-heavy
            left_lvars = {num2logic[n] for n in left}
            right_lvars = {num2logic[n] for n in right}
        else:
            left_lvars, right_lvars = set(), set()

        # print("left_lvars %s" % left_lvars)
        # print("right lvars %s" % right_lvars)

        # Equally Divide the unconnected logical variables
        unconnected = list(logic_variables - connected)
        if len(unconnected) > 0:
            # TODO: Vincent: would it be more beneficial to condition on propositional as fast or late as possible such that only integration remains?
            # Add unconnected vars (somewhat balanced)
            if len(left_lvars) < len(right_lvars):
                too_little, too_many = left_lvars, right_lvars
            else:
                too_little, too_many = right_lvars, left_lvars
            needed_to_balance = min(len(too_many) - len(too_little), len(unconnected))
            too_little.update(unconnected[:needed_to_balance])
            del unconnected[:needed_to_balance]

            if len(unconnected) > 0:
                # Divide the remaining variables equally
                add_to_left = math.floor(len(unconnected)/2)
                left_lvars.update(unconnected[:add_to_left])
                right_lvars.update(unconnected[add_to_left:])


        # # TODO: Only for experimenting, remove in final version
        # if swap_part > 0 and (len(left_lvars) > 1 or len(right_lvars) > 1):
        #     for i in range(round(len(logic_variables)*swap_part)):
        #         if len(left_lvars) == 1 or (not len(right_lvars) == 1 and random.random() < 0.5):
        #             source, target = right_lvars, left_lvars
        #         else:
        #             source, target = left_lvars, right_lvars
        #         lit = random.choice(list(source))
        #         source.remove(lit)
        #         target.add(lit)

        left_cvars = set.union(*(logic2cont[lvar] for lvar in left_lvars)) & continuous_variables
        right_cvars = set.union(*(logic2cont[lvar] for lvar in right_lvars)) & continuous_variables
        overlap_cvars = left_cvars & right_cvars
        new_prev_overlap = prev_overlap | overlap_cvars

        if False:
            print("Spliting logical %s" % logic_variables)
            print("and continuous %s" % continuous_variables)
            print("into left:")
            print("\t logical: %s" % left_lvars)
            print("\t continu: %s" % left_cvars)
            print("into right:")
            print("\t logical: %s" % right_lvars)
            print("\t continu: %s" % right_cvars)
            print("With overlap: %s" % overlap_cvars)
            print("With overlap (excl. prev): %s" % (overlap_cvars - prev_overlap))
            print("")
        return VtreeSplit(build_tree(left_lvars, left_cvars, new_prev_overlap),
                          build_tree(right_lvars, right_cvars, new_prev_overlap))

    return build_tree(logic2cont.keys(), cont2logic.keys())


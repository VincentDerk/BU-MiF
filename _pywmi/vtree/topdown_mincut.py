
from pathlib import Path
from collections import defaultdict
import random
import math

from pywmi.engines.xsdd.literals import LiteralInfo
#from pywmi.engines.xsdd.vtrees.vtree import *
from pywmi.engines.xsdd.vtrees.vtree import VtreeVar, VtreeSplit
from pywmi.smt_math import LinearInequality

# For 'normal' graphs
import igraph

# Own hypergraph library (only use is for mincut)
# TODO: the reason why we need to do this weird manual import stuff
# is because cppimport is apparently not flexible enough in paths...
from cppimport.importer import *
filepath = str(Path(__file__).parent / "hypergraph.cpp")
module_data = setup_module_data("hypergraph", filepath)
if not check_checksum(module_data):
    template_and_build(filepath, module_data)

from . import hypergraph


class EdgeContainer:
    "Helper class to store information about (undirected) edges"

    def __init__(self, default_val=None):
        if default_val is not None:
            self.data = defaultdict(lambda: default_val)
        else:
            self.data = {}
    
    def _key(self, k):
        if k[1] < k[0]:
            return (k[1], k[0])
        return k

    def __getitem__(self, k):
        return self.data[self._key(k)]
    
    def __setitem__(self, k, v):
        self.data[self._key(k)] = v
    
    def __delitem__(self, k):
        del self.data[self._key(k)]
    
    def __iter__(self):
        return iter(self.data.items())

    def __len__(self):
        return len(self.data)
    

class HyperEdgeContainer(EdgeContainer):
    def _key(self, k):
        return frozenset(k)


def conversion_tables(literals: LiteralInfo):
    logic2cont = defaultdict(set)
    cont2logic = defaultdict(set)
    for formula, lit in literals.abstractions.items():
        cvars = set(LinearInequality.from_smt(formula).variables)
        logic2cont[lit] = cvars
        for cvar in cvars:
            cont2logic[cvar].add(lit)
    for var, lit in literals.booleans.items():
        if literals.labels and var in literals.labels:
            pos_val, neg_val = literals.labels[var]
            logic2cont[lit] = {s.symbol_name() for s in pos_val.get_free_variables()}
            logic2cont[lit] |= {s.symbol_name() for s in neg_val.get_free_variables()}
            for cvar in logic2cont[lit]:
                cont2logic[cvar].add(lit)
        else:
            logic2cont[lit] = set()
    return logic2cont, cont2logic


def topdown_mincut_hg(literals: LiteralInfo, swap_part=0):
    logic2cont, cont2logic = conversion_tables(literals)
    logic2num, num2logic = literals.numbered, literals.inv_numbered

    def build_tree(logic_variables, continuous_variables, prev_overlap=set()):
        if len(logic_variables) == 1:
            a, = logic_variables
            return VtreeVar(a)
        elif len(logic_variables) == 2:
            a, b = logic_variables
            return VtreeSplit(VtreeVar(a), VtreeVar(b))

        edge_capacity = HyperEdgeContainer(0)
        node2lvar = list(logic_variables)
        lvar2node = {lvar: i for i, lvar in enumerate(node2lvar)}

        # Encode formula's
        for cvar in (continuous_variables - prev_overlap):
            lvars = cont2logic[cvar] & logic_variables
            if len(lvars) > 1:
                edge_capacity[lvars] += 1

        hg = hypergraph.HyperGraph()
        connected = set()
        
        for i, (edge, capacity) in enumerate(edge_capacity):
            connected.update(edge)
            hg.add_edge(i, set(map(logic2num.__getitem__, edge)), capacity)

        cut = hg.mincut()
        left, right = cut.left, cut.right

        if len(cut.left) > len(cut.right):
            left, right = right, left  # prefer right-heavy

        left_lvars = {num2logic[n] for n in left}
        right_lvars = {num2logic[n] for n in right}

        unconnected = list(logic_variables - connected)
        if len(unconnected) > 0:
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
        
        # TODO: Only for experimenting, remove in final version
        if swap_part > 0 and (len(left_lvars) > 1 or len(right_lvars) > 1):
            for i in range(round(len(logic_variables)*swap_part)):
                if len(left_lvars) == 1 or (not len(right_lvars) == 1 and random.random() < 0.5):
                    source, target = right_lvars, left_lvars
                else:
                    source, target = left_lvars, right_lvars
                lit = random.choice(list(source))
                source.remove(lit)
                target.add(lit)

        left_cvars = set.union(*(logic2cont[lvar] for lvar in left_lvars)) & continuous_variables
        right_cvars = set.union(*(logic2cont[lvar] for lvar in right_lvars)) & continuous_variables
        overlap_cvars = left_cvars & right_cvars
        new_prev_overlap = prev_overlap | overlap_cvars

        # Debugging print statements
        # print("")
        # print("Spliting logical %s" % logic_variables)
        # print("and continuous %s" % continuous_variables)
        # print("into left:")
        # print("\t logical: %s" % left_lvars)
        # print("\t continu: %s" % left_cvars)
        # print("into right:")
        # print("\t logical: %s" % right_lvars)
        # print("\t continu: %s" % right_cvars)
        # print("With overlap: %s" % overlap_cvars)
        return VtreeSplit(build_tree(left_lvars, left_cvars, new_prev_overlap),
                          build_tree(right_lvars, right_cvars, new_prev_overlap))

    return build_tree(logic2cont.keys(), cont2logic.keys())


def create_hypergraph(literals: LiteralInfo):
    """ Utility function to create drawable hypergraphs """
    import hypernetx as hnx

    logic2cont, cont2logic = conversion_tables(literals)
    logic2num, num2logic = literals.numbered, literals.inv_numbered
    
    logic_variables = logic2cont.keys()
    continuous_variables = cont2logic.keys()
    
    edge_capacity = HyperEdgeContainer(0)
    node2lvar = list(logic_variables)
    lvar2node = {lvar: i for i, lvar in enumerate(node2lvar)}

    # Encode formula's
    for cvar in continuous_variables:
        lvars = cont2logic[cvar] & logic_variables
        if len(lvars) > 1:
            edge_capacity[lvars] += 1

    #hg = hypergraph.HyperGraph()
    edges = {}
        
    for i, (edge, capacity) in enumerate(edge_capacity):
        edges[i] = edge
        #hg.add_edge(i, set(map(logic2num.__getitem__, edge)), capacity)

    return hnx.Hypergraph(edges)


def topdown_mincut(literals: LiteralInfo):
    # WARNING: this is ... wrong (but generates pretty good solutions in practice)
    # For more info on why it is wrong, see notes. Short version, encoding is wrong
    # and it's (probably) impossible to find a working encoding.
    
    # Relative importance of an extra continuous var not being included in the overlap
    # versus a logic var not being balanced in the split
    overlap_vs_balance = 100000

    logic2cont, cont2logic = conversion_tables(literals)

    def build_tree(logic_variables, continuous_variables):
        if len(logic_variables) == 1:
            a, = logic_variables
            return VtreeVar(a)
        elif len(logic_variables) == 2:
            a, b = logic_variables
            return VtreeSplit(VtreeVar(a), VtreeVar(b))

        edge_capacity = EdgeContainer(0)
        node2lvar = list(logic_variables)
        lvar2node = {lvar: i for i, lvar in enumerate(node2lvar)}

        # Encode formula's
        for cvar in continuous_variables:
            lvars = cont2logic[cvar] & logic_variables
            # See notes why this is the way it is (and not a )
            if len(lvars) == 1:
                pass
            if len(lvars) == 2:
                a, b = lvars
                edge_capacity[(a, b)] += 2 * overlap_vs_balance
            else:
                # Actually, this code could be used for the above case as well
                lvars = list(lvars)
                for i in range(len(lvars)-1):
                    edge_capacity[(lvars[i], lvars[i+1])] += overlap_vs_balance
                edge_capacity[(lvars[-1], lvars[0])] += overlap_vs_balance
        
        # Encode preference for balance
        for i, a in enumerate(node2lvar):
            for b in node2lvar[i+1:]:
                edge_capacity[(a, b)] += -1
        # TODO?

        graph = igraph.Graph()
        graph.add_vertices(len(node2lvar))
        
        for (a, b), capacity in edge_capacity:
            graph.add_edge(lvar2node[a], lvar2node[b], capacity=capacity)

        cut = graph.mincut(capacity='capacity')

        #best_cut_balance = -1
        #for i in range(len(logic_variables)):
        #    for j in range(i+1, len(logic_variables)):
        #        graph.all_st_mincuts(i, j, capacity='capacity')

        left, right = cut.partition
        if len(left) > len(right):
            left, right = right, left  # prefer right-heavy
        
        left_lvars = {node2lvar[n] for n in left}
        right_lvars = {node2lvar[n] for n in right}

        left_cvars = set.union(*(logic2cont[lvar] for lvar in left_lvars)) & continuous_variables
        right_cvars = set.union(*(logic2cont[lvar] for lvar in right_lvars)) & continuous_variables
        
        return VtreeSplit(build_tree(left_lvars, left_cvars), 
                          build_tree(right_lvars, right_cvars))

    return build_tree(logic2cont.keys(), cont2logic.keys())



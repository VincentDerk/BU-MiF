
import random

from pywmi.engines.xsdd.literals import LiteralInfo
from pywmi.engines.xsdd.vtrees.vtree import VtreeVar, VtreeSplit, Vtree
from .topdown_mincut import topdown_mincut_hg


def pure_random(literals: LiteralInfo):
    def build_tree(lits):
        if len(lits) == 1:
            return VtreeVar(lits.pop())
        elif len(lits) == 2:
            return VtreeSplit(VtreeVar(lits.pop()), VtreeVar(lits.pop()))
        else:
            while True:
                split = [random.random() < 0.5 for i in range(len(lits))]
                if any(split) and not all(split):
                    left = {l for l, s in zip(lits, split) if s}
                    right = {l for l, s in zip(lits, split) if not s}
                    return VtreeSplit(build_tree(left), build_tree(right))
    
    all_literals = set(literals)
    return build_tree(all_literals)


def random_balanced(literals: LiteralInfo):
    l = list(literals)
    random.shuffle(l)
    return Vtree.create_balanced(l, True)


def random_rightlinear(literals: LiteralInfo):
    l = list(literals)
    random.shuffle(l)
    return Vtree.create_rightlinear(l)


def random_leftlinear(literals: LiteralInfo):
    l = list(literals)
    random.shuffle(l)
    return Vtree.create_leftlinear(l)


def swap_tmc(swap_part):
    """ Helper function to create kinda-random tmc heuristics """
    def tmc(literals, _swap_part=swap_part):
        return topdown_mincut_hg(literals, swap_part=_swap_part)
    return tmc


def seeded(seed, strat):
    def seeded_strat(literals: LiteralInfo, __seed=seed, __strat=strat):
        random.seed(__seed)
        return __strat(literals)
    return seeded_strat

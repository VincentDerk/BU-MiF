
from pywmi.engines.xsdd.literals import LiteralInfo, extract_and_replace_literals
import matplotlib.pyplot as plt

import hypernetx as hnx
import tempfile
import pydot
import networkx
from networkx.drawing.nx_agraph import write_dot, graphviz_layout

from ..problems import make_from_graph
from ..vtree.topdown_mincut import create_hypergraph, conversion_tables, VtreeSplit


def shrink(pos, fact_x, fact_y=None):
    """ Shrink networkx positionings """
    if fact_y is None:
        fact_y = fact_x
    return {i: (x*fact_x, y*fact_y) for i, (x, y) in pos.items()}


def plot_primal_and_hyper(pg):
    pg_nx = networkx.Graph(pg.get_edgelist())
    
    density = make_from_graph(pg)
    support = density.support
    _, _, lit = extract_and_replace_literals(support)
    hg = create_hypergraph(lit)
    
    fig, (pg_ax, hg_ax) = plt.subplots(1, 2, figsize=(10, 5))

    pg_ax.set_title("Primal graph")
    dot_pos = shrink(graphviz_layout(pg_nx, prog='dot'), 0.004, 0.002)
    networkx.draw(pg_nx, with_labels=True, node_color='lightgrey', node_size=1500, width=3, font_size=24,
                  pos=dot_pos, ax=pg_ax)

    hg_ax.set_title("Hypergraph")
    hg_ax.axis('off')
    hnx.drawing.draw(hg, with_node_labels=False, ax=hg_ax)
    
    return fig


def plot_hyper(density, name, ax=None):
    support = density.support
    _, _, lit = extract_and_replace_literals(support)
    hg = create_hypergraph(lit)
    
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(6, 6))
    else:
        fig = None
    if name is not None:
        ax.set_title(name)
    ax.axis('off')
    hnx.drawing.draw(hg, with_node_labels=False, ax=ax)
    return fig


def label_vtree(vtree, lit, ignore=None):
    if ignore is None:
        ignore = set()
    logic2cont, cont2logic = conversion_tables(lit)
    if isinstance(vtree, VtreeSplit):
        left_vars = set().union(*(logic2cont[a.var] for a in vtree.primes.all_leaves()))
        right_vars = set().union(*(logic2cont[a.var] for a in vtree.subs.all_leaves()))
        
        intersection = (left_vars & right_vars) - ignore
        
        labels = {str(id(vtree)): ", ".join(map(str, intersection))}
        labels.update(label_vtree(vtree.primes, lit, ignore | intersection))
        labels.update(label_vtree(vtree.subs, lit, ignore | intersection))
        return labels
    else:
        vars_left = logic2cont[vtree.var] - ignore
        return {vtree.var: ", ".join(map(str, vars_left))}

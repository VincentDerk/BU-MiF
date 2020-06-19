
import pydot
import tempfile
import sys
import os

__all__ = ('to_pydot', 'view_dot', 'view_svg')


# Added utility
# =============

def invert_dot_edges(g):
    ig = type(g)(graph_name=g.get_name(), graph_type=g.get_type(), strict=g.get_strict(g))
    for n in g.get_nodes():
        ig.add_node(n)
    for e in g.get_edges():
        ig.add_edge(pydot.Edge(e.get_destination(), e.get_source(), **e.get_attributes()))
    return ig


pydot.Graph.invert = invert_dot_edges


# Viewing graph stuff
# ===================

def is_networkx(x):
    if 'networkx' in sys.modules:
        import networkx
        return isinstance(x, networkx.Graph)
    else:
        return False


def is_igraph(x):
    if 'igraph' in sys.modules:
        import igraph
        return isinstance(x, igraph.Graph)
    else:
        return False


def to_pydot(obj):
    """Specify either of the following options: a dot string (filename or text),
    a networkx graph, a pydot graph, an igraph graph, or a callable function.
    The function will be called with a filename to write it's dot output to."""
    
    if isinstance(obj, pydot.Graph):
        return obj
    elif isinstance(obj, str):
        if os.path.isfile(obj):
            return pydot.graph_from_dot_file(obj)[0]
        else:
            return pydot.graph_from_dot_data(obj)[0]
    elif is_networkx(obj):
        return nx_pydot.to_pydot(obj)
    elif is_igraph(obj):
        with tempfile.NamedTemporaryFile(mode='w+') as f:
            obj.write_dot(f.name)
            return pydot.graph_from_dot_file(f.name)[0]
    elif callable(obj):
        with tempfile.NamedTemporaryFile(mode='w+') as f:
            obj(f.name)
            return pydot.graph_from_dot_file(f.name)[0]
    elif hasattr(obj, 'to_dot') and callable(obj.to_dot):
        return to_pydot(obj.to_dot())
    else:
        raise TypeError("Can't convert to pydot")


def view_svg(svg, invert=False):
    from IPython.display import SVG, display
    svg = SVG(svg)
    if invert:
        # TODO: extremely hacky
        svg._data = svg._data[:4] + ' style="filter: invert(1)"' + svg._data[4:]
    display(svg)
        

def view_dot(obj, invert=True):
    """See documentation of `to_pydot`"""
    
    pydot_graph = to_pydot(obj)
    svg = pydot_graph.create_svg()
    view_svg(svg, invert=invert)


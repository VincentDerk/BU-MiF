
from collections import defaultdict
from functools import wraps

import time
import pydot

from pywmi.engines.xsdd import FactorizedXsddEngine as FXSDD
from pywmi.engines.xsdd.engine_factorized import FactorizedIntegrator
from pywmi.engines.xsdd.draw import sdd_to_dot, SddToDot, walk

from _pywmi.vtree.int_tree import vtree_to_int_tree
from _pywmi.vtree.primal import create_interaction_graph_from_literals
from _pywmi.vtree.topdown_mincut import conversion_tables


def timed(method):
    @wraps(method)
    def new_method(self, *args, __method=method, **kwargs):
        start = time.process_time()
        try:
            return __method(self, *args, **kwargs)
        finally:
            time_taken = (time.process_time() - start)
            self._times[__method.__name__].append(time_taken)
    return new_method


class MeasuredFactorizedIntegrator(FactorizedIntegrator):
    def __init__(self, *args, **kwargs):
        self._times = defaultdict(list)
        self._fint = defaultdict(list)
        self._notes = defaultdict(list)
        super().__init__(*args, **kwargs)

    def recursive(self, node, tags=None, cache=None, order=None):
        res = super().recursive(node, tags, cache, order)
        if tags is not None:
            self._notes[node.id].append("x: " + str([self.groups[v][0] for v in tags]))
            self._notes[node.id].append("vars: " + str([self.groups[t][0] for t in self.node_to_groups[node.id]]))
        return res

    def walk_and(self, prime, sub, tags, cache, order):
        start = time.process_time()
        try:
            if prime.is_false() or sub.is_false():
                return self.algebra.zero()

            tags_prime = self.node_to_groups[prime.id] & tags
            tags_sub = self.node_to_groups[sub.id] & tags
            tags_shared = tags_prime & tags_sub

            if False and order and len(tags_shared) > 0:
                first_index = min(order.index(tag) for tag in tags_shared)
                tags_shared |= (tags & set(order[first_index:]))
            prime_result = self.recursive(prime, tags_prime - tags_shared, cache, order)
            sub_result = self.recursive(sub, tags_sub - tags_shared, cache, order)

            vars = [e for e in order if e in tags_shared] if order else tags_shared

            expand = lambda T: [self.groups[t][0] for t in T]
            self._fint[(prime.id, sub.id)].append((
                expand(self.node_to_groups[prime.id]),
                expand(self.node_to_groups[sub.id]),
                expand(tags_prime),
                expand(tags_sub),
                expand(tags_shared),
                expand(vars)
            ))

            #logger.debug("node AND(%s, %s)", prime.id, sub.id)
            return self.integrate(self.algebra.times(prime_result, sub_result), vars)
        finally:
            time_taken = (time.process_time() - start)
            self._times[(prime.id, sub.id)].append(time_taken)


class MeasuredFXSDD(FXSDD):
    def __init__(self, *args, **kwargs):
        self._times = defaultdict(list)
        self._results = defaultdict(lambda: None)
        self._integrator = None
        super().__init__(*args, **kwargs)
    
    get_vtree = timed(FXSDD.get_vtree)
    #get_sdd = timed(FXSDD.get_sdd)
    compute_volume_for_piece = timed(FXSDD.compute_volume_for_piece)
    compute_volume = timed(FXSDD.compute_volume)

    def create_integrator(self, literals, group_to_vars_poly, node_to_groups):
        self._integrator = MeasuredFactorizedIntegrator(self.domain, literals, group_to_vars_poly, node_to_groups, self.algebra)
        return self._integrator

    def get_sdd(self, logic_support, literals, vtree):
        start = time.process_time()
        try:
            sdd = FXSDD.get_sdd(self, logic_support, literals, vtree)
        finally:
            time_taken = (time.process_time() - start)
            self._times['get_sdd'].append(time_taken)
        
        self._results['logic_support'] = logic_support
        self._results['literals'] = literals
        self._results['vtree'] = vtree
        self._results['sdd'] = sdd

        # Compute induced width and height of integration tree
        logic2cont, cont2logic = conversion_tables(literals)
        int_tree = vtree_to_int_tree(vtree, logic2cont)
        self._results['int_tree'] = int_tree
        self._results['depth'] = int_tree.depth()
        primal = create_interaction_graph_from_literals(cont2logic.keys(), logic2cont.values(), True, False)
        self._results['width'] = int_tree.get_induced_width(primal)

        return sdd
    
    def copy(self, *args, **kwargs):
        new_me = super().copy(*args, **kwargs)
        new_me._times = self._times
        new_me._results = self._results
        return new_me

    def sdd_to_dot(self):
        s = sdd_to_dot(self._results['sdd'], self._results['literals'], node_annotations=None, edge_annotations=None)
        return pydot.graph_from_dot_data(s)[0]
    
    def sdd_to_dot_fancy(self):
        node_annotations = {node_id: ("\\n" + "\\n".join(n)) for node_id, n in self._integrator._notes.items()}
        walker = FancySddToDot(self._integrator, self._results['literals'], node_annotations, None)
        _, nodes, edges, _node_id = walk(walker, self._results['sdd'])
        s = "digraph G {{\n{}\n{}\n}}".format("\n".join(nodes), "\n".join(edges))
        return pydot.graph_from_dot_data(s)[0]


class FancySddToDot(SddToDot):
    def __init__(self, integrator, *args, **kwargs):
        self.integrator = integrator
        super().__init__(*args, **kwargs)

    def walk_and(self, prime_result, sub_result, prime_node, sub_node):
        key = (prime_node.id, sub_node.id)
        vertex_id = self.get_id(key)
        label = "AND"
        if key in self.node_annotations:
            label += ": {}".format(self.node_annotations[key])
        label += f"\\ntimes: " + ", ".join(f"{t:.2f}" for t in self.integrator._times[key])
        label += "\\nvars_1, vars_2, x_1, x_2, x_s:"
        for x in self.integrator._fint[key]:
            label += f"\\n{x}"
        label += self.node_annotations.get(key, "")

        label_prime = self.edge_annotations.get((key, prime_result[3]), "")
        label_sub = self.edge_annotations.get((key, sub_result[3]), "")

        total_time = sum(self.integrator._times[key])
        from matplotlib.cm import get_cmap
        from matplotlib.colors import to_hex
        cmap = get_cmap('plasma_r')
        color = to_hex(cmap(total_time))  # in seconds, so times >= 1s are all same color

        return vertex_id, prime_result[1] | sub_result[1] | {
            f'{vertex_id} [label="{label}",shape=rectangle,color=white,style=filled,fillcolor="{color}"];'
        }, prime_result[2] | sub_result[2] | {
            f'{vertex_id} -> {prime_result[0]} [label="{label_prime}"];',
            f'{vertex_id} -> {sub_result[0]} [label="{label_sub}"];'
        }, key

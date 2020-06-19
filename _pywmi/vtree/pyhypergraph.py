"""
Contains a Hypergraph to use kahypar, a tool to heuristically compute a balanced mincut.
"""
import os
import kahypar as kahypar


class HyperGraph:

    def __init__(self, nodes):
        node_list = list(nodes)
        self.i2l = {index: node for index, node in enumerate(node_list)}
        self.l2i = {node: index for index, node in enumerate(node_list)}
        self.net_indices = [0]
        self.nets = []
        self.net_weights = []
        self.startEpsilon = 1.0
        self.epsilon = self.startEpsilon

    def _get_context(self):
        currdir = os.path.dirname(os.path.realpath(__file__))
        context = kahypar.Context()
        context.loadINIconfiguration(currdir + "/kahypar_config.ini")
        context.setK(k=2)
        context.setEpsilon(self.epsilon)
        context.suppressOutput(True)
        return context

    def set_epsilon(self, epsilon):
        self.epsilon = epsilon

    def add_edge(self, weight, lnodes):
        self.nets += self._to_inum(lnodes)
        self.net_indices.append(len(self.nets))
        self.net_weights.append(weight)

    def num_of_nodes(self):
        return len(self.i2l)

    def num_of_hyperedges(self):
        return len(self.net_indices) - 1

    def cut(self):
        context = self._get_context()
        num_nodes = self.num_of_nodes()
        node_weights = [1] * num_nodes
        k = 2
        # Debug messages
        # print("Creating hypergraph:")
        # print(f"\t num_nodes: {num_nodes}")
        # print(f"\t num_of_hyperedges: {self.num_of_hyperedges()}")
        # print(f"\t net_indices: {self.net_indices}")
        # print(f"\t nets: {self.nets}")
        # print(f"\t net_weights: {self.net_weights}")
        # print(f"\t node_weights: {node_weights}")
        hypergraph = kahypar.Hypergraph(num_nodes, self.num_of_hyperedges(), self.net_indices, self.nets, k,
                                        self.net_weights, node_weights)
        kahypar.partition(hypergraph, context)
        left_partition = [node for node in range(num_nodes) if hypergraph.blockID(node) == 0]
        right_partition = [node for node in range(num_nodes) if hypergraph.blockID(node) == 1]

        # print(left_partition)
        # print(right_partition)

        # IDK what triggers this but a partition can be empty. In that case, tighten the imbalance restriction and retry
        if len(left_partition) == 0 or len(right_partition) == 0:
            self.set_epsilon(self.epsilon/4)
            return self.cut()

        self.epsilon = self.startEpsilon
        return set(self._to_lnum(left_partition)), set(self._to_lnum(right_partition))

    def _to_lnum(self, inodes):
        if isinstance(inodes, int):
            return [self.i2l.get(inodes)]
        else:
            return map(self.i2l.get, inodes)

    def _to_inum(self, lnodes):
        if isinstance(lnodes, int):
            return [self.l2i.get(lnodes)]
        else:
            return map(self.l2i.get, lnodes)



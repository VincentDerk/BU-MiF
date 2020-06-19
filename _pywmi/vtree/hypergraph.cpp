/* 
 * Hypergraph Min Cut implementation by Evert Heylen
 * Based on "A simple hypergraph min cut algorithm" by R Klimmek and F Wagner (1996)
 */

/* Easy importing in Python through cppimport: 
<% 
setup_pybind11(cfg)
cfg['compiler_args'] = ['-O3', '-std=c++14', '-march=native']
%>
*/

#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <unordered_map>
#include <set>
#include <algorithm>  // set_intersection, set_difference
#include <iterator>  // inserter, iterator_traits
#include <limits>
#include <cstddef>
#include <math.h>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
namespace py = pybind11;


// Some type aliases
// -----------------

using EID = unsigned int;  // edge ID
using VID = unsigned int;  // vertex ID

using EdgeSet = std::set<EID>;
using VertexSet = std::set<VID>;



// Utilities
// ---------

template <typename T>
bool has_intersection(const std::set<T>& a, const std::set<T>& b) {
    typename std::set<T>::const_iterator i = a.begin();
    typename std::set<T>::const_iterator j = b.begin();
    while (i != a.end() and j != b.end()) {
        if (*i == *j) return true;
        else if (*i < *j) ++i;
        else ++j;
    }
    return false;
}

// https://stackoverflow.com/a/7667550, modified
template<typename iterator_type>
struct KeyIterator {
    using value_type = typename std::iterator_traits<iterator_type>::value_type::first_type;
    using difference_type = std::ptrdiff_t;
    using pointer = const value_type*;
    using reference = const value_type&;
    using iterator_category = typename std::iterator_traits<iterator_type>::iterator_category;
    
    iterator_type iterator;
    KeyIterator(iterator_type i) : iterator(i) {}
    value_type operator*() { return iterator->first; }
    KeyIterator& operator++() { ++iterator; return *this; }
    bool operator!=(const KeyIterator& right) const { return iterator != right.iterator; }
    
};

template<typename T>
KeyIterator<T> iter_keys(T i) {
    return KeyIterator<T>(i);
}


// Fibonacci heap based on https://github.com/beniz/fiboheap
// Modifications:
//   - roughly consistent format as rest of code
//   - get maximum key instead of minimum (including names)
//   - made Payload a type instead of void*
//   - extracted FibNode class outside FibHeap

template<typename T, typename Payload>
struct FibNode {
    FibNode(T k, const Payload& pl) : key(std::move(k)), mark(false), p(nullptr), left(nullptr), right(nullptr), child(nullptr), degree(-1), payload(pl) {}
    
    ~FibNode() {}
    
    T key;
    bool mark;
    FibNode* p;
    FibNode* left;
    FibNode* right;
    FibNode* child;
    int degree;
    Payload payload;
};


template<typename T, typename Payload, typename Comp = std::greater<T>>
struct FibHeap {
    using Node = FibNode<T, Payload>;
    
    FibHeap() : FibHeap(std::greater<T>()) {}
    FibHeap(Comp comp) : n(0), max(nullptr), comp(comp) {}
    
    ~FibHeap() {
        clear();
    }
    
    void clear() {
        // delete all nodes.
        delete_fibnodes(max);
        max = nullptr;
        n = 0;
    }
    
    void delete_fibnodes(Node *x) {
        if (!x) return;
        
        Node *cur = x;
        while (true) {
            if (cur->left && cur->left != x) {
                Node *tmp = cur;
                cur = cur->left;
                if (tmp->child)
                    delete_fibnodes(tmp->child);
                delete tmp;
            } else {
                if (cur->child) delete_fibnodes(cur->child);
                delete cur;
                break;
            }
        }
    }
    
    void insert(Node *x) {
        x->degree = 0;
        x->p = nullptr;
        x->child = nullptr;
        x->mark = false;
        if ( max == nullptr) {
            max = x->left = x->right = x;
        } else {
            max->left->right = x;
            x->left = max->left;
            max->left = x;
            x->right = max;
            if (comp(x->key, max->key)) {
                max = x;
            }
        }
        ++n;
    }

    Node* maximum() {
        return max;
    }
    
    static FibHeap* union_fibheap(FibHeap* H1, FibHeap* H2) {
        FibHeap* H = new FibHeap();
        H->max = H1->max;
        if (H->max != nullptr && H2->max != nullptr) {
            H->max->right->left = H2->max->left;
            H2->max->left->right = H->max->right;
            H->max->right = H2->max;
            H2->max->left = H->max;
        }
        
        if (H1->max == nullptr || (H2->max != nullptr && H1->comp(H2->max->key, H1->max->key))) {
            H->max = H2->max;
        }
        
        H->n = H1->n + H2->n;
        return H;
    }
    
    Node* extract_max() {
        Node *z, *x, *next;
        Node ** childList;
        
        z = max;
        if (z != nullptr) {
            x = z->child;
            if (x != nullptr) {
                childList = new Node*[z->degree];
                next = x;
                for (int i = 0; i < (int)z->degree; i++) {
                    childList[i] = next;
                    next = next->right;
                }
                for (int i = 0; i < (int)z->degree; i++) {
                    x = childList[i];
                    max->left->right = x;
                    x->left = max->left;
                    max->left = x;
                    x->right = max;
                    x->p = nullptr;
                }
                delete [] childList;
            }
            z->left->right = z->right;
            z->right->left = z->left;
            if (z == z->right) {
                max = nullptr;
            } else {
                max = z->right;
                consolidate();
            }
            n--;
        }
        return z;
    }
    
    void consolidate() {
        Node* w, * next, * x, * y, * temp;
        Node** A, ** rootList;
        // Max degree <= log base golden ratio of n
        int d, rootSize;
        int max_degree = static_cast<int>(floor(log(static_cast<double>(n))/log(static_cast<double>(1 + sqrt(static_cast<double>(5)))/2)));
        
        A = new Node*[max_degree+2]; // plus two both for indexing to max degree and so A[max_degree+1] == NIL
        std::fill_n(A, max_degree+2, nullptr);
        w = max;
        rootSize = 0;
        next = w;
        do {
            rootSize++;
            next = next->right;
        } while ( next != w );
        rootList = new Node*[rootSize];
        for (int i = 0; i < rootSize; i++) {
            rootList[i] = next;
            next = next->right;
        }
        for (int i = 0; i < rootSize; i++) {
            w = rootList[i];
            x = w;
            d = x->degree;
            while (A[d] != nullptr) {
                y = A[d];
                if (comp(y->key, x->key)) {
                    temp = x;
                    x = y;
                    y = temp;
                }
                fib_heap_link(y,x);
                A[d] = nullptr;
                d++;
            }
            A[d] = x;
        }
        delete [] rootList;
        max = nullptr;
        for ( int i = 0; i < max_degree+2; i++ ) {
            if ( A[i] != nullptr ) {
                if ( max == nullptr ) {
                    max = A[i]->left = A[i]->right = A[i];
                } else {
                    max->left->right = A[i];
                    A[i]->left = max->left;
                    max->left = A[i];
                    A[i]->right = max;
                    if ( comp(A[i]->key, max->key) ) {
                        max = A[i];
                    }
                }
            }
        }
        delete [] A;
    }
    
    void fib_heap_link(Node* y, Node* x) {
        
        y->left->right = y->right;
        y->right->left = y->left;
        
        if ( x->child != nullptr ) {
            x->child->left->right = y;
            y->left = x->child->left;
            x->child->left = y;
            y->right = x->child;
        } else {
            x->child = y;
            y->right = y;
            y->left = y;
        }
        y->p = x;
        x->degree++;
        y->mark = false;
    }
    
    void increase_key(Node* x, T k) {
        Node* y;
        
        if ( comp(x->key, k) ) {
            //std::cerr << "new key is smaller than current key\n";
            return;
        }
        x->key = std::move(k);
        y = x->p;
        if ( y != nullptr && comp(x->key, y->key) ) {
            cut(x,y);
            cascading_cut(y);
        }
        if ( comp(x->key, max->key) ) {
            max = x;
        }
    }
    
    void cut(Node* x, Node* y) {
        if ( x->right == x ) {
            y->child = nullptr;
        } else {
            x->right->left = x->left;
            x->left->right = x->right;
            if ( y->child == x ) {
                y->child = x->right;
            }
        }
        y->degree--;
        max->right->left = x;
        x->right = max->right;
        max->right = x;
        x->left = max;
        x->p = nullptr;
        x->mark = false;
    }
    
    void cascading_cut(Node* y) {
        Node* z;
        z = y->p;
        if ( z != nullptr ) {
            if ( y->mark == false ) {
                y->mark = true;
            } else {
                cut(y,z);
                cascading_cut(z);
            }
        }
    }
    
    void remove_fibnode(Node* x) {
        increase_key(x, std::numeric_limits<T>::max());
        Node *fn = extract_max();
        delete fn;
    }
    
    bool empty() const {
        return n == 0;
    }
    
    Node* top_node() {
        return maximum();
    }
    
    T& top() {
        return maximum()->key;
    }
    
    void pop() {
        if (empty()) return;
        Node *x = extract_max();
        if (x) delete x;
    }
    
    Node* push(T k, const Payload& pl) {
        Node *x = new Node(std::move(k), pl);
        insert(x);
        return x;
    }
    
    unsigned int size() {
        return (unsigned int) n;
    }
    
    int n;
    Node *max;
    Comp comp;
};



// Core classes
// ------------


struct HyperGraph;


struct Cut {
    int value;
    VertexSet left;
    VertexSet right;
    
    Cut(int v, VertexSet l, VertexSet r) : value(v), left(l), right(r) {}
    Cut(int v) : value(v) {}
    
    Cut unmerge(HyperGraph& G);
    
    size_t count_balance() const {
        return std::max(left.size(), right.size());
    }
    
    bool operator<(const Cut& other) const {
        return value < other.value or count_balance() < other.count_balance();
    }
    
    bool operator==(const Cut& other) const {
        return left == other.left and right == other.right;
    }
};


struct Edge {
    VertexSet vertices;
    int weight = 0;
    Edge(VertexSet vs, int w) : vertices(vs), weight(w) {}
    Edge() = default;
};


struct Vertex {
    EdgeSet edges;
    std::vector<VID> merged_with;
    Vertex(EdgeSet es) : edges(es) {}
    Vertex() = default;
};


struct HyperGraph {
    std::map<VID, Vertex> vertices;
    std::map<EID, Edge> edges;
    
    HyperGraph() {}
    
    void add_edge(EID e, const VertexSet& vs, int weight) {
        Edge& E = edges[e];
        E.vertices = vs;
        E.weight = weight;
        for (VID v : vs) {
            vertices[v].edges.insert(e);
        }
    }
    
    std::string description() {
        std::string s;
        for (auto& it : edges) {
            s += std::to_string(it.first) + " connects ";
            for (VID v : it.second.vertices) {
                s += std::to_string(v) + ", ";
            }
            s += " with weight " + std::to_string(it.second.weight) + "\n";
        }
        return s;
    }

    std::map<EID, VertexSet> get_edges() {
        std::map<EID, VertexSet> m;
        for (auto& it : edges) {
            m[it.first] = it.second.vertices;
        }
        return m;
    }
    
    Cut cut(const VertexSet& left) {
        VertexSet right;
        set_difference(iter_keys(vertices.begin()), iter_keys(vertices.end()),
                       left.begin(), left.end(),
                       std::inserter(right, right.begin()));
        
        int value = 0;
        for (auto& it : edges) {
            if (has_intersection(it.second.vertices, left) and has_intersection(it.second.vertices, right)) {
                value += it.second.weight;
            }
        }
        return Cut(value, left, right);
    }
    
    void merge(VID a, VID b) {
        // a will be kept
        // b will be merged into a
        Vertex& A = vertices[a];
        Vertex B = std::move(vertices[b]);
        A.merged_with.push_back(b);
        A.merged_with.insert(A.merged_with.end(), B.merged_with.begin(), B.merged_with.end());
        vertices.erase(b);
        
        for (EID e : B.edges) {
            Edge& E = edges[e];
            E.vertices.erase(b);
            E.vertices.insert(a);
            if (E.vertices.size() <= 1) {
                edges.erase(e);
            } else {
                A.edges.insert(e);
            }
        }
    }
};


Cut Cut::unmerge(HyperGraph& G) {
    Cut cut(value);
    for (VID l : left) {
        Vertex& vertex = G.vertices[l];
        cut.left.insert(l);
        cut.left.insert(vertex.merged_with.begin(), vertex.merged_with.end());
    }
    
    for (VID r : right) {
        Vertex& vertex = G.vertices[r];
        cut.right.insert(r);
        cut.right.insert(vertex.merged_with.begin(), vertex.merged_with.end());
    }
    
    return cut;
}


struct MinCut {
    using Heap = FibHeap<int, VID>;
    using Node = Heap::Node;
    
    Cut best_cut;
    VID a;
    HyperGraph& G;
    
    MinCut(HyperGraph& _G) : 
        best_cut(std::numeric_limits<int>::max()),
        a(_G.vertices.begin()->first),
        G(_G) {}
    
    void phase() {
        //std::cout << "\n-------------- PHASE, |V| = " << G.vertices.size() << " ------------------\n";
        //std::cout << G.description();
        
        // A = ... is virtual, not actually maintained
        Heap heap;
        std::unordered_map<VID, Node*> nodes;
        VertexSet marked;
        for (auto& it : G.vertices) {
            VID v = it.first;
            Node* n = heap.push(0, v);
            nodes[v] = n;
        }
        
        add_vertex_to_A(a, heap, nodes, marked);
        heap.remove_fibnode(nodes[a]);
        nodes.erase(a);
        
        VID added_before = 9999;
        VID added_last = a;
        
        for (size_t i=0; i<G.vertices.size()-1; i++) {
            // add to A the most tightly connected vertex with A
            
            Node* topnode = heap.top_node();
            VID mtc = topnode->payload;
            heap.pop();
            
            add_vertex_to_A(mtc, heap, nodes, marked);
            
            //std::cout << "Adding " << mtc << " to A\n";
            added_before = added_last;
            added_last = mtc;
        }
        
        Cut cut = G.cut({added_last});
        //std::cout << "Cut = " << cut.left.size() << " // " << cut.right.size() << "  value = " << cut.value << "\n";
        
        if (cut.value <= best_cut.value) {
            Cut um_cut = cut.unmerge(G);
            // Now also check balance
            if (um_cut < best_cut) {
                best_cut = std::move(um_cut);
                //std::cout << "--> new best cut with value " << best_cut.value << "\n";
            }
        }
        
        G.merge(added_before, added_last);
        //std::cout << "Merged " << added_before << " and " << added_last << "\n";
    }
    
    void add_vertex_to_A(VID v, Heap& heap, std::unordered_map<VID, Node*>& nodes, VertexSet& marked) {
        Vertex& V = G.vertices[v];
        for (EID e : V.edges) {
            if (marked.find(e) == marked.end()) {
                marked.insert(e);
                Edge& E = G.edges[e];
                for (VID u : G.edges[e].vertices) {
                    if (u != v) {
                        Node* n = nodes[u];
                        int w = n->key + E.weight;
                        heap.increase_key(n, w);
                    }
                }
            }
        }
    }
    
    void run() {
        while (G.vertices.size() > 1) {
            phase();
        }
    }
};



// Expose to Python
// ----------------

PYBIND11_MODULE(hypergraph, m) {
    py::class_<HyperGraph>(m, "HyperGraph")
        .def(py::init<>())
        .def("add_edge", &HyperGraph::add_edge)
        .def("cut", &HyperGraph::cut)
        .def("merge", &HyperGraph::merge)
        .def("mincut", [](HyperGraph& G) {
            MinCut mc(G);
            mc.run();
            return mc.best_cut;
        })
        .def("description", &HyperGraph::description)
        .def("get_edges", &HyperGraph::get_edges);
    
    py::class_<Cut>(m, "Cut")
        .def_readwrite("value", &Cut::value)
        .def_readwrite("left", &Cut::left)
        .def_readwrite("right", &Cut::right)
        .def("unmerge", &Cut::unmerge);
}

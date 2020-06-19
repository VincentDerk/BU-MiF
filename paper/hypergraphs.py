"""
hypergrahps.py - By Vincent Derkinderen based on Evert Heylen's master thesis work (2020 KU Leuven DTAI).
Plots the hypergraph for each problem (dual, xor, mutex, star, 3ary and path) for size n = 6 and a plot
containing all hypergraphs.
"""
from _pywmi.problems import *
from _pywmi.util.graphs import *

plt.style.use('default')

tpg_star_gen = lambda n: make_from_graph(tpg_star(n))
tpg_3ary_gen = lambda n: make_from_graph(tpg_3ary_tree(n))
tpg_path_gen = lambda n: make_from_graph(tpg_path(n))


# ALL
size = 6
problems = [('dual', dual),
            ('xor', xor),
            ('mutex', mutual_exclusive),
            ('pg-star', tpg_star_gen),
            ('pg-3ary', tpg_3ary_gen),
            ('pg-path', tpg_path_gen)]

fig, axes = plt.subplots(2, 3, figsize=(9, 6))
for i, (n, p) in enumerate(problems):
    name = f"{n}({size})"
    i1 = i // 3
    i2 = i % 3
    ax = axes[i1][i2]

    density = p(size)
    plot_hyper(density, name, ax)

fig.savefig('hg_all.pdf', bbox_inches='tight')


# Separate graphs
n = 6
hg_dual = dual(n)
hg_xor = xor(n)
hg_mutex = mutual_exclusive(n)
hg_star = tpg_star_gen(n)
hg_3ary = tpg_3ary_gen(n)
hg_path = tpg_path_gen(n)

fig = plot_hyper(hg_dual, " ")
fig.savefig("hg_dual.pdf", bbox_inches='tight')

fig = plot_hyper(hg_xor, " ")
fig.savefig("hg_xor.pdf", bbox_inches='tight')

fig = plot_hyper(hg_mutex, " ")
fig.savefig("hg_mutex.pdf", bbox_inches='tight')

fig = plot_hyper(hg_path, " ")
fig.savefig('hg_path.pdf', bbox_inches='tight')

fig = plot_hyper(hg_star, " ")
fig.savefig('hg_star.pdf', bbox_inches='tight')

fig = plot_hyper(hg_3ary, " ")
fig.savefig('hg_3ary.pdf', bbox_inches='tight')

# fig = plot_primal_and_hyper(pg_path)
# fig.savefig('7_pg_hg_path.pdf')

"""
random-visualization.py - KU Leuven, DTAI 2020

Used in UAI2020 paper, Ordering Variables for Weighted Model Integration.

Visualized the results in the /results/ folder, generated by random-experiments.py
"""
import pickle
import sys
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator

plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42

# PLOTTING CONFIG
markersize = 4
color_gen = (c for c in plt.rcParams['axes.prop_cycle'].by_key()['color'])
hg_mc_color = next(color_gen)
td_mif_color = next(color_gen)
bamif_color = next(color_gen)
balanced_color = next(color_gen)
right_linear_color = next(color_gen)

random_vtree_heuristics = [
    ('Balanced', balanced_color, 'o', 'dashed'),
    ('Right-linear', right_linear_color, 'x', 'dashed'),  # o, +, x, , . *
    ('HG-MC', hg_mc_color, '+', '-'),
    ('TD-MiF', td_mif_color, '.', '-'),
    ('BU-MiF', bamif_color, ',', '-'),
]

smi_name = 'SMI'
smi_color = next(color_gen)
smi_linestyle = 'dotted'
smi_marker = 'v'

opt_name = "Manual"
opt_color = next(color_gen)
opt_linestyle = 'dotted'
opt_marker = '^'

# DATA Top four figures
repeat_nb = 10
timeout_value = 30
max_n = 35
size_range = list(range(1, max_n+1))
heuristic_file_names = [
    'balanced',
    'right-linear',
    'hg-mc',
    'td-mif',
    'bamif',
]

click_exp_randomised = []
dual_exp_randomised = []
xor_exp_randomised = []
mutex_exp_randomised = []
for h_name in heuristic_file_names:
    with open(f"results/click_{h_name}_{max_n}.pl", 'rb') as f:
        click_exp_randomised.append(pickle.load(f))
    with open(f"results/dual_{h_name}_{max_n}.pl", 'rb') as f:
        dual_exp_randomised.append(pickle.load(f))
    with open(f"results/xor_{h_name}_{max_n}.pl", 'rb') as f:
        xor_exp_randomised.append(pickle.load(f))
    with open(f"results/mutex_{h_name}_{max_n}.pl", 'rb') as f:
        mutex_exp_randomised.append(pickle.load(f))


# Optimal
with open(f"results/click_opt_{max_n}.pl", 'rb') as f:
    click_exp_opt = pickle.load(f)
with open(f"results/dual_opt_{max_n}.pl", 'rb') as f:
    dual_exp_opt = pickle.load(f)
with open(f"results/xor_opt_{max_n}.pl", 'rb') as f:
    xor_exp_opt = pickle.load(f)
with open(f"results/mutex_opt_{max_n}.pl", 'rb') as f:
    mutex_exp_opt = pickle.load(f)

randomised_data = [
    dual_exp_randomised,
    xor_exp_randomised,
    mutex_exp_randomised,
    click_exp_randomised,
]

optimal_data = [
    dual_exp_opt,
    xor_exp_opt,
    mutex_exp_opt,
    click_exp_opt,
]

problem_names = [
    "dual",
    "xor",
    "mutex",
    "click",
]

# PLOTTING First four figures

def extend_with(timings, timeout, repeat):
    if len(timings) >= repeat:
        return timings
    else:
        return timings + ([timeout] * repeat)


fig, axes = plt.subplots(1, 4, sharey='row')
fig.set_size_inches(12, 2.5)
fig.subplots_adjust(bottom=0.14, wspace=0.1, hspace=0.3)

for i, name in enumerate(problem_names):
    ax = axes[i]
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    # PyWMI Randomised
    for (strat_name, color, marker, linestyle), times in zip(random_vtree_heuristics, randomised_data[i]):
        # [np.percentile(time_list, 25) for time_list in times]
        total_times = [np.average(extend_with(time_list, timeout_value, repeat_nb)) for time_list in times]
        total_lower = [np.min(extend_with(time_list, timeout_value, repeat_nb)) for time_list in times]
        total_upper = [np.max(extend_with(time_list, timeout_value, repeat_nb)) if len(time_list) > 1 else timeout_value for time_list in times]
        sizes = size_range[:len(times)]
        #sizes = sizes[:min(len(sizes), 11)]
        #total_times = total_times[:len(sizes)]
        #total_lower = total_lower[:len(sizes)]
        #total_upper = total_upper[:len(sizes)]
        ax.plot(sizes, total_times, color=color, marker=marker, linestyle=linestyle, label=strat_name, markersize=markersize)
        ax.fill_between(sizes, total_lower, total_upper, facecolor=color, alpha=0.4)

    # Optimal
    total_times = optimal_data[i]
    sizes = size_range[:len(total_times)]
    if i == 3:
        ax.plot(sizes[:10], total_times[:10], color=opt_color, marker=opt_marker, linestyle=opt_linestyle, label=opt_name, markersize=markersize)
        ax.set_xticks(range(0, 11, 2)) #max(size_range) + 1, 5)) # range(0, 11, 2)
    else:
        ax.plot(sizes, total_times, color=opt_color, marker=opt_marker, linestyle=opt_linestyle, label=opt_name, markersize=markersize)
        ax.set_xticks(range(0, max(size_range) + 1, 5))

    ylabel = "Time (s)" if i == 0 else None
    ax.set_xlabel("Problem size (n)")
    ax.set_ylabel(ylabel)
    ax.set_title(f"{name}(n)")
#ax.legend(loc='upper center', ncol=len(random_vtree_heuristics) + 1, bbox_to_anchor=(0.5, 1.1), bbox_transform=fig.transFigure, frameon=False)
#ax.legend(loc='center right', ncol=1, bbox_to_anchor=(1.07, 0.5), bbox_transform=fig.transFigure, frameon=False)

fig.savefig('improvement-1.pdf', bbox_inches='tight')



##################### PART 2 ########################

# DATA Bottom three figures
timeout_value = 60
max_n = 40
size_range = list(range(1, max_n + 1))

star_exp_randomised = []
ary_exp_randomised = []
path_exp_randomised = []
for h_name in heuristic_file_names:
    with open(f"results/star_{h_name}_{max_n}.pl", 'rb') as f:
        star_exp_randomised.append(pickle.load(f))
    with open(f"results/3ary_{h_name}_{max_n}.pl", 'rb') as f:
        ary_exp_randomised.append(pickle.load(f))
    with open(f"results/path_{h_name}_{max_n}.pl", 'rb') as f:
        path_exp_randomised.append(pickle.load(f))

randomised_data = [
    star_exp_randomised,
    ary_exp_randomised,
    path_exp_randomised,
]


problem_names = [
    "star",
    "3ary",
    "path",
]


# Optimal
with open(f"results/star_opt_{max_n}.pl", 'rb') as f:
    star_exp_opt = pickle.load(f)
with open(f"results/3ary_opt_{max_n}.pl", 'rb') as f:
    ary_exp_opt = pickle.load(f)
with open(f"results/path_opt_{max_n}.pl", 'rb') as f:
    path_exp_opt = pickle.load(f)

optimal_data = [
    star_exp_opt,
    ary_exp_opt,
    path_exp_opt,
]

with open(f"results/star_smi_{max_n}.pl", "rb") as f:
    star_exp_pysmi = pickle.load(f)
with open(f"results/3ary_smi_{max_n}.pl", "rb") as f:
    ary_exp_pysmi = pickle.load(f)
with open(f"results/path_smi_{max_n}.pl", "rb") as f:
    path_exp_pysmi = pickle.load(f)

smi_data = [
    star_exp_pysmi,
    ary_exp_pysmi,
    path_exp_pysmi,
]

# PLOTTING Bottom three figures

fig, axes = plt.subplots(1, 4, sharex='row', sharey='row')
fig.set_size_inches(12, 2.5)
fig.subplots_adjust(bottom=0.14, wspace=0.1, hspace=0.3)

for i, name in enumerate(problem_names):
    ax = axes[i]
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    # Randomised
    for (strat_name, color, marker, linestyle), times in zip(random_vtree_heuristics, randomised_data[i]):
        total_times = [np.average(extend_with(time_list, timeout_value, repeat_nb)) for time_list in times]
        total_lower = [np.min(extend_with(time_list, timeout_value, repeat_nb)) for time_list in times]
        total_upper = [np.max(extend_with(time_list, timeout_value, repeat_nb)) if len(time_list) > 1 else timeout_value for time_list in times]
        sizes = size_range[:len(times)]
        ax.plot(sizes, total_times, color=color, marker=marker, linestyle=linestyle, label=strat_name, markersize=markersize)
        ax.fill_between(sizes, total_lower, total_upper, facecolor=color, alpha=0.4)

    # Optimal
    ax.plot([], [], color=opt_color, marker=opt_marker, linestyle=opt_linestyle, label=opt_name, markersize=markersize)
    # total_times = optimal_data[i]
    # sizes = size_range[:len(total_times)]
    # ax.plot(sizes, total_times, color=opt_color, marker=opt_marker, linestyle=opt_linestyle, label=opt_name, markersize=markersize)

    # PySMI
    total_times = smi_data[i]
    sizes = size_range[:len(total_times)]
    ax.plot(sizes, total_times, color=smi_color, marker=smi_marker, linestyle=smi_linestyle, label=smi_name, markersize=markersize)

    ylabel = "Time (s)" if i == 0 else None
    ax.set_xlabel("Problem size (n)")
    ax.set_xticks(range(0, max(size_range) + 1, 5))
    ax.set_ylabel(ylabel)
    ax.set_title(f"{name}(n)")

ax.legend(loc='center right', ncol=1,
          bbox_to_anchor=(0.85, 0.5), bbox_transform=fig.transFigure, frameon=False)

axes[3].axis('off')

filename = 'improvement-2'
fig.savefig(filename + '.pdf', bbox_inches='tight')

"""
random-experiments.py - KU Leuven, DTAI 2020

Used in UAI2020 paper, Ordering Variables for Weighted Model Integration.
Performed experiments:

* Run first four problems 10 times:
random-experiments.py -s all -p first -n 35 -t 30 -r 10

* Run last three problems 10 times:
random-experiments.py -s all -p second -n 40 -t 60 -r 10

* Run first four problems using the manually configured ordering (once)
random-experiments.py -s opt -p first -n 35 -t 30

* Run last three problems using SMI (once)
random-experiments.py -s smi -p second -n 40 -t 60


Use random-visualization.py to visualize the results stored in the /results/ folder
"""
from typing import Tuple

from _pywmi.vtree.bottomup_elimination import bottomup_balanced_minfill_shuffle as random_bamif
from _pywmi.vtree.topdown_elimination import topdown_minfill
from _pywmi.vtree.topdown_elimination import topdown_minfill_shuffle as random_td_minfill
from _pywmi.vtree.random_vtree import random_balanced
from _pywmi.vtree.bottomup_elimination import bottomup_minfill as minfill
from _pywmi.vtree.topdown_balanced_mincut import topdown_balanced_mincut_hg

from tqdm import tqdm
import pickle
import sys

from _pywmi.experiment import *
from _pywmi.problems import *
from _pywmi.util.experiment import *

from pywmi.engines.pyxadd.algebra import PyXaddAlgebra
from paper.experiment_utils import timed_pysmi, timed_pywmi
from paper.pysmi.graph2formula import igraph_to_tree

tpg_star_gen = lambda n: make_from_graph(tpg_star(n))
tpg_3ary_gen = lambda n: make_from_graph(tpg_3ary_tree(n))
tpg_path_gen = lambda n: make_from_graph(tpg_path(n))
tpg_star_smi_gen = lambda n: igraph_to_tree(tpg_star(n))
tpg_3ary_smi_gen = lambda n: igraph_to_tree(tpg_3ary_tree(n))
tpg_path_smi_gen = lambda n: igraph_to_tree(tpg_path(n))

# %%

heuristic_dict = {
    "balanced": [('balanced', random_balanced)],
    "td-mif": [('td-mif', random_td_minfill)],
    "hg-mc": [('hg-mc', topdown_balanced_mincut_hg)],
    "bamif": [('bamif', random_bamif)],
    "right-linear": [('right-linear', random_rightlinear)],
    "all": [('balanced', random_balanced),
            ('td-mif', random_td_minfill),
            ('hg-mc', topdown_balanced_mincut_hg),
            ('bamif', random_bamif),
            ('right-linear', random_rightlinear)],
    "temp": [
            ('hg-mc', topdown_balanced_mincut_hg),
            ('bamif', random_bamif),
            ('right-linear', random_rightlinear)]
}

problem_dict = {
    "click": [('click', click_graph)],
    "dual": [('dual', dual)],
    "xor": [('xor', xor)],
    "mutex": [('mutex', mutual_exclusive)],
    "star": [('star', tpg_star_gen)],
    "ary": [('3ary', tpg_3ary_gen)],
    "path": [('path', tpg_path_gen)],
    "all": [
        ('click', click_graph),
        ('dual', dual),
        ('xor', xor),
        ('mutex', mutual_exclusive),
        ('star', tpg_star_gen),
        ('3ary', tpg_3ary_gen),
        ('path', tpg_path_gen),
    ],
    "first": [
        ('click', click_graph),
        ('dual', dual),
        ('xor', xor),
        ('mutex', mutual_exclusive),
    ],
    "second": [
        ('star', tpg_star_gen),
        ('3ary', tpg_3ary_gen),
        ('path', tpg_path_gen),
    ]
}

# %%

sys.setrecursionlimit(10 ** 6)


def do_random_experiment(problem_gen, size_range, strat, nb_repeats, filename):
    random.seed(a=1337)
    random_seeds = [random.randint(0, 21470000000) for i in range(nb_repeats)]

    timings = []
    # [n x results]
    for i in tqdm(range(nb_repeats)):
        random.seed(a=random_seeds[i])
        results, total_times, _ = timed_pywmi(
            algebra=lambda: PyXaddAlgebra(reduce_strategy=PyXaddAlgebra.FULL_REDUCE),
            problem_generator=problem_gen,
            size_range=size_range,
            vtree_strategy=strat,
            verbose=False,
            ordered=False)

        for n_index, time in enumerate(total_times):
            while len(timings) < n_index + 1:
                timings.append([])
            timings[n_index].append(time)
    if filename is not None:
        with open(filename, 'wb+') as f:
            pickle.dump(timings, f)
    return timings


def run_experiments(args, strategies: List[Tuple[str, any]], problems: List[Tuple[str, any]]):
    size_range = list(range(1, args.max_n + 1))
    nb = args.nb_of_repeats
    timeout_value = args.timeout
    env_timeout.set(timeout_value)

    for (strat_name, strat) in strategies:
        for (prob_name, problem_gen) in tqdm(problems):
            filename = f"results/{prob_name}_{strat_name}_{args.max_n}.pl"
            do_random_experiment(problem_gen, size_range, strat, nb, filename=filename)
            create_config_file(filename, args)


def run_optimal(args):
    size_range = list(range(1, args.max_n + 1))
    timeout_value = args.timeout
    env_timeout.set(timeout_value)
    problems = problem_dict.get(args.problems, [])
    for prob_name, problem_gen in tqdm(problems):
        results, total_times, _ = timed_pywmi(
            algebra=lambda: PyXaddAlgebra(reduce_strategy=PyXaddAlgebra.FULL_REDUCE),
            problem_generator=problem_gen,
            size_range=size_range,
            vtree_strategy=balanced,
            verbose=False,
            ordered=True)
        filename = f"results/{prob_name}_opt_{args.max_n}.pl"
        print("total_times")
        print(total_times)
        with open(filename, 'wb+') as f:
            pickle.dump(total_times, f)


def run_smi_experiment(args):
    timeout_value = args.timeout
    env_timeout.set(timeout_value)
    size_range = list(range(1, args.max_n + 1))
    smi_problem_dict = problem_dict.copy()
    smi_problem_dict['all'] = [('star', tpg_star_smi_gen), ('3ary', tpg_3ary_smi_gen), ('path', tpg_path_smi_gen)]
    smi_problem_dict['second'] = [('star', tpg_star_smi_gen), ('3ary', tpg_3ary_smi_gen), ('path', tpg_path_smi_gen)]

    for prob_name, smi_problem_gen in tqdm(smi_problem_dict.get(args.problems, [])):
        results, timings = timed_pysmi(
            problem_generator=smi_problem_gen,
            size_range=size_range,
            verbose=False,
        )
        filename = f"results/{prob_name}_smi_{args.max_n}.pl"
        with open(filename, 'wb+') as f:
            pickle.dump(timings, f)
        create_config_file(filename, args)


def create_config_file(filename, args):
    with open(filename.replace(".pl", ".txt"), 'w+') as f:
        f.write(f"{filename}\n")
        f.write(f"problems: \t {args.problems}\n")
        f.write(f"heuristic: \t{args.heuristic}\n")
        f.write(f"repeat: \t {args.nb_of_repeats}\n")
        f.write(f"timeout: \t {args.timeout}\n")
        f.write(f"max_n: \t {args.max_n}\n")


def main(argv):
    if not os.path.exists("results/"):
        os.makedirs("./results/")

    args = argparser().parse_args(argv)

    if args.heuristic == 'smi':
        run_smi_experiment(args)
    elif args.heuristic == 'opt':
        run_optimal(args)
    else:
        run_experiments(args, heuristic_dict.get(args.heuristic, []), problem_dict.get(args.problems, []))


def argparser():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--strategy",
        "-s",
        dest="heuristic",
        choices=["all", "temp", "balanced", "td-mif", "smi", "hg-mc", "bamif", "right-linear", "opt"],
        default="all",
        help="vtree strategy heuristic to use.",
    )
    parser.add_argument(
        "--problem",
        "-p",
        dest="problems",
        choices=problem_dict.keys(),
        default="all",
        help="Problems to test.",
    )
    parser.add_argument(
        "--timeout",
        "-t",
        dest="timeout",
        type=int,
        default="60",
        help="The timeout value",
    )
    parser.add_argument(
        "--repeat",
        "-r",
        dest="nb_of_repeats",
        type=int,
        default="10",
        help="The number of times to repeat",
    )
    parser.add_argument(
        "--n",
        "-n",
        dest="max_n",
        type=int,
        default="40",
        help="The maximum n",
    )
    return parser


if __name__ == "__main__":
    main(sys.argv[1:])


import random

from .vtree import *
from .xsdd import MeasuredFXSDD
from .util.color import get_color
from .util.experiment import *

from pywmi.engines.algebraic_backend import PSIAlgebra


def compute(density, vtree_strategy, algebra, ordered=True, extra_opts={}):
    mfxsdd = MeasuredFXSDD(density.domain, density.support, density.weight,
                           algebra=algebra, vtree_strategy=vtree_strategy, **extra_opts)
    res = mfxsdd.compute_volume(add_bounds=False)  # should be part of density already
    return res, mfxsdd._times


@experiment_outputs(['total_time', 'vtree_time'], proc=True)
def time_pywmi(problem_generator, size, vtree_strategy, algebra=None, verbose=True, ordered=True):
    density = problem_generator(size)
    if algebra is None:
        algebra = PSIAlgebra
    algebra_instance = algebra()
    res, times = compute(density, vtree_strategy, algebra_instance, extra_opts={"ordered": ordered})
    total_time = max(times['compute_volume'])  # possible recursion
    vtree_time = sum(times['get_vtree'])
    if verbose:
        print(f"Computing for {problem_generator.__name__}, size {size}, strategy {vtree_strategy.__name__}, algebra {algebra_instance}, ordered {ordered}")
        print(f"  --> {len(times['compute_volume_for_piece'])} pieces, result = {res}, total time = {total_time}s, vtree time = {vtree_time}")
    return total_time, vtree_time


@experiment_params(['vtree_strategy', 'size'], time_pywmi)
class CompareStrategies:
    def plot(self, ax = None):
        if ax is None:
            from matplotlib import pyplot as plt
            fig, ax = plt.subplots()
        else:
            fig = None
        
        for strat, times in self.all_experiments():
            vtree_times = list(times.get_all_results('vtree_time'))
            total_times = list(times.get_all_results('total_time'))
            color = get_color(strat.__name__)
            sizes = times.values[:len(total_times)]
            ax.plot(sizes, total_times, color=color, marker='o', linestyle='-', label=strat.__name__)
            # no label to keep things tidy
            ax.plot(sizes, vtree_times, color=color, marker='o', linestyle='--')
        
        ax.set_title(f"Times for {self.inputs['problem_generator'].__name__}")
        ax.set_xlabel("Problem size")
        ax.set_ylabel("Time (s)")

        if fig is not None:
            fig.legend(bbox_to_anchor=(0.15, 0.85), loc='upper left')
            return fig


if __name__ == '__main__':
    import argparse
    from .problems import get_problem, problem_generators

    parser = argparse.ArgumentParser()
    parser.add_argument("problem_name", choices=problem_generators.keys())
    parser.add_argument("--maxsize", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=2.0)
    parser.add_argument("--seed", default=None)
    parser.add_argument("--plot", type=str, default=None)

    args = parser.parse_args()
    
    random.seed(args.seed)
    generator = get_problem(args.problem_name)
    
    with use_timeout(args.timeout):
        exp = CompareStrategies(
            problem_generator=generator,
            size=range(1, args.maxsize+1),
            vtree_strategy=[balanced, leftlinear, rightlinear, topdown_mincut_hg],
        )
    
    if args.plot:
        fig = exp.plot()
        fig.savefig(args.plot)



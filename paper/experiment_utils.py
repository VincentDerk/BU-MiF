import time
import traceback
from concurrent.futures import TimeoutError
from pebble import ProcessExpired

from pywmi import PSIAlgebra, PyXaddEngine

from _pywmi.util.experiment import env_timeout
from _pywmi.util.process import run_in_process
from _pywmi.xsdd import MeasuredFXSDD
from .pysmi.smi import SMI


def run_exp_in_process(function, inputs=None, timeout_value=None):
    if inputs is None:
        inputs = dict()
    try:
        return run_in_process(function, timeout=env_timeout.get(), **inputs).result(), None
    except TimeoutError as error:
        return timeout_value, error
    except ProcessExpired as error:
        return timeout_value, error
    except Exception as error:
        print("Raised exception with exitcode %s" % error)
        print(traceback.print_exc())
        return timeout_value, error


def compute_pywmi(density, vtree_strategy, algebra, extra_opts={}):
    mfxsdd = MeasuredFXSDD(density.domain, density.support, density.weight,
                           algebra=algebra, vtree_strategy=vtree_strategy, **extra_opts)

    def execute_pywmi(test=None):
        result = mfxsdd.compute_volume(add_bounds=False)
        return result, mfxsdd._times, mfxsdd._results['width'], mfxsdd._results['depth']

    (res, times, width, depth), error = run_exp_in_process(
        function=execute_pywmi,
        inputs=dict(),
        timeout_value=(None, None, None, None)
    )
    return res, times, width, depth, error


def timed_pywmi(problem_generator, size_range, vtree_strategy, algebra=None, verbose=True, ordered=True):
    results = []
    total_times = []
    vtree_times = []
    for size in size_range:
        density = problem_generator(size)
        if algebra is None:
            algebra = PSIAlgebra
        algebra_instance = algebra()
        res, times, width, depth, error = compute_pywmi(density, vtree_strategy, algebra_instance,
                                                        extra_opts={'ordered': ordered})

        if res is None:
            if isinstance(error, ProcessExpired):
                print("Experiment %s with size %s and strategy %s raised exitcode %s." %
                      (problem_generator, size, vtree_strategy, error.exitcode))
            break

        total_time = max(times['compute_volume'])  # possible recursion
        vtree_time = sum(times['get_vtree'])
        results.append(res)
        total_times.append(total_time)
        vtree_times.append(vtree_time)
        if verbose:
            print(
                f"Computing for {problem_generator.__name__}, size {size}, strategy {vtree_strategy.__name__}, algebra {algebra_instance}")
            print(
                f"  --> {len(times['compute_volume_for_piece'])} pieces, result = {res}, total time = {total_time}s, vtree time = {vtree_time}")

    return results, total_times, vtree_times


def timed_xadd_engine(problem_generator, size_range, reduce_strategy=None):
    """ Execute the problems problem_generator(n) for each n in size_range, using the PyXaddEngine. """
    total_times = []
    result = []

    for size in size_range:
        density = problem_generator(size)
        engine = PyXaddEngine(density.domain, density.support, density.weight, reduce_strategy=reduce_strategy)

        def execute_computation():
            starttime = time.time()
            result = engine.compute_volume(add_bounds=False)
            endtime = time.time()
            return result, (endtime - starttime)

        (res, runtime), error = run_exp_in_process(
            function=execute_computation,
            inputs=dict(),
            timeout_value=(None, None)
        )

        if res is None:
            if isinstance(error, ProcessExpired):
                print("Experiment %s with size %s on xaddEngine raised exitcode %s." %
                      (problem_generator, size, error.exitcode))
            break
        else:
            result.append(res)
            total_times.append(runtime)

    return result, total_times


def timed_pysmi(problem_generator, size_range, verbose=True):
    total_results = []
    total_times = []
    for size in size_range:
        stree = problem_generator(size)
        # formula = tree_to_formula(stree)
        # print(formula)

        def execute_pysmi():
            starttime = time.process_time()
            result = SMI.compute_mi(tree=stree)
            endtime = time.process_time()
            return result, (endtime - starttime)

        (result, total_time), error = run_exp_in_process(
            function=execute_pysmi,
            timeout_value=(None, None)
        )

        if verbose:
            print(f"Computing for {problem_generator.__name__}, size {size}")
            print(f"  -->result = {result}, total time = {total_time}s")

        if result is None:
            if isinstance(error, ProcessExpired):
                print(f"Experiment {problem_generator} with size {size} raised exitcode {error.exitcode}.")
            else:
                print(f"Experiment {problem_generator} with size {size} raised error {error}.")
            break
        total_results.append(result)
        total_times.append(total_time)

    return total_results, total_times

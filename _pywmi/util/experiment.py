
from typing import List, Callable, Dict, Any, Set
from dataclasses import dataclass, field
import inspect
from contextvars import *
from contextlib import contextmanager

from concurrent.futures import TimeoutError
from pebble import ProcessExpired

from .process import run_in_process


env_timeout = ContextVar('env_timeout', default=10)


@contextmanager
def use_timeout(t):
    token = env_timeout.set(t)
    try:
        yield t
    finally:
        env_timeout.reset(token)


@dataclass
class BaseExperimentSetup:
    #exp_class: type
    
    def required_inputs(self) -> Set[str]:
        raise NotImplemented
    
    def __call__(self, __cls=None, **kwargs):
        """Runs an experiment and returns it or calls 'mixin' on the given cls"""
        if __cls is not None:
            assert len(kwargs) == 0
            return self.mixin(__cls)
        exp = self.create(**kwargs)
        exp.run()
        return exp
    
    def mixin(self, cls, **kwargs):
        new_type = type(cls.__name__, (cls, self.exp_class), kwargs)
        self.exp_class = new_type
        return self


@dataclass
class BaseExperiment:
    setup: BaseExperimentSetup
    
    def is_ready(self) -> bool:
        return self.setup.required_inputs().issubset(set(self.inputs.keys()))
    
    def assert_is_ready(self):
        required = self.setup.required_inputs()
        provided = set(self.inputs.keys())
        required -= provided
        if len(required) != 0:
            raise Exception("Still need parameters " + ", ".join(map(repr, required)))
    
    def run(self):
        raise NotImplemented
    
    def had_timeout(self):
        raise NotImplemented
    
    def get_all_results(self, name):
        raise NotImplemented


@dataclass
class Experiment(BaseExperiment):
    inputs: Dict[str, Any]
    results: Dict[str, Any] = field(default_factory=dict)
    timeout: bool = field(default=False)
    exitcode: int = field(default=0)
    
    def run(self):
        self.assert_is_ready()
        if self.setup.separate_process:
            try:
                res_tuple = run_in_process(self.setup.function, timeout=env_timeout.get(), **self.inputs).result()
            except TimeoutError:
                res_tuple = (None,) * len(self.setup.results)  # TODO: this is pretty blunt
                self.timeout = True
            except ProcessExpired as error:  # exitcode -9: probably ran out of memory
                res_tuple = (None,) * len(self.setup.results)
                self.timeout = True
                self.exitcode = error.exitcode
                print("An experiment ran out of memory.")
            except Exception as error:
                res_tuple = (None,) * len(self.setup.results)
                self.timeout = True
                print("Error was raised:")
                print(error)
                print(error.with_traceback())

        else:
            res_tuple = self.setup.function(**self.inputs)
        if not isinstance(res_tuple, tuple):
            res_tuple = (res_tuple,)
        self.results = dict(zip(self.setup.results, res_tuple))
        
    def __str__(self):
        if self.is_ready():
            if len(self.results) == 0:
                status = 'ready'
            else:
                status = 'done'
        else:
            status = 'empty'
        return f"<Experiment {self.setup.function.__name__} : {status}>"
    
    __repr__ = __str__
    
    def had_timeout(self):
        return self.timeout
    
    def get_all_results(self, name):
        yield self.results[name]


@dataclass
class ExperimentSetup(BaseExperimentSetup):
    inputs: List[str]
    defaults: Dict[str, Any]
    results: List[str]
    function: Callable
    
    exp_class: type = field(default=Experiment)
    separate_process: bool = field(default=False)
    
    def required_inputs(self):
        return set(self.inputs) - self.defaults.keys()
        
    def create(self, **kwargs):
        inp = self.defaults.copy()
        inp.update(kwargs)
        exp = Experiment(self, kwargs)
        return exp

        
def experiment_outputs(results, proc=False):
    def make_experiment(f, results=list(results), separate_process=proc):
        sig = inspect.signature(f)
        inputs = []
        defaults = {}
        for name, param in sig.parameters.items():
            if param.default != inspect.Parameter.empty:
                defaults[name] = param.default
            inputs.append(name)
        return ExperimentSetup(inputs, defaults, results, f, separate_process=separate_process)
    return make_experiment
    


@dataclass
class ExperimentParam(BaseExperiment):
    values: List[Any]
    inputs: Dict[str, Any]
    results: List[Experiment] = field(default_factory=list)
    
    def run(self):
        self.results = []
        for v in self.values:
            exp = self.setup.child_exp.create(**{self.setup.input_name: v, **self.inputs})
            exp.run()
            self.results.append(exp)
            if self.setup.stop_on_timeout and exp.had_timeout():
                break
    
    def had_timeout(self):
        return any(exp.had_timeout() for exp in self.results)
    
    def get_experiment_for_value(self, val):
        i = self.values.index(val)
        return self.results[i]
    
    def get_all_results(self, name):
        for exp in self.results:
            yield from exp.get_all_results(name)
    
    def all_experiments(self):
        return zip(self.values, self.results)


@dataclass
class ExperimentParamSetup(BaseExperimentSetup):    
    input_name: str
    child_exp: BaseExperiment
        
    exp_class: type = field(default=ExperimentParam)
        
    stop_on_timeout: bool = field(default=False)
        
    def required_inputs(self):
        return self.child_exp.required_inputs() - {self.input_name}

    def create(self, **kwargs):
        values = list(kwargs.pop(self.input_name))
        return self.exp_class(self, values, kwargs)


def experiment_params(names, setup, stop_on_timeout_last=True):
    last = True  # reversed
    for name in reversed(names):
        setup = ExperimentParamSetup(name, setup, stop_on_timeout=(last and stop_on_timeout_last))
        last = False
    return setup


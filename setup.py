#!/usr/bin/env python

import os
import shutil
import sys

from setuptools import setup, find_packages, Command
from os import path

setup(name='pywmi_experiments',
      version='0.1',
      description='pywmi var order experiments',
      author='Evert Heylen & Vincent Derkinderen',
      packages=['_pywmi'], install_requires=['networkx==2.4',
                                             'numpy==1.17.4',
                                             'scipy==1.3.3',
                                             'pebble==4.4.0',
                                             'contextvars==2.4',
                                             'sortedcontainers==2.1.0',
                                             'sortedcollections==1.1.2',
                                             'tqdm==4.41.1',
                                             'matplotlib==3.1.2',
                                             'pysdd==0.2.9',
                                             'python-sat==0.1.5.dev3',
                                             'python-igraph==0.7.1.post6',
                                             'cppimport==18.11.8',
                                             'pydot==1.4.1']
      )
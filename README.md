# BU-MiF
The code used to conduct the experiments for the UAI2020 paper: "Ordering Variables for Weighted Model Integration".

Previous vtree heuristics did not take into account the continuous variables present in the inequalities. This code contains the heuristics contributed by the paper that do take this information into account, and try to create a vtree where the integration order is more optimal (minimising induced-width/depth).

## Instructions

The paper results can be produced by first running the experiments:

```bash
python3 ./paper/improvement-random/random-experiments.py -s all -p first -n 35 -t 30 -r 10
python3 ./paper/improvement-random/random-experiments.py -s all -p second -n 40 -t 60 -r 10
python3 ./paper/improvement-random/random-experiments.py -s opt -p first -n 35 -t 30
python3 ./paper/improvement-random/random-experiments.py -s smi -p second -n 40 -t 60
```

and then visualizing the results:

```bash
python3 ./paper/improvement-random/random-visualization.py
```

## Dependencies

In addition to the dependencies mentioned in setup.py, you need to install the following:

* PyWMI ([Main_factorized branch](https://github.com/weighted-model-integration/pywmi/tree/main_factorized))
* [KaHyPar](https://kahypar.org) 1.0.4 (TODO: Change installation instruction to install 1.0.4) Used for balanced min-cut.
```bash
python3 -m pip install --index-url https://pypi.org/simple/ --no-deps kahypar==1.0.4
```
* psipy (Instructions from [pywmi](https://github.com/weighted-model-integration/pywmi/blob/master/README.md))
    1. Install the dmd compiler v2.078.3
    2. git clone https://github.com/ariovistus/pyd.git
    3. cd pyd
    4. python setup.py install
    5. cd ../
    6. git clone --recursive https://github.com/ML-KULeuven/psipy.git
    7. cd ./psypi
    8. python ./psipy/build_psi.py
    9. python setup.py install
    10. Add the psi library to your path (command printed during the previous step) OR add a file called psipy.pth to your python distribution python/lib/python3.6/site-packages/ with the printed path as content. For example: `/home/vincent/psipy/build/lib.linux-x86_64-3.6`. The latter approach is recommended when for example using PyCharm and virtual environments.

## Authors

The following people have authored this code and the paper:
* [Vincent Derkinderen](https://github.com/VincentDerk), 
* [Evert Heylen](https://evertheylen.eu/), 
* [Pedro Zuidberg Dos Martires](https://pedrozudo.github.io/), 
* [Samuel Kolb](https://www.kuleuven.be/wieiswie/nl/person/00092538), 
* [Luc De Raedt](https://wms.cs.kuleuven.be/people/lucderaedt/)

You can direct any questions towards Vincent.

## License

Copyright 2020 KU Leuven, DTAI Research Group

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
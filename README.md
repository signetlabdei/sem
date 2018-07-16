# A Simulation Execution Manager for ns-3 #

[![Build Status](https://travis-ci.org/DvdMgr/sem.svg?branch=develop)](https://travis-ci.org/DvdMgr/sem)
[![codecov](https://codecov.io/gh/DvdMgr/sem/branch/develop/graph/badge.svg)](https://codecov.io/gh/DvdMgr/sem) [![Join the chat at https://gitter.im/ns-3-sem/Lobby](https://badges.gitter.im/ns-3-sem/Lobby.svg)](https://gitter.im/ns-3-sem/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

A Python library to perform multiple ns-3 script executions, manage
the results and collect them in processing-friendly data structures.

## Building the module ##

This module is developed using `pipenv` facilities. In order to manage
virtual environments and install dependencies, make sure `pipenv` is
installed. Typically, the following is enough:

```bash
pip install pipenv
```

From the project root, one can then install the package and the
requirements with the following:

```bash
pipenv install
```

If a development environment is also desired, the `Pipfile`'s
`dev-packages` can be installed by attaching the `--dev` flag to the
command above.

After this step, a sub-shell using the new virtual environment can be
created by calling:

```bash
pipenv shell
```

Now, a python REPL can be started to use the library interactively.

## ns-3-dev submodule ##

In order to execute the scripts in the `examples/` folder, it's possible to
populate the `ns-3-dev` git submodule:

```bash
git submodule init
git submodule update
```

Once this is done, the scripts in `examples/` can be directly run:

```bash
python examples/one-shot.py
```

## Documentation ##

Documentation can be built locally using the makefile's `docs` target.
The documentation of the current version of the package is also
available on [readthedocs][rtd].

## Authors ##

Davide Magrin

[rtd]: https://simulationexecutionmanager.readthedocs.io

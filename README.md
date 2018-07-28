# A Simulation Execution Manager for ns-3 #

[![Build Status](https://travis-ci.org/DvdMgr/sem.svg?branch=develop)](https://travis-ci.org/DvdMgr/sem)
[![codecov](https://codecov.io/gh/DvdMgr/sem/branch/develop/graph/badge.svg)](https://codecov.io/gh/DvdMgr/sem)
[![Join the chat at https://gitter.im/ns-3-sem/Lobby](https://badges.gitter.im/ns-3-sem/Lobby.svg)](https://gitter.im/ns-3-sem/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

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

## Running tests ##

Tests can be run, from the project root, using:

```bash
pytest --doctest-glob='*.rst' docs/
pytest -x -n 3 --doctest-modules --cov-report term --cov=sem/ ./tests
```

These two commands will run, respectively, all code contained in the `docs/`
folder and all tests, also measuring coverage and outputting it to the terminal.

Since we are mainly testing integration with ns-3, tests require frequent
copy+paste of folders, ns-3 compilations and simulation running. Because of
this, full tests may need up to 30 minutes to complete. Single test files can be
targeted, to achieve faster testing, by substituting `./tests` in the second
command with the path to the test file that needs to be run.

## ns-3-dev submodule ##

In order to execute the scripts in the `examples/` folder, it's possible to
populate the `ns-3-dev` git submodule:

```bash
git submodule update --init --recursive
```

Once this is done, the scripts in `examples/` can be directly run:

```bash
python examples/wifi_plotting_xarray.py
python examples/lorawan_parsing_xarray.py
```

## Troubleshooting ##

In case there are problems with the pandas installation (this will happen in
macos, for which no binaries are provide), use the following command for
installation (and see [this pandas
issue](https://github.com/pandas-dev/pandas/issues/20775) as a reference):

```bash
PIP_NO_BUILD_ISOLATION=false pipenv install
```

## Documentation ##

Documentation can be built locally using the makefile's `docs` target.
The documentation of the current version of the package is also
available on [readthedocs][rtd].

## Authors ##

Davide Magrin

[rtd]: https://simulationexecutionmanager.readthedocs.io

# A Simulation Execution Manager for ns-3 #

[![Build Status](https://travis-ci.org/signetlabdei/sem.svg?branch=master)](https://travis-ci.org/signetlabdei/sem)
[![codecov](https://codecov.io/gh/DvdMgr/sem/branch/develop/graph/badge.svg)](https://codecov.io/gh/signetlabdei/sem)
[![Join the chat at https://gitter.im/ns-3-sem/Lobby](https://badges.gitter.im/ns-3-sem/Lobby.svg)](https://gitter.im/ns-3-sem/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

This is a Python library to perform multiple ns-3 script executions, manage the
results and collect them in processing-friendly data structures. For complete
step-by-step usage and installation instructions, check out [readthedocs][rtd].

# Contributing #

If you want to contribute to sem development, first of all you'll need an
installation that allows you to modify the code, immediately see the results and
run tests.

## Building the module from scratch ##

This module is developed using
[`pipenv`](https://pipenv.readthedocs.io/en/latest/): in order to correctly
manage virtual environments and install dependencies, make sure it is installed.
Typically, the following is enough:

```bash
pip install -U pipenv
```

Note that, depending on the specifics of your python installation, you may need to add
`~/.local/bin` to your path. In case this is needed, `pip` should warn you
during installation.

Then, clone the repo (or your fork, by changing the url in the following
command), also getting the `ns-3` installations that are used for running
examples and tests:

```bash
git clone https://github.com/DvdMgr/sem
cd sem
git submodule update --init --recursive
```

From the project root, you can then install the package and the
requirements with the following:

```bash
pipenv install --dev
```

This will also get you a set of tools such as `sphinx`, `pygments` and `pytest`
that handle documentation and tests.

Finally, you can spawn a sub-shell using the new virtual environment by calling:

```bash
pipenv shell
```

Now, you can start a python REPL to use the library interactively, issue the
bash `sem` program, run tests and compile the documentation of your local copy
of sem.

## Running tests ##

This project uses the [`pytest`](https://docs.pytest.org/en/latest/) framework
for running tests. Tests can be run, from the project root, using:

```bash
python -m pytest --doctest-glob='*.rst' docs/
python -m pytest -x -n 3 --doctest-modules --cov-report term --cov=sem/ ./tests
```

These two commands will run, respectively, all code contained in the `docs/`
folder and all tests, also measuring coverage and outputting it to the terminal.

Since we are mainly testing integration with ns-3, tests require frequent
copying and pasting of folders, ns-3 compilations and simulation running.
Furthermore, documentation tests run all the examples in the documentation to
make sure the output is as expected. Because of this, full tests are far from
instantaneous. Single test files can be targeted, to achieve faster execution
times, by substituting `./tests` in the second command with the path to the test
file that needs to be run.

## Building the documentation ##

Documentation can be built locally using the makefile's `docs` target:

```bash
make docs
```

The documentation of the current version of the package is also available on
[readthedocs][rtd].

## Running examples ##

The scripts in `examples/` can be directly run:

```bash
python examples/wifi_plotting_xarray.py
python examples/lorawan_parsing_xarray.py
```

## Troubleshooting ##

In case there are problems with the `pandas` installation (this will happen in
macOS, for which no binaries are provided), use the following command for
installation (and see [this pandas
issue](https://github.com/pandas-dev/pandas/issues/20775) as a reference):

```bash
PIP_NO_BUILD_ISOLATION=false pipenv install
```

## Authors ##

Davide Magrin

[rtd]: https://simulationexecutionmanager.readthedocs.io

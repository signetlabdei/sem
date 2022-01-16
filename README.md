<p align="center">
  <img src="res/logo.png" width="200">
</p>

# A Simulation Execution Manager for ns-3 #

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/signetlabdei/sem/develop?urlpath=lab)

This is a Python library to perform multiple ns-3 script executions, manage the
results and collect them in processing-friendly data structures.

# How does this work? #

For complete step-by-step usage and installation instructions, check out
[our documentation][docs].

# How to cite us #

If you used SEM for your ns-3 analysis, please cite the following paper, both to
provide a reference and help others find out about this tool:

Davide Magrin, Dizhi Zhou, and Michele Zorzi. 2019. A Simulation Execution
Manager for ns-3: Encouraging reproducibility and simplifying statistical
analysis of ns-3 simulations. In Proceedings of the 22nd International ACM
Conference on Modeling, Analysis and Simulation of Wireless and Mobile Systems
(MSWIM '19). ACM, New York, NY, USA, 121-125. DOI:
https://doi.org/10.1145/3345768.3355942

# Contributing #

This section contains information on how to contribute to the project. If you
are only interested in using SEM, check out the [documentation][docs].

If you want to contribute to sem development, first of all you'll need
an installation that allows you to modify the code, immediately see
the results and run tests.

## Building the module from scratch ##

This module is developed using
[`poetry`](https://python-poetry.org/docs/): in order to correctly
manage virtual environments and install dependencies, make sure it is installed.
Typically, the following is enough:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Note that, if poetry's installer does not add poetry's path to your shell's startup file properly, you may need to add
`source $HOME/.poetry/env` to your startup file. You can tell that you need to add it if your shell cannot find the poetry command the next time you open a terminal window.

Then, clone the repo (or your fork, by changing the url in the following
command), also getting the `ns-3` installations that are used for running
examples and tests:

```bash
git clone https://github.com/signetlabdei/sem
cd sem
git submodule update --init --recursive
```

From the project root, you can then install the package and the
requirements with the following:

```bash
poetry install
```

This will also get you a set of tools such as `sphinx`, `pygments` and `pytest`
that handle documentation and tests.

Finally, you can spawn a sub-shell using the new virtual environment by calling:

```bash
poetry shell
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

## Running examples ##

The scripts in `examples/` can be directly run:

```bash
python examples/wifi_example.py
```

## Installing SEM in pip's editable mode ##

`pip` currently requires a `setup.py` file to install projects in editable mode.

As explained [here](https://github.com/python-poetry/poetry/issues/761), poetry
actually already generates a `setup.py`. After building the project, you can
extract the file from the archive using the following command:

``` bash
tar -xvf dist/*.tar.gz --wildcards --no-anchored '*/setup.py' --strip=1
```

After this step, it becomes possible to install SEM in editable mode.


## Authors ##

Davide Magrin

[docs]: https://signetlabdei.github.io/sem

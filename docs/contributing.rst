Contribution guidelines
=======================

This page contains various resources for those who want to get started
contributing code or documentation to SEM.

SEM installation for contributors
---------------------------------

Contributors interested in developing new functionalities, fixing bugs, running
tests and updating the documentation should use the following installation
method.

First of all, clone the Github repository:

.. code:: bash

  git clone https://github.com/signetlabdei/sem

This module is developed using pipenv_. In order to manage virtual
environments and install dependencies, make sure pipenv is installed. Typically,
the following is enough:

  .. _pipenv: https://docs.pipenv.org/

.. code:: bash

  pip install pipenv

From the project root, one can then install the sem package and the requirements
with the following:

.. code:: bash

  pipenv install --dev

After this step, a sub-shell using the new virtual environment can be created by
calling:

.. code:: bash

  pipenv shell

From here, the examples in `examples/` can be run and a python REPL can be
started to use the library interactively. Note that, since the sem package is
marked to be installed in editable mode in the Pipfile, changes to the `sem/`
subdirectory will be effective immediately, without requiring a new
installation.

Testing framework
-----------------

SEM uses pytest_ to perform testing. By installing with the procedure described
above, you should automatically download `pytest` and its `xdist` and `cov`
extensions, allowing to perform parallel testing and coverage.

.. _pytest: https://docs.pytest.org/en/latest/

Tests are contained in the `tests/` folder. Here, different files prefixed with
`test_` contain test cases for the various components of the library:

* `test_cli.py` uses `click` facilities to test the command line interface;
* `test_database.py` tests result insertion, querying and generally the
  `DatabaseManager` class;
* `test_examples.py` runs the examples contained in the `examples/` folder;
* `test_manager.py` tests the `CampaignManager` object, from creation to
  simulation running and exporting results;
* `test_runner.py` tests the `SimulationRunner` objects;
* `test_utils.py` tests the utilities provided in `sem/utils.py`

The `conftest` file, on the other hand, contains code that must be run before
each test execution (i.e., downloading and compiling ns-3) and fixtures_ (i.e.,
common data structures used by tests, like temporary folders containing ns-3
installations) that are shared between test files.

.. _fixtures: https://docs.pytest.org/en/latest/fixture.html

From the `pipenv` shell, at the project root, one can run the following command
to run tests for the whole library:

.. code:: bash

   py.test -x .

Tests contained in a single file or in a single function can also be run using
the following formats:

.. code:: bash

   py.test -x tests/test_cli.py
   py.test -x -s ''/home/davide/Work/sem/tests/test_cli.py::test_cli_workflow''

In the commands above, the -x flag ensures that tests will stop at the first
failure or error, while the -s flag disables standard output capturing by
pytest, allowing the library to print to standard output also when tests are
run. To perform testing in parallel via the `xdist` extension, add the -n N
flag, with N equal to the number of parallel processes that should be used.
Considered that most tests involve I/O, this speeds up testing considerably.
Coverage can be computed by adding the --cov=sem flag, and using
the --cov-report html flag will generate an html folder showing detailed
coverage information. Finally, docstring testing is supported through
the --doctest-modules flag.

The code contained in the documentation can be tested through the following
command:

.. code:: bash

   py.test --doctest-glob='*.rst' docs/

Typically, one would run tests on a single file while developing, and on the
whole suite before submitting a pull request. The final commands that should be
run before any pull request are the following:

.. code:: bash

   py.test --doctest-glob='*.rst' docs/
   py.test -x --cov=sem/ --cov-report html --doctest-modules

If both commands finish successfully, and if the new coverage percentage is not
lower than the previous one, the pull request should be ready for submission.

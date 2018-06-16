Installation
============

This module is developed using pipenv facilities. In order to manage virtual
environments and install dependencies, make sure pipenv is installed. Typically,
the following is enough::

  pip install pipenv

From the project root, one can then install the package and the requirements
with the following::

  pipenv install

If a development environment is also desired, the Pipfile's dev-packages can be
installed by attaching the --dev flag to the command above.

After this step, a sub-shell using the new virtual environment can be created by
calling::

  pipenv shell

From here, the examples in examples/ can be run and a python REPL can be started
to use the library interactively.

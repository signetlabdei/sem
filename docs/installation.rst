Installation
============

Via pip
-------

Since SEM is under active development, the recommended method to get all the
latest features is using pip to install directly from the develop branch of the
Github repository:

.. code:: bash

  pip install git+https://github.com/DvdMgr/sem.git@develop

Alternatively, the master branch is more stable but also offers fewer features:

.. code:: bash

  pip install git+https://github.com/DvdMgr/sem.git@master

Installing ns-3
---------------

An ns-3 installation is required to use SEM. Detailed setup instructions for
ns-3 are available here_, however, in most cases, cloning the ns-3 project is
enough to get started. The following command downloads the development version
of ns-3 to the ns-3-dev folder:

  .. _here: https://www.nsnam.org/wiki/Installation

.. code:: bash

  git clone https://github.com/nsnam/ns-3-dev-git ns-3-dev

SEM installation for contributors
---------------------------------

Contributors interested in developing new functionalities, fixing bugs, running
tests and updating the documentation should use the following installation
method.

First of all, clone the Github repository:

.. code:: bash

  git clone https://github.com/DvdMgr/sem

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

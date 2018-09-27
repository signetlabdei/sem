Installation
============

Via pip
-------

Since SEM is under active development, the recommended method to get all the
latest features is using pip to install directly from the develop branch of the
Github repository:

.. code:: bash

  pip3 install git+https://github.com/DvdMgr/sem.git@develop

This will install the sem package and its dependencies in your current python
library path. This same command can also be re-issued to update the library.

Alternatively, the master branch is more stable but also offers fewer features:

.. code:: bash

  pip3 install git+https://github.com/DvdMgr/sem.git@master

In any case, SEM can be removed from the system by issuing:

.. code:: bash

  pip3 uninstall sem

Installing ns-3
---------------

An ns-3 installation is required to use SEM. Detailed setup instructions for
ns-3 are available here_, however, in most cases, cloning the ns-3 project is
enough to get started. The following command downloads the development version
of ns-3 to the ns-3-dev folder:

  .. _here: https://www.nsnam.org/wiki/Installation

.. code:: bash

  git clone https://github.com/nsnam/ns-3-dev-git ns-3-dev

Optionally, from the `ns-3-dev` folder, one can then checkout a precise ns-3
release with the following command:

.. code:: bash

  git checkout ns-3.29

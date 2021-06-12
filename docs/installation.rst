Installation
============

Via pip
-------

You can easily install SEM using pip:

.. code:: bash

   pip3 install --user sem

To get the latest development version, install directly from the develop branch
of the Github repository:

.. code:: bash

  pip3 install --user -U https://github.com/signetlabdei/sem/archive/develop.zip

This will install the sem package and its dependencies in your current python
library path. This same command can also be re-issued to update the library.

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

  git checkout ns-3.33

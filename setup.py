# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['sem']

package_data = \
{'': ['*']}

install_requires = \
['click',
 'drmaa',
 'gitpython',
 'numpy',
 'pandas',
 'salib>=1.3.8,<2.0.0',
 'tinydb>=4.0.0,<5.0.0',
 'tqdm',
 'xarray']

entry_points = \
{'console_scripts': ['sem = sem:cli']}

setup_kwargs = {
    'name': 'sem',
    'version': '0.3.0',
    'description': 'A simulation execution manager for ns-3',
    'long_description': '<p align="center">\n  <img src="res/logo.png" width="200">\n</p>\n\n# A Simulation Execution Manager for ns-3 #\n\n[![Build Status](https://travis-ci.com/signetlabdei/sem.svg)](https://travis-ci.org/signetlabdei/sem)\n[![codecov](https://codecov.io/gh/signetlabdei/sem/branch/master/graph/badge.svg)](https://codecov.io/gh/signetlabdei/sem)\n[![Join the chat at https://gitter.im/ns-3-sem/Lobby](https://badges.gitter.im/ns-3-sem/Lobby.svg)](https://gitter.im/ns-3-sem/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)\n[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/signetlabdei/sem/newrelease?urlpath=lab)\n\nThis is a Python library to perform multiple ns-3 script executions, manage the\nresults and collect them in processing-friendly data structures.\n\n<p align="center">\n  <img src="res/semdemo.gif">\n</p>\n\n# How does this work? #\n\nFor complete step-by-step usage and installation instructions, check out\n[readthedocs][rtd].\n\n# How to cite us #\n\nIf you used SEM for your ns-3 analysis, please cite the following paper, both to\nprovide a reference and help others find out about this tool:\n\nDavide Magrin, Dizhi Zhou, and Michele Zorzi. 2019. A Simulation Execution\nManager for ns-3: Encouraging reproducibility and simplifying statistical\nanalysis of ns-3 simulations. In Proceedings of the 22nd International ACM\nConference on Modeling, Analysis and Simulation of Wireless and Mobile Systems\n(MSWIM \'19). ACM, New York, NY, USA, 121-125. DOI:\nhttps://doi.org/10.1145/3345768.3355942\n\n# Contributing #\n\nThis section contains information on how to contribute to the project. If you\nare only interested in using SEM, check out the [documentation][rtd].\n\nIf you want to contribute to sem development, first of all you\'ll need an\ninstallation that allows you to modify the code, immediately see the results and\nrun tests.\n\n## Building the module from scratch ##\n\nThis module is developed using\n[`poetry`](https://python-poetry.org/docs/): in order to correctly\nmanage virtual environments and install dependencies, make sure it is installed.\nTypically, the following is enough:\n\n```bash\ncurl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python\n```\n\nNote that, if poetry\'s installer does not add poetry\'s path to your shell\'s startup file properly, you may need to add\n`source $HOME/.poetry/env` to your startup file. You can tell that you need to add it if your shell cannot find the poetry command the next time you open a terminal window.\n\nThen, clone the repo (or your fork, by changing the url in the following\ncommand), also getting the `ns-3` installations that are used for running\nexamples and tests:\n\n```bash\ngit clone https://github.com/DvdMgr/sem\ncd sem\ngit submodule update --init --recursive\n```\n\nFrom the project root, you can then install the package and the\nrequirements with the following:\n\n```bash\npoetry install\n```\n\nThis will also get you a set of tools such as `sphinx`, `pygments` and `pytest`\nthat handle documentation and tests.\n\nFinally, you can spawn a sub-shell using the new virtual environment by calling:\n\n```bash\npoetry shell\n```\n\nNow, you can start a python REPL to use the library interactively, issue the\nbash `sem` program, run tests and compile the documentation of your local copy\nof sem.\n\n## Running tests ##\n\nThis project uses the [`pytest`](https://docs.pytest.org/en/latest/) framework\nfor running tests. Tests can be run, from the project root, using:\n\n```bash\npython -m pytest --doctest-glob=\'*.rst\' docs/\npython -m pytest -x -n 3 --doctest-modules --cov-report term --cov=sem/ ./tests\n```\n\nThese two commands will run, respectively, all code contained in the `docs/`\nfolder and all tests, also measuring coverage and outputting it to the terminal.\n\nSince we are mainly testing integration with ns-3, tests require frequent\ncopying and pasting of folders, ns-3 compilations and simulation running.\nFurthermore, documentation tests run all the examples in the documentation to\nmake sure the output is as expected. Because of this, full tests are far from\ninstantaneous. Single test files can be targeted, to achieve faster execution\ntimes, by substituting `./tests` in the second command with the path to the test\nfile that needs to be run.\n\n## Building the documentation ##\n\nDocumentation can be built locally using the makefile\'s `docs` target:\n\n```bash\nmake docs\n```\n\nThe documentation of the current version of the package is also available on\n[readthedocs][rtd].\n\n## Running examples ##\n\nThe scripts in `examples/` can be directly run:\n\n```bash\npython examples/wifi_example.py\n```\n\n## Installing SEM in pip\'s editable mode ##\n\n`pip` currently requires a `setup.py` file to install projects in editable mode.\n\nAs explained [here](https://github.com/python-poetry/poetry/issues/761), poetry\nactually already generates a `setup.py`. After building the project, you can\nextract the file from the archive using the following command:\n\n``` bash\ntar -xvf dist/*.tar.gz --wildcards --no-anchored \'*/setup.py\' --strip=1\n```\n\nAfter this step, it becomes possible to install SEM in editable mode.\n\n\n## Authors ##\n\nDavide Magrin\n\n[rtd]: https://simulationexecutionmanager.rtfd.io\n',
    'author': 'Davide Magrin',
    'author_email': 'magrinda@dei.unipd.it',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/signetlabdei/sem',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.6.1,<4.0.0',
}


setup(**setup_kwargs)

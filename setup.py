# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    readme = f.read()

with open(path.join(here, 'LICENSE'), encoding='utf-8') as f:
    license = f.read()

setup(
    name='sem',
    version='0.1.0',
    description='A simulation execution manager for ns-3',
    long_description=readme,
    author='Davide Magrin',
    author_email='magrinda@dei.unipd.it',
    keywords='ns-3 simulation execution',
    packages=find_packages(exclude=['contrib', 'docs', 'tests', 'examples']),
    install_requires=['tinydb', 'gitpython'],
    extras_require={
        'dev': ['check-manifest'],
        'test': ['pytest'],
    },
    entry_points={
        'console_scripts': [
            'sem=sem:main',
        ],
    },
    license=license
)

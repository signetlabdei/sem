#!/bin/bash

# Example illustrating how SEM can be used to run, view and export simulations
# in few steps. Note: this script is meant to be run from the project root, via
# ./examples/cli.sh.

sem run --results-dir=./results --ns-3-path=examples/ns-3 --script=lorawan-sem-example

sem export --results-dir=./results results.mat

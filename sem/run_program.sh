#!/bin/bash
# General template for running programs.
# Specify we always want a certain type of cpu
#$ -l cputype=intel
eval "$1"

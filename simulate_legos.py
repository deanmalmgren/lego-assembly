#!/usr/bin/env python

import sys

import legos


# parse command line arguments
n_pieces = 50
n_universes = 1000

for universe in range(n_universes):
    contraption = randomly_assemble_legos(n_pieces)
    print contraption.width(), contraption.height()

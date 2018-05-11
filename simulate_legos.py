#!/usr/bin/env python

import sys

import legos


# parse command line arguments
n_pieces = 10
n_universes = 10

bucket = legos.Bucket()
for universe in range(n_universes):
    contraption = legos.Contraption()

    contraption.randomly_assemble(n_pieces)

    w1, w2, h = contraption.dimensions()
    d = contraption.density()
    print w1, w2, h, d

    # contraption = randomly_assemble_legos(n_pieces)
    # print contraption.width(), contraption.height()

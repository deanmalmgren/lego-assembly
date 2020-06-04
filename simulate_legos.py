#!/usr/bin/env python

import sys

import legos


# parse command line arguments
n_pieces = 10
n_universes = 8

bucket = legos.Bucket()
for universe in range(n_universes):
    # contraption = legos.Contraption()
    #
    # contraption.randomly_assemble(bucket, n_pieces=n_pieces)
    #
    # # w1, w2, h = contraption.dimensions()
    # d = contraption.density()
    # print(d)
    #
    # # contraption = randomly_assemble_legos(n_pieces)
    # # print contraption.width(), contraption.height()

    contraption = legos.Contraption(monochrome=True)
    contraption.randomly_assemble(
        bucket,
        n_pieces=10,
        render=True,
        filename_root="assembly-%03d-" % universe,
        width=1920,
        height=1080,
    )

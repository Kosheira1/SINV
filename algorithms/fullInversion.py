"""
@author: Vincent Maillou (vmaillou@iis.ee.ethz.ch)
@date: 2023-05

Copyright 2023 ETH Zurich and the QuaTrEx authors. All rights reserved.
"""

import numpy as np
from scipy.sparse import csc_matrix
from scipy.sparse.linalg import inv
import time
from mpi4py import MPI



def numpyInversion(A):
    """
        Invert a matrix using numpy dense matrix: numpy.linalg.inv
    """
    timings : dict[str, float] = {}

    tic = time.perf_counter() # -----------------------------
    A_inv = np.linalg.inv(A)
    toc = time.perf_counter() # -----------------------------
    timings["inversion"] = toc - tic

    timings["test"] = 0.0005

    return A_inv, timings



def scipyCSCInversion(A):
    """
        Invert a matrix using scipy CSC matrix: scipy.sparse.linalg.inv
    """
    timings : dict[str, float] = {}

    tic = time.perf_counter() # -----------------------------
    A_inv = inv(A)
    toc = time.perf_counter() # -----------------------------
    timings["inversion"] = toc - tic

    return A_inv, timings
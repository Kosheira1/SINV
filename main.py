"""
@author: Vincent Maillou (vmaillou@iis.ee.ethz.ch)
@date: 2023-05

Copyright 2023 ETH Zurich and the QuaTrEx authors. All rights reserved.
"""

import utils.generateMatrices    as genMat
import utils.convertMatrices     as convMat
import utils.transformMatrices   as transMat
import utils.vizualisation       as vizu
import utils.benchmarking        as bench

import algorithms.fullInversion as inv
import algorithms.rgf           as rgf
import algorithms.rgf2sided     as rgf2sided
import algorithms.hybridParRec  as hpr

import verifyResults as verif

import numpy as np
import time

from mpi4py import MPI



if __name__ == "__main__":
    # ---------------------------------------------------------------------------------------------
    # Initialization of the problem and computation of the reference solution
    # ---------------------------------------------------------------------------------------------
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()


    # Benchmarking parameters
    n_runs = 3

    greenRetardedBenchmark = bench.Benchmark("Retarded Green's function computation", n_runs)
    greenLesserBenchmark   = bench.Benchmark("Lesser Green's function computation", n_runs)


    # Problem parameters
    size = 120
    blocksize = 10
    density = blocksize**2/size**2
    bandwidth = np.ceil(blocksize/2)

    isComplex = True
    seed = 63



    # ---------------------------------------------------------------------------------------------
    # 0. Retarded Green's function references solutions (Full inversions)
    # ---------------------------------------------------------------------------------------------
    # Retarded Green's function initial matrix
    A = genMat.generateBandedDiagonalMatrix(size, bandwidth, isComplex, seed)
    A = transMat.transformToSymmetric(A)
    A_csc = convMat.convertDenseToCSC(A)

    # Retarded Green's function references solutions (Full inversions)
    numpy_runs : list = [None for i in range(n_runs)]
    for i in range(n_runs):
        GreenRetarded_refsol_np, numpy_runs[i] = inv.numpyInversion(A)

    greenRetardedBenchmark.addMethodBenchmark("numpy", numpy_runs)


    scipy_runs : list = [None for i in range(n_runs)]
    for i in range(n_runs):   
        GreenRetarded_refsol_csc, scipy_runs[i] = inv.scipyCSCInversion(A_csc)

    greenRetardedBenchmark.addMethodBenchmark("scipy", scipy_runs)

    print(greenRetardedBenchmark.getMethodMean("numpy"))
    #print(greenRetardedBenchmark.getMethodStdDeviation("numpy"))





    if not verif.verifResults(GreenRetarded_refsol_np, GreenRetarded_refsol_csc):
        print("Error: Green retarded references solutions are different.")
        exit()
    else:
        # Extract the blocks from the retarded Green's function reference solution
        GreenRetarded_refsol_block_diag\
        , GreenRetarded_refsol_block_upper\
        , GreenRetarded_refsol_block_lower = convMat.convertDenseToBlocksTriDiagStorage(GreenRetarded_refsol_np, blocksize)

    A_block_diag, A_block_upper, A_block_lower = convMat.convertDenseToBlocksTriDiagStorage(A, blocksize)













































    """ # ---------------------------------------------------------------------------------------------
    # 0. Lesser Green's function references solutions (Full inversions)
    # ---------------------------------------------------------------------------------------------
    # Lesser Green's function initial matrix
    GreenAdvanced_refsol_np = np.conjugate(np.transpose(GreenRetarded_refsol_np)) 

    SigmaLesser = genMat.generateBandedDiagonalMatrix(size, bandwidth, isComplex, seed)
    SigmaLesser = transMat.transformToSymmetric(SigmaLesser)

    # 1. Dense matrix
    for i in range(n_runs):
        tic = time.perf_counter()
        B = A @ SigmaLesser @ GreenAdvanced_refsol_np
        toc = time.perf_counter()

        timing = toc - tic

        GreenLesser_refsol_np, np_greenLesser_timings.timingRuns[i] = inv.numpyInversion(B)
        np_greenLesser_timings.timingRuns[i] += timing

    # 2. CSC matrix
    GreenAdvanced_refsol_csc = convMat.convertDenseToCSC(GreenAdvanced_refsol_np)
    SigmaLesser_csc = convMat.convertDenseToCSC(SigmaLesser)

    for i in range(n_runs):
        tic = time.perf_counter()
        B_csc = A_csc @ SigmaLesser_csc @ GreenAdvanced_refsol_csc
        toc = time.perf_counter()

        timing = toc - tic

        GreenLesser_refsol_csc, csc_greenLesser_timings.timingRuns[i] = inv.scipyCSCInversion(B_csc)
        csc_greenLesser_timings.timingRuns[i] += timing

    if not verif.verifResults(GreenLesser_refsol_np, GreenLesser_refsol_csc):
        print("Error: Green lesser references solutions are different.")
        exit()
    else:
        # Extract the blocks from the retarded Green's function reference solution
        GreenAdvanced_refsol_block_diag\
        , GreenAdvanced_refsol_block_upper\
        , GreenAdvanced_refsol_block_lower = convMat.convertDenseToBlocksTriDiagStorage(GreenLesser_refsol_np, blocksize)



    comm.barrier()
    # ---------------------------------------------------------------------------------------------
    # 1. RGF  
    # ---------------------------------------------------------------------------------------------

    if rank == 0: # Single process algorithm
        for i in range(n_runs):
            GreenRetarded_rgf_diag\
            , GreenRetarded_rgf_upper\
            , GreenRetarded_rgf_lower\
            , rgf_greenRetarded_timings.timingRuns[i] = rgf.rgf_leftToRight_Gr(A_block_diag, A_block_upper, A_block_lower)

        print("RGF: Gr validation: ", verif.verifResultsBlocksTri(GreenRetarded_refsol_block_diag, 
                                                                 GreenRetarded_refsol_block_upper, 
                                                                 GreenRetarded_refsol_block_lower, 
                                                                 GreenRetarded_rgf_diag, 
                                                                 GreenRetarded_rgf_upper, 
                                                                 GreenRetarded_rgf_lower)) 



    comm.barrier()
    # ---------------------------------------------------------------------------------------------
    # 2. RGF 2-sided 
    # ---------------------------------------------------------------------------------------------
    # mpiexec -n 2 python benchmarking.py

    for i in range(n_runs):
        GreenRetarded_rgf2sided_diag\
        , GreenRetarded_rgf2sided_upper\
        , GreenRetarded_rgf2sided_lower\
        , rgf2sided_greenRetarded_timings.timingRuns[i] = rgf2sided.rgf2sided_Gr(A_block_diag, A_block_upper, A_block_lower)
        comm.barrier()

    if rank == 0: # Results agregated on 1st process and compared to reference solution
        print("RGF 2-sided: Gr validation: ", verif.verifResultsBlocksTri(GreenRetarded_refsol_block_diag, 
                                                                          GreenRetarded_refsol_block_upper, 
                                                                          GreenRetarded_refsol_block_lower, 
                                                                          GreenRetarded_rgf2sided_diag, 
                                                                          GreenRetarded_rgf2sided_upper, 
                                                                          GreenRetarded_rgf2sided_lower)) 


        #matUtils.compareDenseMatrixFromBlocks(GreenRetarded_refsol_block_diag, 
        #                                    GreenRetarded_refsol_block_upper, 
        #                                    GreenRetarded_refsol_block_lower,
        #                                    GreenRetarded_rgf2sided_diag, 
        #                                    GreenRetarded_rgf2sided_upper, 
        #                                    GreenRetarded_rgf2sided_lower, "RGF 2-sided solution")



    comm.barrier()
    # ---------------------------------------------------------------------------------------------
    # 3. HPR (Hybrid Parallel Recurence) 
    # ---------------------------------------------------------------------------------------------

    # .1 Serial HPR
    if rank == 0:
        for i in range(n_runs):
            G_hpr_serial, hpr_serial_greenRetarded_timings.timingRuns[i] = hpr.hpr_serial(A, blocksize)

        G_hpr_serial_diag = np.zeros((size, size), dtype=np.complex128)
        G_hpr_serial_upper = np.zeros((size, size), dtype=np.complex128)
        G_hpr_serial_lower = np.zeros((size, size), dtype=np.complex128)

        G_hpr_serial_diag\
        , G_hpr_serial_upper\
        , G_hpr_serial_lower = convMat.convertDenseToBlocksTriDiagStorage(G_hpr_serial, blocksize)

        print("HPR serial: Gr validation: ", verif.verifResultsBlocksTri(GreenRetarded_refsol_block_diag, 
                                                                         GreenRetarded_refsol_block_upper, 
                                                                         GreenRetarded_refsol_block_lower, 
                                                                         G_hpr_serial_diag, 
                                                                         G_hpr_serial_upper, 
                                                                         G_hpr_serial_lower))
        
    comm.barrier()
        
        
    

    # ---------------------------------------------------------------------------------------------
    # X. Data plotting
    # ---------------------------------------------------------------------------------------------
   #if rank == 0:
        #fullBenchmark = [np_greenRetarded_timings, csc_greenRetarded_timings, rgf_greenRetarded_timings, rgf2sided_greenRetarded_timings, hpr_serial_greenRetarded_timings]
        #bench.showBenchmark(fullBenchmark, size/blocksize, blocksize)

        #fullBenchmark = [np_greenLesser_timings, csc_greenLesser_timings, rgf_greenLesser_timings, rgf2sided_greenLesser_timings]
        #bench.showBenchmark(fullBenchmark, size/blocksize, blocksize) """




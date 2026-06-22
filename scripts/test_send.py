from mpi4py import MPI
import numpy as np

comm = MPI.COMM_WORLD
rank = comm.Get_rank()

if rank == 0:
    buf = np.array([42], dtype='i')
    comm.Send([buf, MPI.INT], dest=1, tag=42)
elif rank == 1:
    buf = np.empty(1, dtype='i')
    comm.Recv([buf, MPI.INT], source=0, tag=42)
    print(buf[0])
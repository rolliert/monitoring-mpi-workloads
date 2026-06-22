from mpi4py import MPI
import numpy as np

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

buf = np.array([rank], dtype='i')

if rank < size - 1:
    comm.Send([buf, MPI.INT], dest=rank + 1, tag=100 + rank)

if rank > 0:
    recv_buf = np.empty(1, dtype='i')
    comm.Recv([recv_buf, MPI.INT], source=rank - 1, tag=100 + rank - 1)
    print(f"rank {rank} received {recv_buf[0]}")
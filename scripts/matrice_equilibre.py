from mpi4py import MPI
import numpy as np

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

N = 1800
ITERATIONS = 1

rows = N // size

if rank == 0:
    A = np.random.rand(N, N)
    B = np.random.rand(N, N)
else:
    A = None
    B = np.empty((N, N))

local_A = np.empty((rows, N))

comm.Scatter(A, local_A, root=0)
comm.Bcast(B, root=0)

for iteration in range(ITERATIONS):
    comm.Barrier()
    start = MPI.Wtime()

    local_C = local_A @ B

    local_sum = np.array(local_C.sum())
    global_sum = np.array(0.0)
    comm.Allreduce(local_sum, global_sum, op=MPI.SUM)

    elapsed = MPI.Wtime() - start
    times = comm.gather(elapsed, root=0)

    if rank == 0:
        print(f"Iteration {iteration + 1}: {times}")

global_C = np.empty((N, N)) if rank == 0 else None
comm.Gather(local_C, global_C, root=0)

if rank == 0:
    print("Matrice C reconstituée")


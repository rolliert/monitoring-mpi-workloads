from mpi4py import MPI
import numpy as np

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

N = 8000
ITERATIONS = 10
BLOCK_SIZE = 500

rows = N // size

if rank == 0:
    np.random.seed(42)
    A = np.random.rand(N, N)
    B = np.random.rand(N, N)
else:
    A = None
    B = None

local_A = np.empty((rows, N))

comm.Scatter(A, local_A, root=0)

for iteration in range(ITERATIONS):
    local_C = np.zeros((rows, N))

    comm.Barrier()
    total_start = MPI.Wtime()

    compute_time = 0.0
    bcast_time = 0.0

    for k in range(0, N, BLOCK_SIZE):
        if rank == 0:
            B_block = B[k:k + BLOCK_SIZE, :]
        else:
            B_block = np.empty((BLOCK_SIZE, N))

        bcast_start = MPI.Wtime()
        comm.Bcast(B_block, root=0)
        bcast_time += MPI.Wtime() - bcast_start

        compute_start = MPI.Wtime()
        local_C += local_A[:, k:k + BLOCK_SIZE] @ B_block
        compute_time += MPI.Wtime() - compute_start

    local_sum = np.array(local_C.sum())
    global_sum = np.array(0.0)

    allreduce_start = MPI.Wtime()
    comm.Allreduce(local_sum, global_sum, op=MPI.SUM)
    allreduce_time = MPI.Wtime() - allreduce_start

    total_time = MPI.Wtime() - total_start

    compute_times = comm.gather(compute_time, root=0)
    bcast_times = comm.gather(bcast_time, root=0)
    allreduce_times = comm.gather(allreduce_time, root=0)
    total_times = comm.gather(total_time, root=0)

    if rank == 0:
        print(f"Iteration {iteration + 1}")
        print(f"  Calcul    : {compute_times}")
        print(f"  Bcast     : {bcast_times}")
        print(f"  Allreduce : {allreduce_times}")
        print(f"  Total     : {total_times}")


global_C = np.empty((N, N)) if rank == 0 else None

comm.Gather(local_C, global_C, root=0)

if rank == 0:
    print("Matrice C reconstituée")
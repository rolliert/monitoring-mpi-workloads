from mpi4py import MPI
import numpy as np

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

N = 8000
ITERATIONS = 10
BLOCK_SIZE = 500

rows_per_rank = np.array([1200, 1200, 1200, 4400], dtype=int)

local_rows = rows_per_rank[rank]

counts = rows_per_rank * N

displacements = np.array([
    0,
    counts[0],
    counts[0] + counts[1],
    counts[0] + counts[1] + counts[2]
], dtype=int)

if rank == 0:
    A = np.random.rand(N, N)
    B = np.random.rand(N, N)
    print(f"Lignes par processus : {rows_per_rank}")
else:
    A = None
    B = None

local_A = np.empty((local_rows, N))

if rank == 0:
    comm.Scatterv(
        [A, counts, displacements, MPI.DOUBLE],
        local_A,
        root=0
    )
else:
    comm.Scatterv(
        None,
        local_A,
        root=0
    )

for iteration in range(ITERATIONS):
    local_C = np.zeros((local_rows, N))

    comm.Barrier()
    start = MPI.Wtime()

    for k in range(0, N, BLOCK_SIZE):
        if rank == 0:
            B_block = B[k:k + BLOCK_SIZE, :]
        else:
            B_block = np.empty((BLOCK_SIZE, N))

        comm.Bcast(B_block, root=0)

        local_C += local_A[:, k:k + BLOCK_SIZE] @ B_block

    local_sum = np.array(local_C.sum())
    global_sum = np.array(0.0)

    comm.Allreduce(local_sum, global_sum, op=MPI.SUM)

    elapsed = MPI.Wtime() - start
    times = comm.gather(elapsed, root=0)

    if rank == 0:
        print(f"Iteration {iteration + 1}: {times}")

if rank == 0:
    global_C = np.empty((N, N))
else:
    global_C = None

comm.Gatherv(
    local_C,
    [global_C, counts, displacements, MPI.DOUBLE] if rank == 0 else None,
    root=0
)

if rank == 0:
    print("Matrice C reconstituée")
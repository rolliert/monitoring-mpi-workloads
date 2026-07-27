from mpi4py import MPI
import numpy as np

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

N = 1800
ITERATIONS = 1

# Rank 0 receives 55% of the rows.
rows_per_rank = [990, 270, 270, 270]

counts = np.array([rows * N for rows in rows_per_rank])
displacements = np.array([0, counts[0], counts[0] + counts[1],
                          counts[0] + counts[1] + counts[2]])

local_rows = rows_per_rank[rank]

if rank == 0:
    A = np.random.rand(N, N)
    B = np.random.rand(N, N)
else:
    A = None
    B = np.empty((N, N))

local_A = np.empty((local_rows, N))

comm.Scatterv([A, counts, displacements, MPI.DOUBLE], local_A, root=0)
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
comm.Gatherv(local_C, [global_C, counts, displacements, MPI.DOUBLE], root=0)

if rank == 0:
    print("Matrice C reconstituée")
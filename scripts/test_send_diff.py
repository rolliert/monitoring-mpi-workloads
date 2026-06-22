from mpi4py import MPI
import numpy as np
import time

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

if size != 4:
    if rank == 0:
        print("Ce test doit être lancé avec exactement 4 processus.")
    raise SystemExit

# Nombre de messages à envoyer par rank
send_counts = {
    0: 100,
    1: 110,
    2: 120,
    3: 130,
}

# Destination en anneau
dest = (rank + 1) % 4
source = (rank - 1) % 4

# Combien je vais recevoir du rank précédent
recv_count = send_counts[source]

# Buffer simple
send_buf = np.array([rank], dtype='i')
recv_buf = np.empty(1, dtype='i')

comm.Barrier()

# Phase 1 : tous les sends
for i in range(send_counts[rank]):
    comm.Send([send_buf, MPI.INT], dest=dest, tag=1000 + rank * 10 + i)
    print(f"rank {rank} sent message {i + 1}/{send_counts[rank]} to rank {dest}")

    time.sleep(20) 

# Phase 2 : tous les recvs
for i in range(recv_count):
    comm.Recv([recv_buf, MPI.INT], source=source, tag=1000 + source * 10 + i)
    print(f"rank {rank} received message {i + 1}/{recv_count} from rank {source}: {recv_buf[0]}")

comm.Barrier()

if rank == 0:
    print("Test terminé.")
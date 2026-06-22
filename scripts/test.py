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

send_counts = {
    0: 100,
    1: 110,
    2: 120,
    3: 130,
}

dest = (rank + 1) % 4
source = (rank - 1) % 4
recv_count = send_counts[source]

comm.Barrier()

requests = []
recv_buffers = []
send_buffers = []

# 1. Poster toutes les réceptions d'abord
for i in range(recv_count):
    recv_buf = np.empty(1, dtype='i')
    recv_buffers.append(recv_buf)

    req = comm.Irecv(
        [recv_buf, MPI.INT],
        source=source,
        tag=1000 + source * 10 + i
    )
    requests.append(req)

# 2. Poster les envois ensuite
for i in range(send_counts[rank]):
    send_buf = np.array([rank], dtype='i')
    send_buffers.append(send_buf)

    req = comm.Isend(
        [send_buf, MPI.INT],
        dest=dest,
        tag=1000 + rank * 10 + i
    )
    requests.append(req)

    print(f"rank {rank} posted send {i + 1}/{send_counts[rank]} to rank {dest}", flush=True)

    time.sleep(5) # Simuler un délai pour rendre les choses plus visibles

# 3. Attendre que toutes les communications finissent
MPI.Request.Waitall(requests)

# 4. Afficher les messages reçus
for i, buf in enumerate(recv_buffers):
    print(f"rank {rank} received message {i + 1}/{recv_count} from rank {source}: {buf[0]}", flush=True)

comm.Barrier()

if rank == 0:
    print("Test terminé.")
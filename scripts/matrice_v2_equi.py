from mpi4py import MPI
import numpy as np

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

N = 8000

# Trois multiplications complètes suffisent normalement pour la démonstration.
ITERATIONS = 3

# 8000 / 500 = 16 diffusions MPI_Bcast par multiplication.
BLOCK_SIZE = 500

if N % size != 0:
    if rank == 0:
        print(
            f"Erreur : N={N} doit être divisible par "
            f"le nombre de processus ({size})."
        )
    comm.Abort(1)

rows = N // size

# Création des matrices uniquement sur le processus racine.
if rank == 0:
    rng = np.random.default_rng(seed=42)

    A = rng.random((N, N), dtype=np.float64)
    B = rng.random((N, N), dtype=np.float64)
else:
    A = None
    B = None

# Chaque processus reçoit un bloc de lignes de A.
local_A = np.empty((rows, N), dtype=np.float64)

comm.Scatter(A, local_A, root=0)

# Buffer réutilisé pour recevoir les panneaux de B.
B_panel_buffer = np.empty((BLOCK_SIZE, N), dtype=np.float64)

number_of_panels = (N + BLOCK_SIZE - 1) // BLOCK_SIZE

if rank == 0:
    print(f"Nombre de processus : {size}")
    print(f"Taille des matrices : {N} x {N}")
    print(f"Taille des panneaux : {BLOCK_SIZE}")
    print(f"Nombre de MPI_Bcast par itération : {number_of_panels}")

for iteration in range(ITERATIONS):

    # Le résultat local est recalculé à chaque itération.
    local_C = np.zeros((rows, N), dtype=np.float64)

    comm.Barrier()
    start = MPI.Wtime()

    # Multiplication par panneaux.
    for k0 in range(0, N, BLOCK_SIZE):
        k1 = min(k0 + BLOCK_SIZE, N)
        current_block_size = k1 - k0

        # Vue correspondant à la taille réelle du panneau.
        B_panel = B_panel_buffer[:current_block_size, :]

        # Le processus 0 prépare le panneau à envoyer.
        if rank == 0:
            B_panel[:, :] = B[k0:k1, :]

        # Diffusion du panneau vers tous les processus.
        comm.Bcast(B_panel, root=0)

        # Contribution de ce panneau au résultat local.
        local_C += local_A[:, k0:k1] @ B_panel

    # Vérification globale du résultat avec une somme de contrôle.
    local_sum = np.array(
        [local_C.sum()],
        dtype=np.float64
    )

    global_sum = np.zeros(
        1,
        dtype=np.float64
    )

    comm.Allreduce(
        local_sum,
        global_sum,
        op=MPI.SUM
    )

    elapsed = np.array(
        [MPI.Wtime() - start],
        dtype=np.float64
    )

    # Utilisation de Gather avec des buffers NumPy plutôt que comm.gather.
    if rank == 0:
        times = np.empty(size, dtype=np.float64)
    else:
        times = None

    comm.Gather(
        elapsed,
        times,
        root=0
    )

    if rank == 0:
        print(
            f"Iteration {iteration + 1}: "
            f"min={times.min():.3f} s, "
            f"moyenne={times.mean():.3f} s, "
            f"max={times.max():.3f} s, "
            f"checksum={global_sum[0]:.6e}"
        )

# Reconstruction de la matrice complète après la dernière itération.
if rank == 0:
    global_C = np.empty((N, N), dtype=np.float64)
else:
    global_C = None

comm.Gather(
    local_C,
    global_C,
    root=0
)

if rank == 0:
    print("Matrice C reconstituée.")
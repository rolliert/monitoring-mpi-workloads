import yaml

CONFIG_FILE = "config_wrapper.yml"
OUTPUT_FILE = "mpi_monitoring_generated.c"

# Wrapper implementations for the MPI functions supported by the monitoring system.
# Each wrapper measures the time spent in the corresponding MPI operation,
# calls the original implementation through PMPI, and records the resulting metrics.
WRAPPERS = {
    "MPI_Send": """
int MPI_Send(const void *buf, int count, MPI_Datatype datatype,
             int dest, int tag, MPI_Comm comm) {
    uint64_t start = now_ns();

    int ret = PMPI_Send(buf, count, datatype, dest, tag, comm);

    uint64_t end = now_ns();

    if (ret == MPI_SUCCESS) {
        int type_size = 0;
        PMPI_Type_size(datatype, &type_size);

        record_metric("MPI_Send", dest,
                      (uint64_t)count * (uint64_t)type_size,
                      end - start);
    }

    return ret;
}
""",

    "MPI_Recv": """
int MPI_Recv(void *buf, int count, MPI_Datatype datatype,
             int source, int tag, MPI_Comm comm, MPI_Status *status) {
    uint64_t start = now_ns();

    int ret = PMPI_Recv(buf, count, datatype, source, tag, comm, status);

    uint64_t end = now_ns();

    if (ret == MPI_SUCCESS) {
        int actual_count = count;
        int real_source = source;

        if (status != MPI_STATUS_IGNORE && status != NULL) {
            PMPI_Get_count(status, datatype, &actual_count);
            real_source = status->MPI_SOURCE;
        }

        int type_size = 0;
        PMPI_Type_size(datatype, &type_size);

        record_metric("MPI_Recv", real_source,
                      (uint64_t)actual_count * (uint64_t)type_size,
                      end - start);
    }

    return ret;
}
""",

    "MPI_Isend": """
int MPI_Isend(const void *buf, int count, MPI_Datatype datatype,
              int dest, int tag, MPI_Comm comm, MPI_Request *request) {
    uint64_t start = now_ns();

    int ret = PMPI_Isend(buf, count, datatype, dest, tag, comm, request);

    uint64_t end = now_ns();

    if (ret == MPI_SUCCESS) {
        int type_size = 0;
        PMPI_Type_size(datatype, &type_size);

        record_metric("MPI_Isend", dest,
                      (uint64_t)count * (uint64_t)type_size,
                      end - start);
    }

    return ret;
}""",

    "MPI_Irecv": """
int MPI_Irecv(void *buf, int count, MPI_Datatype datatype,
              int source, int tag, MPI_Comm comm, MPI_Request *request) {
    uint64_t start = now_ns();

    int ret = PMPI_Irecv(buf, count, datatype, source, tag, comm, request);

    uint64_t end = now_ns();

    if (ret == MPI_SUCCESS) {
        int type_size = 0;
        PMPI_Type_size(datatype, &type_size);

        record_metric("MPI_Irecv", source,
                      (uint64_t)count * (uint64_t)type_size,
                      end - start);
    }

    return ret;
}

""",

    "MPI_Barrier": """
int MPI_Barrier(MPI_Comm comm) {
    uint64_t start = now_ns();

    int ret = PMPI_Barrier(comm);

    uint64_t end = now_ns();

    if (ret == MPI_SUCCESS) {
        record_metric("MPI_Barrier", -1, 0, end - start);
    }

    return ret;
}
""",

    "MPI_Bcast": """
int MPI_Bcast(void *buffer, int count, MPI_Datatype datatype,
              int root, MPI_Comm comm) {
    uint64_t start = now_ns();

    int ret = PMPI_Bcast(buffer, count, datatype, root, comm);

    uint64_t end = now_ns();

    if (ret == MPI_SUCCESS) {
        int type_size = 0;
        PMPI_Type_size(datatype, &type_size);

        record_metric("MPI_Bcast", root,
                      (uint64_t)count * (uint64_t)type_size,
                      end - start);
    }

    return ret;
}
""",

    "MPI_Wait": """
int MPI_Wait(MPI_Request *request, MPI_Status *status) {
    uint64_t start = now_ns();

    int ret = PMPI_Wait(request, status);

    uint64_t end = now_ns();

    if (ret == MPI_SUCCESS) {
        int real_source = -1;


        if (status != MPI_STATUS_IGNORE && status != NULL) {
            real_source = status->MPI_SOURCE;
        }

        record_metric("MPI_Wait", real_source, 0, end - start);
    }

    return ret;
}
""",

    "MPI_Waitall": """
int MPI_Waitall(int count, MPI_Request array_of_requests[],
                MPI_Status array_of_statuses[]) {
    uint64_t start = now_ns();

    int ret = PMPI_Waitall(count, array_of_requests, array_of_statuses);

    uint64_t end = now_ns();

    if (ret == MPI_SUCCESS) {
        record_metric("MPI_Waitall", -1, 0, end - start);
    }

    return ret;
}
""",

    "MPI_Reduce": """
int MPI_Reduce(const void *sendbuf, void *recvbuf, int count,
               MPI_Datatype datatype, MPI_Op op, int root, MPI_Comm comm) {
    uint64_t start = now_ns();

    int ret = PMPI_Reduce(sendbuf, recvbuf, count, datatype, op, root, comm);

    uint64_t end = now_ns();

    if (ret == MPI_SUCCESS) {
        int type_size = 0;
        PMPI_Type_size(datatype, &type_size);

        record_metric("MPI_Reduce", root,
                      (uint64_t)count * (uint64_t)type_size,
                      end - start);
    }

    return ret;
}
""",

    "MPI_Allreduce": """
int MPI_Allreduce(const void *sendbuf, void *recvbuf, int count,
                  MPI_Datatype datatype, MPI_Op op, MPI_Comm comm) {
    uint64_t start = now_ns();

    int ret = PMPI_Allreduce(sendbuf, recvbuf, count, datatype, op, comm);

    uint64_t end = now_ns();

    if (ret == MPI_SUCCESS) {
        int type_size = 0;
        PMPI_Type_size(datatype, &type_size);

        record_metric("MPI_Allreduce", -1,
                      (uint64_t)count * (uint64_t)type_size,
                      end - start);
    }

    return ret;
}
""",

    "MPI_Gather": """
int MPI_Gather(const void *sendbuf, int sendcount, MPI_Datatype sendtype,
               void *recvbuf, int recvcount, MPI_Datatype recvtype,
               int root, MPI_Comm comm) {
    uint64_t start = now_ns();

    int ret = PMPI_Gather(sendbuf, sendcount, sendtype,
                          recvbuf, recvcount, recvtype,
                          root, comm);

    uint64_t end = now_ns();

    if (ret == MPI_SUCCESS) {
        int type_size = 0;
        PMPI_Type_size(sendtype, &type_size);

        record_metric("MPI_Gather", root,
                      (uint64_t)sendcount * (uint64_t)type_size,
                      end - start);
    }

    return ret;
}
""",

    "MPI_Scatter": """
int MPI_Scatter(const void *sendbuf, int sendcount, MPI_Datatype sendtype,
                void *recvbuf, int recvcount, MPI_Datatype recvtype,
                int root, MPI_Comm comm) {
    uint64_t start = now_ns();

    int ret = PMPI_Scatter(sendbuf, sendcount, sendtype,
                           recvbuf, recvcount, recvtype,
                           root, comm);

    uint64_t end = now_ns();

    if (ret == MPI_SUCCESS) {
        int type_size = 0;
        PMPI_Type_size(recvtype, &type_size);

        record_metric("MPI_Scatter", root,
                      (uint64_t)recvcount * (uint64_t)type_size,
                      end - start);
    }

    return ret;
}
"""
}


# Common C code shared by all generated MPI wrappers.
# It manages metric aggregation, synchronization, and periodic export
# to the Prometheus textfile collector.
COMMON_CODE = r"""
#include <mpi.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

#define MAX_ENTRIES 4096
#define FLUSH_INTERVAL_NS 1000000000ULL

// Stores aggregated metrics for one MPI operation and peer.
typedef struct {
    int used;
    char operation[32];
    int peer;
    uint64_t calls_total;
    uint64_t bytes_total;
    uint64_t duration_ns_total;
} metric_entry_t;

// Protects metric updates and file writes in multi-threaded applications.
static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;
static metric_entry_t entries[MAX_ENTRIES];

static int rank_id = -1;
static uint64_t last_flush_ns = 0;

static const char *prom_file = "/var/lib/node_exporter/textfile_collector/mpi_metrics.prom";
static const char *tmp_file  = "/var/lib/node_exporter/textfile_collector/mpi_metrics.prom.tmp";

// Returns a timestamp in nanoseconds for MPI duration measurements.
static uint64_t now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

// Finds the metric entry associated with an operation and peer.
// A new entry is initialized if no existing entry is found.
static metric_entry_t *get_entry(const char *operation, int peer) {
    for (int i = 0; i < MAX_ENTRIES; i++) {
        if (entries[i].used &&
            strcmp(entries[i].operation, operation) == 0 &&
            entries[i].peer == peer) {
            return &entries[i];
        }
    }

    for (int i = 0; i < MAX_ENTRIES; i++) {
        if (!entries[i].used) {
            entries[i].used = 1;
            strncpy(entries[i].operation, operation, sizeof(entries[i].operation) - 1);
            entries[i].peer = peer;
            entries[i].calls_total = 0;
            entries[i].bytes_total = 0;
            entries[i].duration_ns_total = 0;
            return &entries[i];
        }
    }

    return NULL;
}

// Writes the current metrics in Prometheus exposition format.
// Metrics are first written to a temporary file and then renamed
// to avoid Node Exporter reading a partially written file.
static void flush_metrics(void) {
    FILE *f = fopen(tmp_file, "w");
    if (!f) {
        return;
    }

    fprintf(f, "# HELP mpi_calls_total Total number of MPI calls\n");
    fprintf(f, "# TYPE mpi_calls_total counter\n");

    fprintf(f, "# HELP mpi_bytes_total Total bytes transferred by MPI calls\n");
    fprintf(f, "# TYPE mpi_bytes_total counter\n");

    fprintf(f, "# HELP mpi_duration_seconds_total Total time spent in MPI calls\n");
    fprintf(f, "# TYPE mpi_duration_seconds_total counter\n");

    for (int i = 0; i < MAX_ENTRIES; i++) {
        if (!entries[i].used) {
            continue;
        }

        fprintf(f,
                "mpi_calls_total{rank=\"%d\",operation=\"%s\",peer=\"%d\"} %llu\n",
                rank_id,
                entries[i].operation,
                entries[i].peer,
                (unsigned long long)entries[i].calls_total);

        fprintf(f,
                "mpi_bytes_total{rank=\"%d\",operation=\"%s\",peer=\"%d\"} %llu\n",
                rank_id,
                entries[i].operation,
                entries[i].peer,
                (unsigned long long)entries[i].bytes_total);

        fprintf(f,
                "mpi_duration_seconds_total{rank=\"%d\",operation=\"%s\",peer=\"%d\"} %.9f\n",
                rank_id,
                entries[i].operation,
                entries[i].peer,
                (double)entries[i].duration_ns_total / 1e9);
    }

    fclose(f);
    rename(tmp_file, prom_file);
    last_flush_ns = now_ns();
}

// Updates the aggregated metrics for an intercepted MPI call.
// Metrics are periodically exported according to FLUSH_INTERVAL_NS.
static void record_metric(const char *operation, int peer,
                          uint64_t bytes, uint64_t duration_ns) {
    pthread_mutex_lock(&lock);

    if (rank_id < 0) {
        PMPI_Comm_rank(MPI_COMM_WORLD, &rank_id);
    }

    metric_entry_t *e = get_entry(operation, peer);

    if (e) {
        e->calls_total += 1;
        e->bytes_total += bytes;
        e->duration_ns_total += duration_ns;
    }

    if (now_ns() - last_flush_ns >= FLUSH_INTERVAL_NS) {
        flush_metrics();
    }

    pthread_mutex_unlock(&lock);
}

// Performs a final metric export before terminating the MPI environment.
int MPI_Finalize(void) {
    pthread_mutex_lock(&lock);

    if (rank_id < 0) {
        PMPI_Comm_rank(MPI_COMM_WORLD, &rank_id);
    }

    flush_metrics();

    pthread_mutex_unlock(&lock);

    return PMPI_Finalize();
}
"""


def main():
    # Load the list of MPI functions to instrument.
    with open(CONFIG_FILE, "r") as f:
        config = yaml.safe_load(f)

    functions = config.get("functions", [])

    # Start with the common metric collection and export code.
    code = COMMON_CODE

    # Append only the wrappers enabled in the configuration file.
    for func in functions:
        if func not in WRAPPERS:
            raise ValueError(f"Wrapper not defined for {func}")
        code += "\n"
        code += WRAPPERS[func]

    # Generate the final C source file used to build the shared library.
    with open(OUTPUT_FILE, "w") as f:
        f.write(code)

    print(f"Generated {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
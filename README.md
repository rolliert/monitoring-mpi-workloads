# MPI Monitoring Cluster

## Description

This project deploys and configures a MPI cluster with monitoring using Ansible.

The infrastructure contains:

- one MPI master node;
- several MPI worker/slave nodes;
- one monitoring node;
- Prometheus for metric collection;
- Grafana for dashboards;
- Caddy as a reverse proxy for Grafana;
- Node Exporter on MPI nodes;
- An MPI wrapper.

The goal is to monitor both system-level metrics and MPI-specific metrics in order to detect performance issues, communication bottlenecks, synchronization problems, and abnormal MPI behavior.

---

## Architecture

```text
                +-------------------+
                |   Monitoring VM   |
                |-------------------|
                | Prometheus :9090  |
                | Grafana    :3000  |
                | Caddy      :80    |
                +---------+---------+
                          |
                          | scrape
                          |
        +-----------------+-----------------+
        |                 |                 |
+-------+------+   +------+-------+   +-----+--------+
|   MPI Master |   | MPI Worker 1 |   | MPI Worker 2 |
| node_exporter|   | node_exporter|   | node_exporter|
|     :9100    |   |     :9100    |   |     :9100    |
+--------------+   +--------------+   +--------------+
```

---

## Repository Structure

.
├── dashboard.json
├── hosts.yaml
├── site.yml
├── playbooks/
│   ├── mpi.yml
│   ├── monitor.yml
│   ├── preload.yml
│   └── ssh_mpi.yml
├── tasks/
│   ├── prometheus.yml
│   ├── grafana.yml
│   ├── caddy.yml
│   ├── script_import.yml
│   └── node_exporter.yml
├── templates/
│   ├── prometheus.service.j2
│   ├── prometheus.yml.j2
│   ├── node-exporter.service.j2
│   ├── Caddyfile.j2
│   ├── config_wrapper.yml
│   └── wrapper_gen.py
├── group_vars/
│   └── monitor.yml
└── README.md

---

### Main files

* `hosts.yaml`: Ansible inventory defining the monitoring node, the MPI master node, and the MPI worker/slave nodes.

* `site.yml`: Main Ansible entry point. It imports the playbooks required to configure the whole infrastructure.

* `templates/config_wrapper.yml`: Configuration file used to define which MPI functions are monitored by the wrapper.

* `templates/wrapper_gen.py`: Python script used to generate the MPI wrapper source code.

* `group_vars/monitor.yml`: Contains the list of MPI nodes scraped by Prometheus.


---

## Control Machine

This repository must be executed from a control machine, which can itself be a virtual machine.

The control machine is not part of the MPI cluster. Its role is to run the Ansible playbooks and configure the MPI nodes and the monitoring node remotely through SSH.

Before starting the deployment, the control machine must therefore:

- have Ansible installed;
- have network access to all target virtual machines;
- be able to connect to all target virtual machines through SSH;
- have access to the SSH private key defined in `hosts.yaml`.

All Ansible commands shown in this README must be executed from this control machine.

---

## Requirements

Before running the deployment, the following requirements must be satisfied:

* Ansible must be installed on the control machine.
* The control machine must be able to reach all VMs through SSH.
* The SSH private key used by Ansible must be configured in `hosts.yaml`.
* The user defined in the inventory must have sudo privileges.
* The MPI nodes and the monitoring node must be reachable on the network.

The project assumes the following roles:

* `monitor`: the node running Prometheus, Grafana, and Caddy.
* `master`: the MPI master node used to launch MPI applications.
* `slave`: the MPI worker nodes used to execute MPI processes.

---

## Deployment

The full infrastructure can be deployed using the main Ansible playbook.
Run the following command from the control machine:

```bash
ansible-playbook -i hosts.yaml site.yml
```

This command runs all the required playbooks in the correct order:

1. install and configure the MPI environment;
2. generate the MPI wrapper and deploy it on each VM;
3. install and configure the monitoring stack;
4. configure SSH access between the MPI master and the worker nodes.

---

## Individual Playbooks

Each part of the infrastructure can also be deployed separately.

To configure the MPI nodes:

```bash
ansible-playbook -i hosts.yaml playbooks/mpi.yml
```

To configure the monitoring node:

```bash
ansible-playbook -i hosts.yaml playbooks/monitor.yml
```

To configure SSH access from the MPI master to the worker nodes:

```bash
ansible-playbook -i hosts.yaml playbooks/ssh_mpi.yml
```

To deploy the MPI wrapper:

```bash
ansible-playbook -i hosts.yaml playbooks/preload.yml
```

---

## Accessing the Monitoring Tools

After deployment, the monitoring tools can be accessed from the monitoring node.

Prometheus is available at:

```text
http://<monitoring-node-ip>:9090
```

Grafana is available at:

```text
http://<monitoring-node-ip>:3000
```

Grafana is also exposed through Caddy on port `80`:

```text
http://<monitoring-node-ip>
```

Caddy acts as a reverse proxy and forwards HTTP traffic from port `80` to Grafana running on port `3000`.

---

## Prometheus Targets

Prometheus scrapes system-level metrics from the MPI nodes through Node Exporter.

The list of MPI nodes monitored by Prometheus is defined in:

```text
group_vars/monitor.yml
```

Example:

```yaml
mpi_targets:
  - 192.168.1.100
  - 192.168.1.101
  - 192.168.1.102
  - 192.168.1.103
```

To check whether Prometheus is correctly scraping the MPI nodes, open:

```text
http://<monitoring-node-ip>:9090/targets
```

All Node Exporter targets should appear with the state `UP`.

---

## Running an MPI Application with the Wrapper

The MPI wrapper is deployed on the MPI nodes and can be loaded using `LD_PRELOAD`.

From the MPI master node, an MPI application can be started with:

```bash
mpirun -np 4 \
  --hostfile scripts/hosts.txt \
  --map-by node \
  -x LD_PRELOAD=/usr/local/bin/libmpi_monitor.so \
  python3 scripts/code_to_run.py
```

Explanation:

* `mpirun`: starts the MPI application.
* `-np 4`: runs the application with 4 MPI processes.
* `--hostfile scripts/hosts.txt`: specifies the MPI nodes used by OpenMPI.
* `--map-by node`: distributes the MPI processes across the available nodes.
* `-x LD_PRELOAD=/usr/local/bin/libmpi_monitor.so`: loads the MPI monitoring wrapper before the MPI application starts.
* `python3 scripts/code_to_run.py`: runs the MPI test script.

The wrapper intercepts selected MPI calls while the application is running. The collected data can then be exposed to Prometheus and visualized in Grafana.

---

## Displaying the Grafana Dashboard

After the deployment, Grafana can be accessed from a web browser.

If the monitoring node is directly reachable, Grafana is available through Caddy on port `80`:

```text
http://<monitoring-node-ip>
```

If the monitoring node is not directly reachable from the local machine, an SSH tunnel can be used. From the local machine, run:

```bash
ssh -i .\path_to_your_ssh_key -N -L 8080:localhost:80 user@<monitoring-node-ip>
```

Then open:

```text
http://localhost:8080
```

On the first connection, Grafana may ask for authentication. The default credentials are usually:

```text
Username: admin
Password: admin
```

After logging in, Grafana may ask to change the default password.

---

### Add Prometheus as a data source

Before displaying the dashboard, Prometheus must be added as a Grafana data source.

In Grafana:

1. go to `Connections`;
2. click `Add new connection`;
3. search for `Prometheus`;
4. select `Prometheus`;
5. click `Add new data source`;
6. set the Prometheus URL to:

```text
http://localhost:9090
```

If Grafana and Prometheus run on the same monitoring node, `localhost:9090` is correct because Grafana connects to Prometheus from the monitoring node itself.

Then click `Save & test`. Grafana should confirm that the Prometheus data source is working.

---

### Import the dashboard

The Grafana dashboard is provided as a JSON file in the repository.

To import it:

1. go to `Dashboards`;
2. click `New`;
3. click `Import`;
4. upload the dashboard JSON file;
5. select the Prometheus data source;
6. click `Import`.

The MPI monitoring dashboard should now be displayed in Grafana and show the metrics collected from the MPI cluster.

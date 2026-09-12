# Linux edge workload v1

`LinuxEdgeWorkload.v1` is an immutable, offline declaration of a bounded Linux edge workload. It does not start a process, capture syscalls, publish evidence, grant an authorization, or issue a control action.

Each declaration content-addresses its image or executable, entrypoint, expected process tree, roles, permissions, network and storage interactions, configuration, code and dependency identities. It records only identities: configuration values and secrets are never fields in the contract. The workload scope explicitly excludes Mosquitto, MinIO, CometBFT, ABCI, collector, and unrelated container processes.

The only declared activities are safe acquisition, serialization, MQTT, consensus interaction, evidence write, and an explicitly approved deviation. Requests outside that allowlist fail closed. A runtime identity contains immutable host/VM, boot, container, cgroup, process, thread, kernel, architecture, edge, experiment, run, and correlation identities.

Authentic execution is authoritative whenever it is reproducible. A mock request is rejected in that case. Where authentic reproduction is unavailable, a caller must supply an exact immutable mock-admission identity and validate it through an injected `MockAdmission.v1` resolver; this module neither accepts planning approval nor creates an admission. `fixture-replay` is valid only when explicitly test-only and is distinct from `host_capture`.

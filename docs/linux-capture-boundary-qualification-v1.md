# Linux capture boundary qualification v1

`LinuxCaptureBoundaryQualification.v1` is an immutable, offline assessment of
facts already collected by a capture-qualification spike. It never starts
Sysdig/eBPF, Docker, a workload, storage, or any network client. It also never
authorizes a `host-capture` session.

The caller supplies only opaque SHA-256 identities and injected resolvers for
immutable evidence and parameter evidence. The qualification requires the
actual host or VM, boot, Linux kernel, architecture, runtime, collector/version,
capture mode/filter, buffer, queue, compression, storage, resource, and code
runtime identities. Docker Desktop must be represented as `linux_vm`; a Windows
host kernel and unknown boundary fail qualification.

All of workload attribution, ordering, duplicates, gaps, drops, queue behavior,
storage lag, overhead, and raw-to-canonical replay require their own immutable
evidence. Any declared limit must resolve through the injected parameter
evidence resolver; this contract has no numeric defaults.

Each segment must be `host_capture`, have immutable raw-byte/hash, collector,
filter, Linux kernel/boot, workload/cgroup/process/run, ordering and replay
identities, and agree exactly with the candidate environment. Fixture replay,
injected, generated, replayed, external-dataset, and unknown origins are
ineligible. A rejected candidate must name an immutable pinned fallback; a
blocked decision remains explicitly blocked.

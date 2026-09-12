# Syscall capture contracts v1

`RawCaptureSegment.v1` is the immutable manifest for a collector-closed raw
segment. `SyscallEventBatch.v1` is a separate, transport-neutral projection on
`host/syscalls/v1`; it never belongs on a physical-consensus route.

Each event carries an ordered, non-overlapping byte range into the declared raw
segment. A `host_capture` batch is formally eligible only when all provenance
binds to its valid immutable segment. `fixture_replay` is permanently
`test_only`, even if reserialized or transported again. The pure validators do
not capture, persist, route, or authorize evidence.

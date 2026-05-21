"""Offline benchmark-driven LSTM training track.

Owns the academic supervised-classifier path that is decoupled from the
live runtime loop. Reference: course-correction-2026-05-21.md +
architecture-update-2026-05-21.md section B.1.

This package must NOT import the deprecated runtime LSTM modules (the
in-runtime autoencoder trainer, the deferred lifecycle, the
reconstruction-error inference path). Those modules are kept in the tree
only as historical artifacts; they are not the academic fingerprint claim.
"""

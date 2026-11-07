# Tests

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Contract and service tests use local fixtures. Runtime smoke tests require the
corresponding optional dependencies and explicit environment configuration.
Go tests run under `abci/consensus_app` with `go test ./...`.

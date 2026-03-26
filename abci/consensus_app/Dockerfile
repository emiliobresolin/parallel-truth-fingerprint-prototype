FROM golang:1.24

WORKDIR /src

COPY go.mod ./
COPY go.sum ./
COPY cmd ./cmd
COPY internal ./internal

RUN go mod download
RUN CGO_ENABLED=0 go build -o /usr/local/bin/consensus_abci ./cmd/consensus_abci

ENTRYPOINT ["consensus_abci"]

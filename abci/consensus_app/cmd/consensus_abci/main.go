package main

import (
	"flag"
	"fmt"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"

	abciserver "github.com/cometbft/cometbft/abci/server"
	cmtlog "github.com/cometbft/cometbft/libs/log"

	"consensus_app/internal/app"
)

var (
	homeDir    string
	socketAddr string
)

func init() {
	flag.StringVar(&homeDir, "home", "", "Path to the ABCI app home directory")
	flag.StringVar(&socketAddr, "socket-addr", "tcp://0.0.0.0:26658", "Socket address")
}

func main() {
	flag.Parse()
	if homeDir == "" {
		homeDir = filepath.Join(".", ".consensus_abci")
	}
	if err := os.MkdirAll(homeDir, 0o755); err != nil {
		fmt.Fprintf(os.Stderr, "error creating app home: %v\n", err)
		os.Exit(1)
	}

	logger := cmtlog.NewTMLogger(os.Stdout)
	application, err := app.NewConsensusApplication(
		filepath.Join(homeDir, "state.json"),
	)
	if err != nil {
		fmt.Fprintf(os.Stderr, "error creating app: %v\n", err)
		os.Exit(1)
	}

	server := abciserver.NewSocketServer(socketAddr, application)
	server.SetLogger(logger)
	if err := server.Start(); err != nil {
		fmt.Fprintf(os.Stderr, "error starting socket server: %v\n", err)
		os.Exit(1)
	}
	defer server.Stop()

	logger.Info("consensus abci app started", "socket", socketAddr, "home", homeDir)

	signals := make(chan os.Signal, 1)
	signal.Notify(signals, os.Interrupt, syscall.SIGTERM)
	<-signals
}

package app

import (
	"context"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"

	abcitypes "github.com/cometbft/cometbft/abci/types"
)

type goldenCatalog struct {
	CatalogID string `json:"catalog_id"`
	Entries []struct {
		RequirementID    string `json:"requirement_id"`
		FilesystemLocator string `json:"filesystem_locator"`
		DecodedSHA256     string `json:"decoded_sha256"`
	} `json:"entries"`
}

const story95CatalogDigest = "9e954bd3291f34079e3b8a370d0f9496417a01b834b83333d8c8d1d5cf34d144"

func goldenRoot(t *testing.T) string {
	t.Helper()
	if explicit := os.Getenv("PTFP_GOLDEN_TESTDATA_ROOT"); explicit != "" {
		return explicit
	}
	_, file, _, ok := runtime.Caller(0)
	if !ok {
		t.Fatal("runtime.Caller unavailable; set PTFP_GOLDEN_TESTDATA_ROOT for -trimpath")
	}
	return filepath.Clean(filepath.Join(filepath.Dir(file), "..", "..", "..", "..", "testdata", "golden", "v1"))
}

func fixtureBytes(t *testing.T, requirementID string) []byte {
	t.Helper()
	root := goldenRoot(t)
	catalogPath := filepath.Join(root, "catalogs", "sha256-"+story95CatalogDigest, "catalog.v1.json")
	raw, err := os.ReadFile(catalogPath)
	if err != nil {
		t.Fatal(err)
	}
	var catalog goldenCatalog
	if err := json.Unmarshal(raw, &catalog); err != nil {
		t.Fatal(err)
	}
	if catalog.CatalogID != "sha256:"+story95CatalogDigest {
		t.Fatalf("unexpected golden catalog identity: %q", catalog.CatalogID)
	}
	for _, entry := range catalog.Entries {
		if entry.RequirementID != requirementID {
			continue
		}
		if entry.FilesystemLocator == "" || strings.Contains(entry.FilesystemLocator, "\\") ||
			strings.HasPrefix(entry.FilesystemLocator, "/") || strings.Contains(entry.FilesystemLocator, "..") {
			t.Fatalf("unsafe golden fixture locator: %q", entry.FilesystemLocator)
		}
		fixturePath := filepath.Clean(filepath.Join(root, filepath.FromSlash(entry.FilesystemLocator)))
		relative, err := filepath.Rel(root, fixturePath)
		if err != nil || relative == "." || strings.HasPrefix(relative, "..") || filepath.IsAbs(relative) {
			t.Fatalf("golden fixture escapes root: %q", entry.FilesystemLocator)
		}
		carrier, err := os.ReadFile(fixturePath)
		if err != nil {
			t.Fatal(err)
		}
		if strings.TrimSpace(string(carrier)) != string(carrier) {
			t.Fatal("golden base64 carrier must not contain whitespace")
		}
		decoded, err := base64.StdEncoding.Strict().DecodeString(string(carrier))
		if err != nil || base64.StdEncoding.EncodeToString(decoded) != string(carrier) {
			t.Fatalf("noncanonical golden carrier: %v", err)
		}
		observed := fmt.Sprintf("sha256:%x", sha256.Sum256(decoded))
		if observed != entry.DecodedSHA256 {
			t.Fatalf("golden payload hash mismatch: got %s want %s", observed, entry.DecodedSHA256)
		}
		return decoded
	}
	t.Fatalf("missing golden requirement %s", requirementID)
	return nil
}

func TestV1GoldenConsensusTransactionAndState(t *testing.T) {
	txBytes := fixtureBytes(t, "consensus.go.transaction")
	var tx RoundInputTx
	if err := json.Unmarshal(txBytes, &tx); err != nil {
		t.Fatal(err)
	}
	round, err := evaluateRound(tx, 7)
	if err != nil {
		t.Fatal(err)
	}
	if round.FinalStatus != statusSuccess || round.CommitHeight != 7 || round.RoundID != "fixture-round" {
		t.Fatalf("unexpected golden round: %+v", round)
	}

	statePath := filepath.Join(t.TempDir(), "state.json")
	application, err := NewConsensusApplication(statePath)
	if err != nil {
		t.Fatal(err)
	}
	checked, err := application.CheckTx(context.Background(), &abcitypes.CheckTxRequest{Tx: txBytes})
	if err != nil || checked.Code != 0 {
		t.Fatalf("golden CheckTx failed: %+v %v", checked, err)
	}
	finalized, err := application.FinalizeBlock(context.Background(), &abcitypes.FinalizeBlockRequest{
		Height: 7, Txs: [][]byte{txBytes},
	})
	if err != nil || len(finalized.TxResults) != 1 || finalized.TxResults[0].Code != 0 {
		t.Fatalf("golden FinalizeBlock failed: %+v %v", finalized, err)
	}
	if _, err := application.Commit(context.Background(), &abcitypes.CommitRequest{}); err != nil {
		t.Fatal(err)
	}
	found, err := application.Query(context.Background(), &abcitypes.QueryRequest{Data: []byte("fixture-round")})
	if err != nil || found.Code != 0 || len(found.Value) == 0 {
		t.Fatalf("golden query failed: %+v %v", found, err)
	}
	missing, err := application.Query(context.Background(), &abcitypes.QueryRequest{Data: []byte("missing")})
	if err != nil || missing.Code != 1 {
		t.Fatalf("missing query behavior drifted: %+v %v", missing, err)
	}
	reloaded, err := NewConsensusApplication(statePath)
	if err != nil {
		t.Fatal(err)
	}
	info, err := reloaded.Info(context.Background(), &abcitypes.InfoRequest{})
	if err != nil || info.LastBlockHeight != 7 || len(info.LastBlockAppHash) == 0 {
		t.Fatalf("persisted v1 state drifted: %+v %v", info, err)
	}
}

func TestV1GoldenFailureExclusionAndDeclaredRoundingDivergence(t *testing.T) {
	var tx RoundInputTx
	if err := json.Unmarshal(fixtureBytes(t, "consensus.go.transaction"), &tx); err != nil {
		t.Fatal(err)
	}
	tx.ReplicatedStates[2].SensorValues["rpm"] = SensorValue{Value: 5000, Unit: "sentinel"}
	round, err := evaluateRound(tx, 8)
	if err != nil {
		t.Fatal(err)
	}
	if len(round.Exclusions) == 0 {
		t.Fatal("expected the preserved exclusion path")
	}
	tx.ReplicatedStates[0].SensorValues = map[string]SensorValue{}
	if _, err := evaluateRound(tx, 9); err == nil {
		t.Fatal("expected missing-sensor failure path")
	}
	// Python Decimal/half-even can round this tie down; Go math.Round is away from zero.
	if roundValue := roundToV1Precision(0.0005); roundValue != 0.001 {
		t.Fatalf("declared Go v1 half-tie behavior drifted: %v", roundValue)
	}
}

func TestV1GoldenCommittedStatusFixturesRemainDistinct(t *testing.T) {
	for _, expectation := range []struct {
		requirementID string
		status        string
		exclusions    int
		hasState      bool
	}{
		{"consensus.committed.success", statusSuccess, 0, true},
		{"consensus.committed.exclusion", statusSuccess, 1, true},
		{"consensus.committed.failed", statusFailedConsensus, 0, false},
	} {
		t.Run(expectation.requirementID, func(t *testing.T) {
			var committed CommittedRound
			if err := json.Unmarshal(fixtureBytes(t, expectation.requirementID), &committed); err != nil {
				t.Fatal(err)
			}
			if committed.FinalStatus != expectation.status || len(committed.Exclusions) != expectation.exclusions {
				t.Fatalf("committed status fixture drifted: %+v", committed)
			}
			if (committed.ConsensusedValidState != nil) != expectation.hasState {
				t.Fatalf("committed state presence drifted: %+v", committed)
			}
		})
	}
	if queryKey := string(fixtureBytes(t, "consensus.query.missing")); queryKey != "missing" {
		t.Fatalf("missing-query fixture drifted: %q", queryKey)
	}
}

func roundToV1Precision(value float64) float64 {
	return round(value)
}
